from fastapi import APIRouter
from app.services.ai_agent import ask_ai

router = APIRouter()

@router.post("/ai")
def ai_endpoint(data: dict):
    ai_data = ask_ai(data["message"])

    action = ai_data.get("action")

    if action == "get_ton_kho":
        return {"result": "Tồn kho: 120 bình"}

    return {"result": "Không hiểu"}
