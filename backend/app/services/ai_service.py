import json
import re
import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from openai import OpenAI
from dateutil import parser as date_parser

from app.config import get_settings
from app.models.category import Category
from app.models.chat_message import ChatMessage
from app.schemas.ai import LLMExtractionResult, ParsedTransaction, ParsedSavings, ChatResponse
from app.schemas.transaction import TransactionCreate
from app.schemas.savings import (
    SavingsInitializeRequest,
    SavingsDepositRequest,
    SavingsWithdrawRequest,
    SavingsBalanceAdjustmentRequest,
)
from app.services import transaction_service, savings_service, category_service

settings = get_settings()

CATEGORY_KEYWORDS = {
    "Travel": [
        "petrol", "diesel", "fuel", "cng", "auto", "cab", "uber", "ola", "rapido",
        "travel", "metro", "bus", "train", "flight", "ticket", "fare", "kiraya",
        "toll", "parking", "transport", "bike", "car"
    ],
    "Bills": [
        "recharge", "bill", "electricity", "bijli", "water", "pani", "wifi",
        "broadband", "internet", "dth", "cylinder", "gas", "maintenance",
        "subscription", "netflix", "prime", "spotify"
    ],
    "Rent": [
        "rent", "kamre ka kiraya", "room rent", "flat rent", "pg rent", "ghar ka kiraya", "fridge ka rent"
    ],
    "Groceries": [
        "groceries", "grocery", "ration", "kirana", "doodh", "milk", "vegetable",
        "sabzi", "sabji", "fruits", "fruit", "atta", "dal", "chawal", "oil",
        "shampoo", "soap", "sabun", "surf", "toothpaste", "pepsi", "coke"
    ],
    "Shopping": [
        "shopping", "kapde", "clothes", "shirt", "pant", "jeans", "tshirt",
        "dress", "shoes", "shoe", "chappal", "amazon", "flipkart", "myntra",
        "meesho", "zudio", "zara", "watch", "electronics", "laptop", "mobile", "phone"
    ],
    "Entertainment": [
        "movie", "cinema", "theatre", "popcorn", "pvr", "game", "gaming", "outing",
        "party", "club", "concert", "cricket", "match", "fire cracker", "crackers",
        "cracker", "patakha", "patakhe", "diwali shopping", "fun", "amusement"
    ],
    "Healthcare": [
        "dawa", "dawakhana", "medicine", "medicines", "doctor", "hospital", "clinic",
        "medical", "treatment", "tablet", "tablets", "syrup", "health", "checkup", "test", "dentist"
    ],
    "Education": [
        "book", "books", "course", "fee", "fees", "school", "college", "tuition",
        "exam", "pen", "stationery", "notebook", "classes"
    ],
    "Food": [
        "food", "khana", "lunch", "dinner", "breakfast", "nashta", "cafe", "coffee",
        "tea", "chai", "samosa", "burger", "pizza", "biryani", "swiggy", "zomato",
        "restaurant", "hotel", "snack", "snacks", "dahi", "paneer", "sweets",
        "mithai", "ice cream", "momo", "momos", "roll", "thali", "eating"
    ],
    "Salary": [
        "salary", "tankhwah", "stipend", "paycheck", "wages", "mahina"
    ],
    "Freelancing": [
        "freelance", "freelancing", "client", "project payment", "gig", "contract", "upwork", "fiverr"
    ],
    "Business": [
        "business", "dukaan", "shop profit", "sales", "revenue", "vyapar", "dhandha"
    ],
    "Investment": [
        "investment", "dividend", "mutual fund", "stocks", "share market", "interest", "fd", "crypto", "return"
    ],
    "Gift": [
        "gift", "inaam", "shagun", "roommate", "friend"
    ]
}

CATEGORY_ALIASES = {
    "Travel": ["transport", "travel", "commute", "cab", "auto"],
    "Entertainment": ["outing", "entertainment", "fun", "leisure"],
    "Bills": ["rent", "bills", "utilities"],
    "Rent": ["rent", "bills"],
    "Food": ["dining", "food", "groceries", "restaurant"],
    "Groceries": ["food", "groceries"],
    "Salary": ["salary", "income", "freelancing"],
    "Gift": ["gift", "other", "income"],
    "Freelancing": ["freelancing", "salary", "income", "business"],
    "Business": ["business", "income", "freelancing"],
    "Investment": ["investment", "income"],
}


