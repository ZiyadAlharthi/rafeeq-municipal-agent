# ==============================================================================
# RAFEEQ (رفيق) - Context Engineering & Memory Module (context_memory.py)
# ==============================================================================

from typing import List, Dict

class ContextManager:
    def __init__(self, token_budget: int = 1500):
        self.token_budget = token_budget
        self.system_prompt = (
            "أنت 'رفيق' (Rafeeq)، المساعد الذكي لبلدية مدار (Madar Municipal Services). "
            "مهمتك مساعدة المواطنين والمستثمرين في استخراج وتوضيح اشتراطات رخص البناء، الفود تراك، والفعاليات "
            "باللغة العربية الفصحى وبدقة تامة استناداً إلى ملف السياسات والأدوات المتاحة."
        )
        self.memory: List[Dict[str, str]] = [
            {"role": "system", "content": self.system_prompt}
        ]

    def add_message(self, role: str, content: str):
        """إضافة رسالة جديدة للذاكرة مع تطبيق قاعدة تقليص السياق تلقائياً"""
        self.memory.append({"role": role, "content": content})
        self.compact_if_needed()

    def compact_if_needed(self):
        """
        قاعدة تقليص السياق (Context Compaction & Budget Rule):
        إذا زاد طول المحادثة عن ميزانية التوكنز المحددة، نقوم بضغط الرسائل القديمة
        والاحتفاظ بالبرومبت الأساسي وأحدث الرسائل لضمان عدم تجاوز الحد واستقرار الوكيل.
        """
        # تقدير تقريبي لعدد التوكنز بناءً على الكلمات
        estimated_tokens = sum(len(m["content"].split()) for m in self.memory) * 1.3

        if estimated_tokens > self.token_budget and len(self.memory) > 4:
            # الاحتفاظ برسالة النظام الأساسية + رسالة تنبيه بالضغط + آخر 3 رسائل تفاعلية
            compaction_notice = {
                "role": "system",
                "content": "[ملاحظة نظامية: تم ضغط المحادثات السابقة لتوفير ميزانية السياق (Token Budget)]."
            }
            recent_messages = self.memory[-3:]
            self.memory = [self.memory[0], compaction_notice] + recent_messages
