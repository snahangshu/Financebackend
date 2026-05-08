from fastapi import APIRouter, Depends, Request
from database import get_db
from routes.accounts import get_current_user
from datetime import datetime, timedelta
import os

router = APIRouter(prefix="/analysis", tags=["analysis"])

@router.get("/summary")
async def get_ai_summary(user_id: str = Depends(get_current_user), db = Depends(get_db)):
    # Fetch recent data to provide context to the "AI"
    # In a real app, you'd send this to OpenAI/Gemini
    # For now, we'll generate a high-quality "Neural" analysis based on real trends
    
    user_accounts = await db.accounts.find({"user_id": user_id}).to_list(100)
    acc_ids = [a["_id"] for a in user_accounts]
    
    # Get last 30 days transactions
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    transactions = await db.transactions.find({
        "account_id": {"$in": acc_ids},
        "date": {"$gte": thirty_days_ago}
    }).to_list(1000)
    
    income = sum(t["amount"] for t in transactions if t["amount"] > 0)
    expense = sum(abs(t["amount"]) for t in transactions if t["amount"] < 0)
    
    # Find top category
    cat_map = {}
    for t in transactions:
        if t["amount"] < 0:
            cid = t.get("category_id", "Uncategorized")
            cat_map[cid] = cat_map.get(cid, 0) + abs(t["amount"])
    
    top_cat_name = "diverse areas"
    if cat_map:
        top_cat_id = max(cat_map, key=cat_map.get)
        cat_doc = await db.categories.find_one({"_id": top_cat_id})
        if cat_doc:
            top_cat_name = cat_doc["name"]

    # Generate the analysis string
    status = "nominal" if income >= expense else "aggressive"
    trend = "surplus" if income > expense else "deficit"
    
    analysis = f"Neural analysis complete. Your portfolio is currently in a {status} state with a 30-day {trend}. "
    if cat_map:
        analysis += f"Primary burn detected in {top_cat_name}. "
    
    if income > expense * 1.5:
        analysis += "Capital efficiency is optimal. Consider reinvesting excess liquidity."
    elif expense > income:
        analysis += "Alert: Burn rate exceeding revenue. Re-evaluating allocation strategies."
    else:
        analysis += "Stable trajectory maintained. All systems performing within expected baseline."

    return {"data": {"insight": analysis}}
