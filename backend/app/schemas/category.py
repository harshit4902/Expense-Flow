import datetime
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


CategoryType = Literal["income", "expense"]


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, examples=["Food"])
    type: CategoryType = Field(..., examples=["expense"])


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, examples=["Food & Dining"])


class CategoryResponse(CategoryBase):
    id: int
    user_id: int
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

