# ==============================================================================
# RAFEEQ (رفيق) - Tools, Approvals & Budgets Module (tools_and_approvals.py)
# ==============================================================================

from typing import Dict, Any
from pydantic import BaseModel, Field

class PermitRequest(BaseModel):
    applicant_name: str = Field(..., description="اسم مقدم الطلب")
    permit_type: str = Field(..., description="نوع التصريح (بناء, فود تراك, فعالية)")
    details: str = Field(..., description="تفاصيل الطلب والاشتراطات")

class BudgetManager:
    """إدارة ميزانية الخطوات والتكلفة (Step and Cost Budgets) للوكيل"""
    def __init__(self, max_steps: int = 6, max_cost_usd: float = 0.05):
        self.max_steps = max_steps
        self.max_cost_usd = max_cost_usd
        self.current_steps = 0
        self.estimated_cost = 0.0

    def track_step(self):
        self.current_steps += 1
        self.estimated_cost += 0.0015  # تكلفة تقديرية لكل خطوة نموذج
        if self.current_steps > self.max_steps:
            raise Exception("⚠️ تجاوز الحد الأقصى لخطوات الوكيل (Step Budget Exceeded). تم إيقاف التنفيذ لحماية الميزانية.")

def tool_issue_permit_draft(request: PermitRequest) -> Dict[str, Any]:
    """
    أداة كتابة (Write Action) تتطلب بوابة موافقة بشرية (Human Approval Gate):
    تقوم بإنشاء مسودة تصريح رسمي ولا تعتمد نهائياً إلا بموافقة موظف البلدية.
    """
    return {
        "status": "PENDING_APPROVAL",
        "action": "ISSUE_PERMIT",
        "data": request.model_dump(),
        "message": "⚠️ تم إنشاء مسودة التصريح بنجاح. تتطلب هذه العملية موافقة موظف الاعتماد المختص ببلدية مدار قبل الإصدار النهائي."
    }

def human_approval_gate(approval_status: bool, permit_data: Dict[str, Any]) -> str:
    """محاكاة بوابة المراجعة والموافقة البشرية (Human-in-the-Loop Gate)"""
    if approval_status:
        return f"✅ تمت الموافقة البشرية بنجاح! تم اعتماد وإصدار التصريح رسمياً : {permit_data['applicant_name']}."
    else:
        return "❌ تم رفض الطلب من قبل موظف الاعتماد المختص وإعادته للمستثمر للتعديل."