def _parse_relative_or_absolute_date(text: str) -> Optional[datetime.date]:
    """Detects and parses dates from English/Hinglish text.
    Handles relative dates (aaj, kal, parso, yesterday, 2 days ago)
    and absolute dates (e.g., '8 nov', '8th november', '2026-11-05', '05/11/2026').
    """
    clean_text = text.lower()
    today = datetime.date.today()

    # Relative days
    if re.search(r'\b(aaj|today)\b', clean_text):
        return today
    if re.search(r'\b(kal|yesterday|beeta kal)\b', clean_text):
        return today - datetime.timedelta(days=1)
    if re.search(r'\b(parso|day before yesterday)\b', clean_text):
        return today - datetime.timedelta(days=2)

    # "N days ago" / "N din pehle"
    days_ago_match = re.search(r'(\d+)\s*(?:days?|din)\s*(?:ago|pehle)', clean_text)
    if days_ago_match:
        days = int(days_ago_match.group(1))
        return today - datetime.timedelta(days=days)

    # Explicit date regex patterns
    date_candidates = [
        # "8 nov", "8th november", "8 nov ko", "on 8 november"
        r'\b(\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*(?:\s+\d{2,4})?)\b',
        # "on 8th", "8 tarikh ko", "8 date"
        r'\b(?:on|ko|tarikh|date)\s+(\d{1,2}(?:st|nd|rd|th)?)\b',
        r'\b(\d{1,2}(?:st|nd|rd|th)?)\s+(?:tarikh|tareekh|date)\b',
        # Standard formatted dates: 2026-11-08 or 08/11/2026 or 8-11-2026
        r'\b(\d{4}[-/]\d{1,2}[-/]\d{1,2})\b',
        r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b',
    ]

    for pat in date_candidates:
        match = re.search(pat, clean_text)
        if match:
            date_str = match.group(1)
            date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)
            try:
                parsed = date_parser.parse(date_str, default=datetime.datetime(today.year, today.month, today.day))
                parsed_date = parsed.date()
                if parsed_date > today and not re.search(r'\b\d{4}\b', date_str):
                    parsed_date = parsed_date.replace(year=today.year - 1)
                return parsed_date
            except Exception:
                continue

    return None


def _find_best_matching_category(text: str, tx_type: str, available_categories: List[Category]) -> Category:
    """Finds best matching category for tx_type, utilizing semantic keywords,
    user-specific category names, and synonym aliases.
    """
    clean_text = text.lower()
    type_categories = [c for c in available_categories if c.type == tx_type]
    if not type_categories:
        type_categories = available_categories

    # 1. Direct name match in user categories
    for cat in type_categories:
        if re.search(rf'\b{re.escape(cat.name.lower())}\b', clean_text):
            return cat

    # 2. Match via semantic keywords and alias expansion
    for standard_cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if re.search(rf'\b{re.escape(kw)}\b', clean_text):
                # Check direct user category match
                direct = next((c for c in type_categories if c.name.lower() == standard_cat.lower()), None)
                if direct:
                    return direct

                # Check alias mapping
                for alias in CATEGORY_ALIASES.get(standard_cat, []):
                    found_alias = next((c for c in type_categories if c.name.lower() == alias.lower()), None)
                    if found_alias:
                        return found_alias

    # 3. Fallback: 'Other' if available, otherwise first category of that type
    other_cat = next((c for c in type_categories if c.name.lower() == "other"), None)
    if other_cat:
        return other_cat

    return type_categories[0] if type_categories else available_categories[0]


def _detect_is_income(text: str) -> bool:
    """Accurately distinguishes income vs expense in English, Hindi, and Hinglish."""
    clean = text.lower()

    expense_strong = [
        "kharch", "khaya", "bharwaya", "kharida", "spent", "paid",
        "de diya", "diye maine", "diya maine", "bhara", "peeya", "pee li"
    ]
    if any(k in clean for k in expense_strong):
        return False

    income_strong = [
        "salary", "kamaya", "earned", "income", "freelance", "freelancing",
        "stipend", "bonus", "profit", "dividend"
    ]
    if any(k in clean for k in income_strong):
        return True

    # Directional credit/receipt indicators in Hindi/English:
    # "mujhe ... mila/diya/aaya", "roommate ne diya", "friend gave", "received"
    directional_income = [
        r'\b(mujhe|mere account|mere paas|mujhko)\b.*\b(mila|mile|diya|diye|transfer|bheja|aaya|aaye)\b',
        r'\b(diya|diye|bheja|transfer kiya)\b.*\b(mujhe|mere|mujhko)\b',
        r'\b(roommate|friend|dost|bhai|papa|mom|client)\s*(?:ne)?\s*(?:\w+\s*){0,3}(?:diya|bheja|transfer|send)',
        r'\b(received|got|credited|deposited to my account)\b',
        r'\b(aaya|aayi|credit hua|credit hue)\b',
    ]
    for pat in directional_income:
        if re.search(pat, clean):
            return True

    return False


