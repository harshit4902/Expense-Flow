import json
import re
import datetime
from typing import List
from sqlalchemy.orm import Session
from openai import OpenAI

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


def _get_system_prompt(categories: List[Category]) -> str:
    today_str = datetime.date.today().isoformat()
    expense_cats = [c.name for c in categories if c.type == "expense"]
    income_cats = [c.name for c in categories if c.type == "income"]

    return f"""You are ExpenseFlow's smart financial assistant.
You understand English, Hindi, and Hinglish (e.g. "Aaj maine 20 ka samosa khaya", "5000 salary aayi", "Saved 1000 rupees").
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
      "description": "<Short meaningful description, e.g. Samosa, Metro ticket, Freelancing>",
      "date": "{today_str}"
    }}
  ],
  "savings": null | {{
    "type": "initial_balance" | "deposit" | "withdrawal" | "balance_adjustment",
    "amount": <INTEGER AMOUNT IN PAISE>,
    "description": "<Description>",
    "date": "{today_str}"
  }},
  "requires_clarification": false
}}

Rules:
1. Always convert rupee amounts to integer paise (amount * 100).
2. If multiple items are in one sentence (e.g. "20 ka samosa aur 50 ka petrol"), output multiple items in the `transactions` array.
3. If it's about savings:
   - "Mere paas 50000 savings hai" -> type: "initial_balance" (or "balance_adjustment")
   - "Saved 5000" / "Savings mein dale 5000" -> type: "deposit"
   - "Savings se 2000 nikale" -> type: "withdrawal"
4. If amount is missing (e.g. "Maine samosa khaya" with no amount), set "intent": "clarification", "requires_clarification": true, and ask how much in "reply".
5. Return ONLY valid JSON.
"""


def _mock_rule_based_fallback(user_text: str, categories: List[Category]) -> LLMExtractionResult:
    """Intelligent regex fallback when OpenAI API key is not configured."""
    text = user_text.lower()
    today_str = datetime.date.today().isoformat()

    # Search for numbers: e.g. "20 ka samosa", "rs 20", "₹20", "20 rupaye", "2000"
    amount_match = re.search(r'(?:₹|rs\.?|rupees?|rupaye?|\b)(\d+(?:\.\d+)?)\s*(?:ka|ki|ke|rs\.?|rupees?|rupaye?|\b)', text)
    if not amount_match:
        # Try finding standalone number
        amount_match = re.search(r'\b(\d+(?:\.\d+)?)\b', text)

    amount_rupees = float(amount_match.group(1)) if amount_match else None

    # Savings checks
    if "saving" in text or "bachat" in text:
        if not amount_rupees:
            return LLMExtractionResult(
                intent="clarification",
                reply="Savings ki kitni amount record karni hai?",
                requires_clarification=True,
            )
        paise = int(amount_rupees * 100)
        if "nikal" in text or "withdraw" in text:
            return LLMExtractionResult(
                intent="savings",
                reply=f"₹{amount_rupees:,.2f} savings se withdrawal record kar diya.",
                savings=ParsedSavings(type="withdrawal", amount=paise, description="Savings withdrawal", date=today_str),
            )
        if "hai" in text or "balance" in text:
            return LLMExtractionResult(
                intent="savings",
                reply=f"Current savings balance ₹{amount_rupees:,.2f} set kar diya.",
                savings=ParsedSavings(type="balance_adjustment", amount=paise, description="Savings balance adjustment", date=today_str),
            )
        return LLMExtractionResult(
            intent="savings",
            reply=f"₹{amount_rupees:,.2f} savings deposit record kar diya.",
            savings=ParsedSavings(type="deposit", amount=paise, description="Savings deposit", date=today_str),
        )

    # Income check
    if any(k in text for k in ["salary", "kamaya", "earned", "income", "freelance", "credit", "aayi"]):
        if not amount_rupees:
            return LLMExtractionResult(
                intent="clarification",
                reply="Kitni income aayi hai?",
                requires_clarification=True,
            )
        paise = int(amount_rupees * 100)
        return LLMExtractionResult(
            intent="transaction",
            reply=f"₹{amount_rupees:,.2f} income record kar di gayi hai.",
            transactions=[
                ParsedTransaction(
                    type="income",
                    amount=paise,
                    category_name="Salary" if "salary" in text else "Other",
                    description=user_text.strip(),
                    date=today_str,
                )
            ],
        )

    # Expense check
    if not amount_rupees:
        return LLMExtractionResult(
            intent="clarification",
            reply="Kitna kharch hua? Kripya amount batayein.",
            requires_clarification=True,
        )

    paise = int(amount_rupees * 100)
    # Match category keyword
    cat_name = "Food"
    if any(k in text for k in ["petrol", "auto", "cab", "uber", "ola", "travel", "metro", "bus", "train", "flight"]):
        cat_name = "Travel"
    elif any(k in text for k in ["recharge", "bill", "electricity", "wifi", "rent"]):
        cat_name = "Bills"
    elif any(k in text for k in ["shopping", "kapde", "cloth", "shoes"]):
        cat_name = "Shopping"
    elif any(k in text for k in ["dawa", "medicine", "doctor", "health"]):
        cat_name = "Healthcare"

    # Extract short description
    desc = user_text.strip()
    return LLMExtractionResult(
        intent="transaction",
        reply=f"₹{amount_rupees:,.2f} ka expense ({cat_name}) record kar diya gaya hai.",
        transactions=[
            ParsedTransaction(
                type="expense",
                amount=paise,
                category_name=cat_name,
                description=desc,
                date=today_str,
            )
        ],
    )


def call_openai_extraction(message: str, categories: List[Category]) -> LLMExtractionResult:
    """Calls OpenAI API with JSON mode, or falls back to rule-based parser if no API key is set."""
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
    """Processes chat message, parses with OpenAI, and directly updates the database."""
    # 1. Store user message in history
    user_msg_record = ChatMessage(user_id=user_id, role="user", message=message)
    db.add(user_msg_record)
    db.commit()

    # 2. Fetch categories
    categories = category_service.get_categories(db, user_id)
    cat_map = {c.name.lower(): c for c in categories}

    # 3. Call OpenAI / Parser
    extraction = call_openai_extraction(message, categories)

    recorded_txs = []
    recorded_savings = None

    # 4. Handle Transactions
    if extraction.intent == "transaction" and extraction.transactions:
        for t in extraction.transactions:
            # Match category or fallback
            target_cat = cat_map.get(t.category_name.lower())
            if not target_cat:
                # Fallback to first category of same type
                target_cat = next((c for c in categories if c.type == t.type), None)

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
