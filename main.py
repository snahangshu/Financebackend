from fastapi import FastAPI, Request
import time
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
import os
from routes import accounts, summary, chat, categories, transactions, analysis

load_dotenv()

app = FastAPI(title="Finance AI Advisor API")

# Configure CORS
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    print(f"{request.method} {request.url.path} - {response.status_code} ({process_time:.2f}ms)")
    return response

# Register routes
app.include_router(accounts.router, prefix="/api")
app.include_router(summary.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
app.include_router(transactions.router, prefix="/api")
app.include_router(analysis.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Finance AI Advisor API is running"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
