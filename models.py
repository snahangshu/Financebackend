from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class Account(BaseModel):
    id: str = Field(..., alias="_id")
    plaid_id: Optional[str] = None
    name: str
    user_id: str

    class Config:
        populate_by_name = True

class Category(BaseModel):
    id: str = Field(..., alias="_id")
    plaid_id: Optional[str] = None
    name: str
    user_id: str

    class Config:
        populate_by_name = True

class Transaction(BaseModel):
    id: str = Field(..., alias="_id")
    amount: int
    payee: str
    notes: Optional[str] = None
    date: datetime
    account_id: str
    category_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
