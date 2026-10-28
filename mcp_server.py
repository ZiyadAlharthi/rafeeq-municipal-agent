# ==============================================================================
# RAFEEQ (رفيق) - MCP Server & Tools Module (mcp_server.py)
# ==============================================================================

import os
from typing import Dict, Any, List
from pydantic import BaseModel, Field

class PermitRequest(BaseModel):
    applicant_name: str = Field(..., description="اسم مقدم الطلب")
    permit_type: str = Field(..., description="نوع التصريح (بناء, فود تراك, فعالية)")
    details: str = Field(..., description="تفاصيل الطلب والاشتراطات")

def tool_search_policy(query_keyword: str) -> str:
    """
    Tool 1 (Retrieval over Context File):
    البحث واسترجاع المعلومات مباشرة من ملف السياق policies.md بناءً على الكلمة المفتاحية.
    """
    policy_file = "policies.md"
    if not os.path.exists(policy_file):
        return "⚠️ تنبيه: ملف السياسات غير موجود في بيئة العمل."

    with open(policy_file, "r", encoding="utf-8") as f:
        content = f.read()

    # البحث البسيط داخل الملف واسترجاع القسم المناسب
    sections = content.split("## ")
    for section in sections:
        if query_keyword.lower() in section.lower():
            return "## " + section.strip()

    return "لم يتم العثور على اشتراط مطابق تماماً في أرشيف السياسات، يرجى مراجعة القسم العام."

def tool_check_applicant_status(national_id: str) -> str:
    """Tool 2: الاستعلام عن سجل وسوابق مقدم الطلب البلدي"""
    if len(national_id) != 10:
        return "رقم الهوية غير صحيح. يجب أن يتكون من 10 أرقام."
    return f"السجل البلدي للمواطن/ة صاحب الهوية {national_id}: سليم تماماً، ولا توجد مخالفات سابقة مسجلة."

def get_available_tools_registry() -> List[Dict[str, Any]]:
    """تسجيل الأدوات المتاحة لتوفيرها للوكيل (Agent)"""
    return [
        {
            "name": "tool_search_policy",
            "description": "استرجاع اللوائح والاشتراطات من ملف سياسات بلدية مدار (مثل: بناء، فود تراك، فعالية)",
            "parameters": {"query_keyword": "string"}
        },
        {
            "name": "tool_check_applicant_status",
            "description": "الاستعلام عن حالة السجل البلدي لمقدم الطلب عبر رقم الهوية",
            "parameters": {"national_id": "string"}
        }
    ]
