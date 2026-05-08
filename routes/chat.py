import os
import json
import time
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import StreamingResponse
from google import genai
from google.genai import types
from database import get_db
from datetime import datetime, timedelta
from routes.accounts import get_current_user

router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize the new Google GenAI Client
client = genai.Client(api_key=os.getenv("GOOGLE_GENERATION_AI_API_KEY"))

async def get_financial_summary(u_id: str, db, from_date: str = None, to_date: str = None):
    start_date = datetime.strptime(from_date, "%Y-%m-%d") if from_date else datetime.utcnow() - timedelta(days=30)
    end_date = datetime.strptime(to_date, "%Y-%m-%d") if to_date else datetime.utcnow()
    
    user_accounts = await db.accounts.find({"user_id": u_id}).to_list(1000)
    account_ids = [acc["_id"] for acc in user_accounts]
    
    query = {
        "account_id": {"$in": account_ids},
        "date": {"$gte": start_date, "$lte": end_date}
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
        "period": {"from": start_date.isoformat(), "to": end_date.isoformat()},
        "summary": {"income": income, "expenses": expenses, "remaining": income - expenses}
    }

async def get_recent_transactions(u_id: str, db, limit: int = 10):
    user_accounts = await db.accounts.find({"user_id": u_id}).to_list(1000)
    account_ids = [acc["_id"] for acc in user_accounts]
    
    cursor = db.transactions.find({"account_id": {"$in": account_ids}}).sort("date", -1).limit(limit)
    transactions = []
    async for t in cursor:
        acc = next((a for a in user_accounts if a["_id"] == t["account_id"]), None)
        cat = await db.categories.find_one({"_id": t.get("category_id")}) if t.get("category_id") else None
        
        transactions.append({
            "id": t["_id"],
            "date": t["date"].isoformat(),
            "amount": t["amount"],
            "payee": t["payee"],
            "category": cat["name"] if cat else "Uncategorized",
            "account": acc["name"] if acc else "Unknown"
        })
    return transactions

@router.post("/")
async def chat(request: Request, user_id: str = Depends(get_current_user), db = Depends(get_db)):
    body = await request.json()
    messages = body.get("messages", [])
    
    if not messages:
        raise HTTPException(status_code=400, detail="Messages are required")

    # Fetch context to inject into the model
    summary = await get_financial_summary(user_id, db)
    recent = await get_recent_transactions(user_id, db, 5)
    
    system_prompt = f"""You are a knowledgeable and professional financial assistant chatbot. 
    You have access to the user's financial data.
    Current Context for user ({user_id}):
    Summary (last 30 days): {json.dumps(summary)}
    Recent Transactions: {json.dumps(recent)}
    
    Provide accurate, concise, and clear information. Maintain a professional tone. 
    Always respond in Rupees (₹) for currency values."""

    # Prepare conversation history
    contents = []
    for m in messages:
        if m["content"] == "Neural analysis active. How can I assist with your portfolio today?":
            continue
        role = "model" if m.get("role") == "assistant" else "user"
        contents.append(types.Content(role=role, parts=[types.Part(text=m["content"])]))

    def generate():
        # Cascade through available models to bypass potential quota limits
        # Using exact names from the user's supported list
        models_to_try = ['gemini-2.0-flash', 'gemini-flash-latest', 'gemini-pro-latest']
        
        for model_name in models_to_try:
            try:
                print(f"Attempting chat with {model_name}...")
                response = client.models.generate_content_stream(
                    model=model_name, 
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.7
                    )
                )
                success = False
                for chunk in response:
                    if chunk.text:
                        success = True
                        yield chunk.text
                
                if success:
                    return # Exit if successful
                    
            except Exception as e:
                print(f"GenAI Error with {model_name}: {str(e)}")
                if "RESOURCE_EXHAUSTED" in str(e):
                    continue # Try the next model in the cascade
                else:
                    yield f"Error: {str(e)}"
                    return

        yield "Neural capacity reached for the current session. Please pause for 60 seconds while the system recalibrates."

    return StreamingResponse(generate(), media_type="text/plain")