def _get_system_prompt(categories: List[Category]) -> str:
    today_str = datetime.date.today().isoformat()
    expense_cats = [c.name for c in categories if c.type == "expense"]
    income_cats = [c.name for c in categories if c.type == "income"]

    return f"""You are ExpenseFlow's smart financial assistant.
You understand English, Hindi, and Hinglish (e.g. "Aaj maine 20 ka samosa khaya", "5000 salary aayi 5 nov ko", "mera roommate mujhe 200 diya kal", "Saved 1000 rupees").
Today's date is: {today_str}.

Available User Expense Categories: {json.dumps(expense_cats)}
Available User Income Categories: {json.dumps(income_cats)}

Your job is to extract financial transaction information or savings intent and return pure JSON conforming to this schema:
{{
  "intent": "transaction" | "savings" | "clarification" | "general_chat",
  "reply": "Friendly response in the user's language acknowledging the action or answering questions",
  "transactions": [
    {{
      "type": "expense" | "income",
      "amount": <INTEGER AMOUNT IN PAISE, where ₹1 = 100 paise. E.g. ₹20 = 2000, ₹250.50 = 25050>,
      "category_name": "<Match closest category name from available categories>",
      "description": "<Short meaningful description, e.g. Samosa, Roommate payment, Petrol>",
      "date": "<YYYY-MM-DD extracted from text if specified, otherwise {today_str}>"
    }}
  ],
  "savings": null | {{
    "type": "initial_balance" | "deposit" | "withdrawal" | "balance_adjustment",
    "amount": <INTEGER AMOUNT IN PAISE>,
    "description": "<Description>",
    "date": "<YYYY-MM-DD extracted from text if specified, otherwise {today_str}>"
  }},
  "requires_clarification": false
}}

Rules:
1. Always convert rupee amounts to integer paise (amount * 100).
2. Differentiate between INCOME vs EXPENSE:
   - EXPENSE: spent, kharch, khaya, liya, kharida, bharwaya, pay kiya, bill, paid, rent.
   - INCOME: received, salary, kamaya, earned, credit, aaya, aayi, mila, diya mujhe, roommate ne diya, friend ne diya.
3. Categorization: Match the most specific category available from the user's categories.
4. Date Handling: When user mentions a date (e.g. '8 nov', 'yesterday', 'kal', '2 days ago', '5 nov'), accurately calculate YYYY-MM-DD relative to today ({today_str}).
5. Return ONLY valid JSON.
"""


def _mock_rule_based_fallback(user_text: str, categories: List[Category]) -> LLMExtractionResult:
    """High-accuracy fallback parser when OpenAI API is not configured or rate-limited."""
    text = user_text.lower()
    today = datetime.date.today()
    extracted_date = _parse_relative_or_absolute_date(text) or today
    date_str = extracted_date.isoformat()

    amount_match = re.search(r'(?:₹|rs\.?|rupees?|rupaye?|\b)(\d+(?:\.\d+)?)\s*(?:ka|ki|ke|rs\.?|rupees?|rupaye?|\b)', text)
    if not amount_match:
        amount_match = re.search(r'\b(\d+(?:\.\d+)?)\b', text)

    amount_rupees = float(amount_match.group(1)) if amount_match else None

    # Savings check
    if "saving" in text or "bachat" in text:
        if not amount_rupees:
            return LLMExtractionResult(
                intent="clarification",
                reply="Savings ki kitni amount record karni hai?",
                requires_clarification=True,
            )
        paise = int(amount_rupees * 100)
        if any(w in text for w in ["nikal", "withdraw", "nikale", "nikala"]):
            return LLMExtractionResult(
                intent="savings",
                reply=f"₹{amount_rupees:,.2f} savings se withdrawal record kar diya ({date_str}).",
                savings=ParsedSavings(type="withdrawal", amount=paise, description="Savings withdrawal", date=date_str),
            )
        if any(w in text for w in ["hai", "balance", "actually", "kul"]):
            return LLMExtractionResult(
                intent="savings",
                reply=f"Current savings balance ₹{amount_rupees:,.2f} set kar diya ({date_str}).",
                savings=ParsedSavings(type="balance_adjustment", amount=paise, description="Savings balance adjustment", date=date_str),
            )
        return LLMExtractionResult(
            intent="savings",
            reply=f"₹{amount_rupees:,.2f} savings deposit record kar diya ({date_str}).",
            savings=ParsedSavings(type="deposit", amount=paise, description="Savings deposit", date=date_str),
        )

    if not amount_rupees:
        return LLMExtractionResult(
            intent="clarification",
            reply="Kitni amount hai? Kripya amount batayein.",
            requires_clarification=True,
        )

    paise = int(amount_rupees * 100)
    is_income = _detect_is_income(text)
    tx_type = "income" if is_income else "expense"
    matched_cat = _find_best_matching_category(text, tx_type, categories)
    desc = user_text.strip()

    if tx_type == "income":
        reply_msg = f"₹{amount_rupees:,.2f} income ({matched_cat.name}) record kar di gayi hai on {date_str}."
    else:
        reply_msg = f"₹{amount_rupees:,.2f} ka expense ({matched_cat.name}) record kar diya gaya hai on {date_str}."

    return LLMExtractionResult(
        intent="transaction",
        reply=reply_msg,
        transactions=[
            ParsedTransaction(
                type=tx_type,
                amount=paise,
                category_name=matched_cat.name,
                description=desc,
                date=date_str,
            )
        ],
    )


