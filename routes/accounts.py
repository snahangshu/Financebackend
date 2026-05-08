from fastapi import APIRouter, Depends, HTTPException, Request
from database import get_db
from models import Account
from typing import List
import uuid

router = APIRouter(prefix="/accounts", tags=["accounts"])

# Placeholder for auth - in a real app, this would verify the Clerk JWT
async def get_current_user(request: Request):
    # This should extract the user_id from the Clerk JWT
    # For now, we'll use a hardcoded user_id for demonstration or extract from headers
    user_id = request.headers.get("x-user-id")
    if not user_id:
        # For development ease, if no header is present, use a default
        return "user_3DAO9StBFpXBiYYCahBYDmXykNb"
    return user_id

@router.get("/", response_model=dict)
async def get_accounts(user_id: str = Depends(get_current_user), db = Depends(get_db)):
    accounts = await db.accounts.find({"user_id": user_id}).to_list(1000)
    # Convert _id to id for consistency with frontend
    for acc in accounts:
        acc["id"] = acc.pop("_id")
    return {"data": accounts}

@router.post("/")
async def create_account(account_data: dict, user_id: str = Depends(get_current_user), db = Depends(get_db)):
    account_id = str(uuid.uuid4())
    new_account = {
        "_id": account_id,
        "name": account_data["name"],
        "user_id": user_id
    }
    await db.accounts.insert_one(new_account)
    new_account["id"] = new_account.pop("_id")
    return {"data": new_account}

@router.get("/{account_id}")
async def get_account(account_id: str, user_id: str = Depends(get_current_user), db = Depends(get_db)):
    account = await db.accounts.find_one({"_id": account_id, "user_id": user_id})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    account["id"] = account.pop("_id")
    return {"data": account}

@router.patch("/{account_id}")
async def update_account(account_id: str, account_data: dict, user_id: str = Depends(get_current_user), db = Depends(get_db)):
    result = await db.accounts.update_one(
        {"_id": account_id, "user_id": user_id},
        {"$set": {"name": account_data["name"]}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"success": True}

@router.delete("/{account_id}")
async def delete_account(account_id: str, user_id: str = Depends(get_current_user), db = Depends(get_db)):
    result = await db.accounts.delete_one({"_id": account_id, "user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"success": True}

@router.post("/bulk-delete")
async def bulk_delete_accounts(data: dict, user_id: str = Depends(get_current_user), db = Depends(get_db)):
    ids = data.get("ids", [])
    await db.accounts.delete_many({"_id": {"$in": ids}, "user_id": user_id})
    return {"success": True}
