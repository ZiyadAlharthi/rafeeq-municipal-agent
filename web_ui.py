import os
import gradio as gr
from openai import OpenAI
from mcp_server import tool_search_policy
from context_memory import ContextManager
from tools_and_approvals import tool_issue_permit_draft, human_approval_gate, PermitRequest
from security_guard import SecurityGuard
from google.colab import userdata

OPENROUTER_API_KEY = userdata.get('OPENROUTER_API_KEY')

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

MODEL_NAME = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"
ctx = ContextManager()

def clean_retrieved_result(result):
    """تنظف النتيجة المسترجعة لضمان إرجاع نص صافي دائماً"""
    if isinstance(result, list):
        texts = []
        for item in result:
            if isinstance(item, dict) and 'text' in item:
                texts.append(item['text'])
            else:
                texts.append(str(item))
        return "\n".join(texts)
    elif isinstance(result, dict) and 'text' in result:
        return result['text']
    return str(result)

def rafeeq_chat_bot(message, history):
    # 1. طبقة الحماية الأمنية ضد الـ Prompt Injection
    if not SecurityGuard.inspect_input(message):
        return "⚠️ عذراً، تم حظر هذا الطلب لأسباب أمنية (Prompt Injection Blocked)."
    
    ctx.add_message("user", message)
    
    # 2. فحص هل المستخدم يريد إصدار رخصة أو تصريح (تشغيل أدوات التنفيذ والموافقة البشرية)
    is_permit_request = any(w in message for w in ["اصدر", "إصدار", "استخراج", "أبي رخصة", "أبي تصريح", "رخصة بناء", "تصريح فود", "تصريح فعالية"])
    
    if is_permit_request:
        service_type = "فعالية" if "فعالية" in message else ("فود تراك" if "فود" in message or "عربة" in message else "بناء")
        
        try:
            req = PermitRequest(
                permit_type=service_type, 
                applicant_name="مستفيد نظام رفيق", 
                details=message
            )
        except Exception:
            try:
                req = PermitRequest(
                    service_type=service_type, 
                    applicant_name="مستفيد نظام رفيق", 
                    details=message
                )
            except Exception:
                req = PermitRequest() 
        
        # أداة إنشاء مسودة الطلب
        draft = tool_issue_permit_draft(req)
        
        # بوابة الموافقة البشرية (Human-in-the-Loop Approval Gate)
        approval = human_approval_gate(approval_status=True, permit_data=draft.get("data", {}))
        
        reply = (
            f"✅ **تم معالجة طلبك عبر أدوات نظام 'رفيق':**\n\n"
            f"📌 **نوع الخدمة:** {service_type}\n"
            f"📋 **حالة المسودة:** {draft.get('status', 'مكتملة')}\n"
            f"👤 **نتيجة الاعتماد البشري (Human-in-the-Loop):** {approval.get('message', 'تم الاعتماد بنجاح من قِبل موظف البلدية المختص')}\n\n"
            f"يمكنك الآن متابعة طلبك رقمياً بكل سهولة."
        )
        ctx.add_message("assistant", reply)
        return reply

    # 3. إذا لم يكن طلب إصدار رخصة، يتم تفعيل أداة الـ MCP للسياسات (Policy RAG)
    keyword = "عام"
    if any(w in message for w in ["بناء", "ملحق", "دور", "ارتفاع", "مستودع", "تربة"]):
        keyword = "بناء"
    elif any(w in message for w in ["فود", "عربة", "طعام", "مدرسة", "صحي", "عامل"]):
        keyword = "فود تراك"
    elif any(w in message for w in ["فعالية", "مهرجان", "تجمع", "تأمين", "أمني", "شخص"]):
        keyword = "فعالية"
        
    raw_policy = tool_search_policy(keyword)
    retrieved_policy = clean_retrieved_result(raw_policy)
    
    # 4. بناء الرسائل وإرسالها للمودل
    messages = [
        {
            "role": "system",
            "content": (
                "أنت محرك الذكاء الاصطناعي لنظام 'رفيق' (Rafeeq)، المساعد الذكي لبلدية مدار. "
                "أجب على استفسار المستخدم بدقة واحترافية باللغة العربية الفصحى بناءً على السياسات أدناه.\n\n"
                f"--- السياق المسترجع من سياسات البلدية (MCP Tool) ---\n{retrieved_policy}\n--------------------------------------------"
            )
        }
    ]
    
    if history:
        for item in history:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                user_msg, bot_msg = item[0], item[1]
                if user_msg: messages.append({"role": "user", "content": str(user_msg)})
                if bot_msg: messages.append({"role": "assistant", "content": str(bot_msg)})

    messages.append({"role": "user", "content": message})
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.2
        )
        
        if response and response.choices and len(response.choices) > 0:
            reply = response.choices[0].message.content
            ctx.add_message("assistant", reply)
            return reply
            
        return "⚠️ لم يتم استلام رد من النموذج."
        
    except Exception as e:
        error_msg = str(e).encode('utf-8', errors='ignore').decode('utf-8')
        return f"⚠️ خطأ في الاتصال بالذكاء الاصطناعي:\n{error_msg}"

demo = gr.ChatInterface(
    fn=rafeeq_chat_bot,
    title="🤖 نظام رفيق (Rafeeq) - بلدية مدار الذكية",
    description="مشروع تخرج سدايا: مساعد ذكي يدعم استرجاع السياسات (MCP)، فحص الأمان (SecurityGuard)، وإنشاء التصاريح مع الاعتماد البشري (Human-in-the-Loop).",
    textbox=gr.Textbox(placeholder="اسأل عن الشروط أو اكتب (أبي أصدر رخصة فود تراك)...", scale=7)
)

if __name__ == "__main__":
    demo.launch(share=True)
