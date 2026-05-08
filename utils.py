from datetime import datetime, timedelta
from typing import List, Dict

def calculate_percentage_change(current: float, last: float) -> float:
    if last == 0:
        return 0 if current == 0 else 100
    return ((current - last) / abs(last)) * 100

def fill_missing_days(active_days: List[Dict], start_date: datetime, end_date: datetime) -> List[Dict]:
    days_map = {d["date"].date(): d for d in active_days}
    result = []
    current_date = start_date
    while current_date <= end_date:
        date_key = current_date.date()
        if date_key in days_map:
            result.append(days_map[date_key])
        else:
            result.append({
                "date": current_date,
                "income": 0,
                "expenses": 0
            })
        current_date += timedelta(days=1)
    return result
