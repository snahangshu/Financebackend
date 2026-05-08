from fastapi import APIRouter, Depends, HTTPException, Request
from database import get_db
from typing import List
import uuid
from routes.accounts import get_current_user

router = APIRouter(prefix="/categories", tags=["categories"])

@router.get("/")
async def get_categories(user_id: str = Depends(get_current_user), db = Depends(get_db)):
    categories = await db.categories.find({"user_id": user_id}).to_list(1000)
    for cat in categories:
        cat["id"] = cat.pop("_id")
    return {"data": categories}

@router.post("/")
async def create_category(category_data: dict, user_id: str = Depends(get_current_user), db = Depends(get_db)):
    category_id = str(uuid.uuid4())
    new_category = {
        "_id": category_id,
        "name": category_data["name"],
        "user_id": user_id
    }
    await db.categories.insert_one(new_category)
    new_category["id"] = new_category.pop("_id")
    return {"data": new_category}

@router.delete("/{category_id}")
async def delete_category(category_id: str, user_id: str = Depends(get_current_user), db = Depends(get_db)):
    result = await db.categories.delete_one({"_id": category_id, "user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"success": True}
