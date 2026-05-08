# Finance AI Advisor - Backend (Core)

This is the high-performance Python backend for the Finance AI Advisor, built with **FastAPI**, **Motor (Async MongoDB)**, and **Google Gemini 2.0**.

## 🚀 Tech Stack
- **Framework**: FastAPI (Asynchronous Python)
- **Database**: MongoDB Atlas (via Motor)
- **AI Engine**: Google GenAI (Gemini 2.0 Flash / 1.5 Pro)
- **Authentication**: Clerk JWT Integration
- **Deployment**: Optimized for Render

## 🛠️ API Architecture

### 1. Financial Summary (`/api/summary/`)
- **GET `/`**: Returns a comprehensive financial overview.
- **Functionality**: Calculates total income, expenses, and remaining balance for the current period vs. the previous period. Includes day-by-day transaction data for the dashboard charts.

### 2. Transaction Management (`/api/transactions/`)
- **GET `/`**: Retrieves all transactions for the authenticated user.
- **POST `/`**: Creates a new transaction. Supports negative amounts for expenses and positive for income.
- **Functionality**: Automatically links transactions to specific bank accounts and categories.

### 3. Neural Analysis (`/api/analysis/`)
- **GET `/summary`**: The "Brain" of the dashboard.
- **Functionality**: Uses data-driven logic to analyze 30-day trends. It identifies spending anomalies, top burn categories, and provides natural language insights for the "System Overview" banner.

### 4. AI Chatbot (`/api/chat/`)
- **POST `/`**: Real-time streaming interface for the Gemini AI.
- **Functionality**: 
    - **Context Awareness**: Automatically injects the user's financial summary and recent history into the AI prompt.
    - **Model Cascading**: Automatically fails over between Gemini 2.0, 1.5, and Pro to bypass free-tier quota limits.
    - **Rupee Localized**: Strictly calibrated to provide advice in Indian Rupees (₹).

### 5. Taxonomy & Accounts
- **`/api/accounts/`**: Manage bank accounts, credit cards, and cash wallets.
- **`/api/categories/`**: Manage spending tags and income sources.

## ⚙️ Environment Variables
To run this project, you must set up a `.env` file in the root:
```env
DATABASE_URL=mongodb+srv://...
CLERK_SECRET_KEY=sk_test_...
GOOGLE_GENERATION_AI_API_KEY=AIza...
```

## 📦 Installation & Setup
1. Clone the repository.
2. Create a virtual environment: `python -m venv venv`.
3. Activate venv: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux).
4. Install dependencies: `pip install -r requirements.txt`.
5. Start the server: `uvicorn main:app --reload`.

## 🌐 Deployment
This backend is configured for **Render**. Ensure the `$PORT` environment variable is used and the host is set to `0.0.0.0`.
