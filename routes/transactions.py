from fastapi import APIRouter, Depends, HTTPException, Request, Query
from database import get_db
from datetime import datetime
from typing import List, Optional
import uuid
from routes.accounts import get_current_user

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.get("/")
async def get_transactions(
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    account_id: Optional[str] = Query(None, alias="accountId"),
    user_id: str = Depends(get_current_user),
    db = Depends(get_db)
):
    # Get user's account IDs first
    user_accounts = await db.accounts.find({"user_id": user_id}).to_list(1000)
    user_account_ids = [acc["_id"] for acc in user_accounts]
    
    query = {"account_id": {"$in": user_account_ids}}
    
    if account_id:
        if account_id in user_account_ids:
            query["account_id"] = account_id
        else:
            return {"data": []}
            
    if from_date or to_date:
        query["date"] = {}
        if from_date:
            query["date"]["$gte"] = datetime.strptime(from_date, "%Y-%m-%d")
        if to_date:
            query["date"]["$lte"] = datetime.strptime(to_date, "%Y-%m-%d")

    cursor = db.transactions.find(query).sort("date", -1)
    transactions = []
    async for t in cursor:
        t["id"] = t.pop("_id")
        # Include account and category details
        acc = next((a for a in user_accounts if a["_id"] == t["account_id"]), None)
        cat = await db.categories.find_one({"_id": t.get("category_id")}) if t.get("category_id") else None
        
        t["account"] = acc["name"] if acc else "Unknown"
        t["category"] = cat["name"] if cat else "Uncategorized"
        transactions.append(t)
        
    return {"data": transactions}

@router.post("/")
async def create_transaction(data: dict, user_id: str = Depends(get_current_user), db = Depends(get_db)):
    # Verify account belongs to user
    account = await db.accounts.find_one({"_id": data["account_id"], "user_id": user_id})
    if not account:
        raise HTTPException(status_code=400, detail="Invalid account")
        
    transaction_id = str(uuid.uuid4())
    new_t = {
        "_id": transaction_id,
        "amount": data["amount"],
        "payee": data["payee"],
        "notes": data.get("notes"),
        "date": datetime.fromisoformat(data["date"].replace('Z', '')),
        "account_id": data["account_id"],
        "category_id": data.get("category_id"),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    await db.transactions.insert_one(new_t)
    new_t["id"] = new_t.pop("_id")
    return {"data": new_t}

@router.post("/bulk-create")
async def bulk_create_transactions(data: List[dict], user_id: str = Depends(get_current_user), db = Depends(get_db)):
    # Simple implementation
    for t in data:
        await create_transaction(t, user_id, db)
    return {"success": True}