def call_openai_extraction(message: str, categories: List[Category]) -> LLMExtractionResult:
    """Calls OpenAI API with JSON mode, or falls back to rule-based parser if key is absent or rate-limited."""
    if not settings.OPENAI_API_KEY:
        return _mock_rule_based_fallback(message, categories)

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        system_prompt = _get_system_prompt(categories)

        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )

        content = response.choices[0].message.content
        data = json.loads(content)
        return LLMExtractionResult.model_validate(data)
    except Exception as e:
        print(f"OpenAI API call failed: {e}. Falling back to rule-based parser.")
        return _mock_rule_based_fallback(message, categories)


def process_chat_message(db: Session, user_id: int, message: str) -> ChatResponse:
    """Processes chat message, parses with OpenAI/fallback, and directly updates the database."""
    # 1. Store user message in history
    user_msg_record = ChatMessage(user_id=user_id, role="user", message=message)
    db.add(user_msg_record)
    db.commit()

    # 2. Fetch user's categories
    categories = category_service.get_categories(db, user_id)
    cat_map = {c.name.lower(): c for c in categories}

    # 3. Call OpenAI / Parser
    extraction = call_openai_extraction(message, categories)

    recorded_txs = []
    recorded_savings = None

    # 4. Handle Transactions
    if extraction.intent == "transaction" and extraction.transactions:
        for t in extraction.transactions:
            # Intelligent category matching with type validation
            target_cat = cat_map.get(t.category_name.lower())
            if not target_cat or target_cat.type != t.type:
                target_cat = _find_best_matching_category(t.description + " " + t.category_name, t.type, categories)

            if target_cat:
                parsed_date = datetime.date.fromisoformat(t.date) if t.date else datetime.date.today()
                tx_create = TransactionCreate(
                    category_id=target_cat.id,
                    amount=t.amount,
                    type=t.type,
                    description=t.description,
                    transaction_date=parsed_date,
                )
                created_tx = transaction_service.create_transaction(db, user_id, tx_create)
                recorded_txs.append(created_tx.model_dump())

    # 5. Handle Savings
    elif extraction.intent == "savings" and extraction.savings:
        s = extraction.savings
        parsed_date = datetime.date.fromisoformat(s.date) if s.date else datetime.date.today()

        if s.type == "deposit":
            rec = savings_service.add_deposit(
                db, user_id,
                SavingsDepositRequest(amount=s.amount, description=s.description, transaction_date=parsed_date)
            )
            recorded_savings = rec.model_dump()
        elif s.type == "withdrawal":
            try:
                rec = savings_service.add_withdrawal(
                    db, user_id,
                    SavingsWithdrawRequest(amount=s.amount, description=s.description, transaction_date=parsed_date)
                )
                recorded_savings = rec.model_dump()
            except Exception as e:
                extraction.reply = f"Savings withdrawal record nahi ho saki: {e.detail if hasattr(e, 'detail') else str(e)}"
        elif s.type in ["initial_balance", "balance_adjustment"]:
            summary = savings_service.calculate_savings_summary(db, user_id)
            if not summary.has_initial_balance:
                rec = savings_service.initialize_savings(
                    db, user_id,
                    SavingsInitializeRequest(amount=s.amount, description=s.description, transaction_date=parsed_date)
                )
                recorded_savings = rec.model_dump()
            else:
                rec, _ = savings_service.adjust_savings_balance(
                    db, user_id,
                    SavingsBalanceAdjustmentRequest(target_balance=s.amount, description=s.description, transaction_date=parsed_date)
                )
                recorded_savings = rec.model_dump()

    # 6. Store assistant reply in chat history
    assistant_msg = ChatMessage(user_id=user_id, role="assistant", message=extraction.reply)
    db.add(assistant_msg)
    db.commit()

    return ChatResponse(
        reply=extraction.reply,
        intent=extraction.intent,
        recorded_transactions=recorded_txs,
        recorded_savings=recorded_savings,
        requires_clarification=extraction.requires_clarification,
    )
