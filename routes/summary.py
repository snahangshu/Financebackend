from fastapi import APIRouter, Depends, Query, Request
from database import get_db
from utils import calculate_percentage_change, fill_missing_days
from datetime import datetime, timedelta
from typing import Optional
from routes.accounts import get_current_user

router = APIRouter(prefix="/summary", tags=["summary"])

@router.get("/")
async def get_summary(
    request: Request,
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    account_id: Optional[str] = Query(None, alias="accountId"),
    user_id: str = Depends(get_current_user),
    db = Depends(get_db)
):
    default_to = datetime.utcnow()
    default_from = default_to - timedelta(days=30)

    start_date = datetime.strptime(from_date, "%Y-%m-%d") if from_date else default_from
    end_date = datetime.strptime(to_date, "%Y-%m-%d") if to_date else default_to

    period_length = (end_date - start_date).days + 1
    last_period_start = start_date - timedelta(days=period_length)
    last_period_end = end_date - timedelta(days=period_length)

    async def fetch_financial_data(u_id: str, s_date: datetime, e_date: datetime):
        # Filter for transactions where account belongs to user
        # We need to join with accounts to check user_id if account_id is not provided
        # But in our schema, transaction has account_id, and account has user_id
        
        # Step 1: Get valid account IDs for this user
        user_accounts = await db.accounts.find({"user_id": u_id}).to_list(1000)
        account_ids = [acc["_id"] for acc in user_accounts]
        
        if account_id:
            if account_id not in account_ids:
                return {"income": 0, "expenses": 0, "remaining": 0}
            target_account_ids = [account_id]
        else:
            target_account_ids = account_ids

        query = {
            "account_id": {"$in": target_account_ids},
            "date": {"$gte": s_date, "$lte": e_date}
        }
        
        cursor = db.transactions.find(query)
        income = 0
        expenses = 0
        async for t in cursor:
            amount = t["amount"]
            if amount >= 0:
                income += amount
            else:
                expenses += abs(amount)
        
        return {
            "income": income,
            "expenses": expenses,
            "remaining": income - expenses
        }

    current_period = await fetch_financial_data(user_id, start_date, end_date)
    last_period = await fetch_financial_data(user_id, last_period_start, last_period_end)

    income_change = calculate_percentage_change(current_period["income"], last_period["income"])
    expenses_change = calculate_percentage_change(current_period["expenses"], last_period["expenses"])
    remaining_change = calculate_percentage_change(current_period["remaining"], last_period["remaining"])

    # Categories data
    user_accounts = await db.accounts.find({"user_id": user_id}).to_list(1000)
    account_ids = [acc["_id"] for acc in user_accounts]
    target_account_ids = [account_id] if account_id else account_ids

    cat_query = {
        "account_id": {"$in": target_account_ids},
        "amount": {"$lt": 0},
        "date": {"$gte": start_date, "$lte": end_date}
    }
    
    category_map = {}
    async for t in db.transactions.find(cat_query):
        cat_id = t.get("category_id")
        cat_name = "Uncategorized"
        if cat_id:
            cat_doc = await db.categories.find_one({"_id": cat_id})
            if cat_doc:
                cat_name = cat_doc["name"]
        
        category_map[cat_name] = category_map.get(cat_name, 0) + abs(t["amount"])

    category_list = [{"name": n, "value": v} for n, v in category_map.items()]
    category_list.sort(key=lambda x: x["value"], reverse=True)
    
    top_categories = category_list[:3]
    other_categories = category_list[3:]
    if other_categories:
        top_categories.append({
            "name": "Other",
            "value": sum(c["value"] for c in other_categories)
        })

    # Days data
    days_query = {
        "account_id": {"$in": target_account_ids},
        "date": {"$gte": start_date, "$lte": end_date}
    }
    
    days_map = {}
    async for t in db.transactions.find(days_query):
        date_str = t["date"].strftime("%Y-%m-%d")
        if date_str not in days_map:
            days_map[date_str] = {"date": t["date"], "income": 0, "expenses": 0}
        
        if t["amount"] >= 0:
            days_map[date_str]["income"] += t["amount"]
        else:
            days_map[date_str]["expenses"] += abs(t["amount"])

    active_days = list(days_map.values())
    days = fill_missing_days(active_days, start_date, end_date)

    return {
        "data": {
            "remainingAmount": current_period["remaining"],
            "remainingChange": remaining_change,
            "incomeAmount": current_period["income"],
            "incomeChange": income_change,
            "expensesAmount": current_period["expenses"],
            "expensesChange": expenses_change,
            "categories": top_categories,
            "days": days
        }
    }
