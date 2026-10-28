# ==============================================================================
# RAFEEQ (رفيق) - Web UI & FastAPI Service (app.py)
# ==============================================================================

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# استيراد موديولات رفيق
from mcp_server import tool_search_policy
from context_memory import ContextManager
from tools_and_approvals import tool_issue_permit_draft, human_approval_gate, PermitRequest
from security_guard import SecurityGuard

app = FastAPI(title="Rafeeq (رفيق) - Madar Municipal Assistant", version="1.0")

ctx = ContextManager()

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def home():
    return {"status": "online", "message": "أهلاً بك في نظام رفيق (Rafeeq) - بلدية مدار الذكية"}

@app.post("/chat")
def chat_with_rafeeq(req: ChatRequest):
    user_msg = req.message

    # 1. فحص الأمان
    if not SecurityGuard.inspect_input(user_msg):
        raise HTTPException(status_code=400, detail="⚠️ تم رفض الطلب لأسباب أمنية (Prompt Injection Blocked).")

    # 2. إضافة للذاكرة
    ctx.add_message("user", user_msg)

    # 3. استرجاع السياسات بناءً على محتوى الرسالة
    keyword = "بناء" if "بناء" in user_msg else ("فود تراك" if "فود" in user_msg or "عربة" in user_msg else "فعالية")
    policy_result = tool_search_policy(keyword)

    response_text = f"مرحباً بك في بلدية مدار. بناءً على استفسارك، إليك الاشتراطات المعتمدة:\n\n{policy_result}"

    ctx.add_message("assistant", response_text)
    return {
        "reply": response_text,
        "context_memory_count": len(ctx.memory)
    }

@app.post("/issue-permit")
def issue_permit_endpoint(permit: PermitRequest):
    # إنشاء مسودة وبوابة موافقة بشرية
    draft = tool_issue_permit_draft(permit)
    approval = human_approval_gate(approval_status=True, permit_data=draft["data"])
    return {
        "draft_status": draft,
        "approval_result": approval
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8088)
