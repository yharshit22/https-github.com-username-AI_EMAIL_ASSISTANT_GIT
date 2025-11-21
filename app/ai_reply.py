import os
import logging
from typing import Optional, Any

import google.generativeai as genai

logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# Custom closing signature for all AI replies
# ---------------------------------------------------------
CLOSING_SIGNATURE = "जय श्री राम,\nBest regards,\nHarshit's AI Assistant (MOTU.AI)"


class AIReplyGenerator:
    """AI-powered email reply generator using Google Gemini."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: int = 512,
    ):
        # API key auto-load
        if api_key is None:
            api_key = os.getenv("GEMINI_API_KEY")

        # Model name: env override -> default
        if model_name is None:
            # You can override this in .env / Render:
            # GEMINI_MODEL=gemini-2.5-flash-lite  (or gemini-2.5-flash, gemini-2.0-flash, etc.)
            model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens

        self._initialized = False
        self._model: Optional[genai.GenerativeModel] = None

        # Fallback templates (used when Gemini key missing or model fails)
        self.templates = {
            "positive": {
                "high": "Thank you for your positive feedback! I really appreciate your kind words and I'm glad I could help.",
                "medium": "Thank you for your message and positive feedback. I appreciate it and will continue doing my best.",
                "low": "Thanks for reaching out with your positive message — it means a lot!",
            },
            "negative": {
                "high": "I sincerely apologize for the inconvenience you've experienced. Let me address this immediately and work on a resolution for you.",
                "medium": "I'm sorry to hear about your experience. I'll look into this and get back to you with a solution.",
                "low": "Thank you for sharing this. I'll review it and follow up shortly.",
            },
            "neutral": {
                "high": "Thank you for your detailed message. I'll prioritize this and respond with the information you need.",
                "medium": "Thank you for your message. I'll review it and reply accordingly.",
                "low": "Thanks for reaching out. I'll get back to you soon.",
            },
        }

        if not self.api_key:
            logger.error("GEMINI_API_KEY not configured; fallback replies only.")
            return

        try:
            genai.configure(api_key=self.api_key)
            # Old google-generativeai SDK still takes model id as a string
            self._model = genai.GenerativeModel(self.model_name)
            self._initialized = True
            logger.info("Gemini initialized (model=%s)", self.model_name)
        except Exception as exc:
            logger.exception("Gemini initialization failed: %s", exc)
            self._initialized = False

    # ------------------------------------------------------------------
    # Internal Gemini caller
    # ------------------------------------------------------------------
    def _call_gemini(self, prompt: str) -> Optional[str]:
        if not self._initialized:
            return None
        try:
            response = self._model.generate_content(
                prompt,
                generation_config={
                    "temperature": self.temperature,
                    "max_output_tokens": self.max_output_tokens,
                },
            )
            text = (getattr(response, "text", "") or "").strip()
            if not text:
                logger.warning("Gemini returned empty text.")
                return None
            return text
        except Exception as exc:
            logger.exception("Gemini error: %s", exc)
            return None

    # ------------------------------------------------------------------
    # MAIN: generate reply
    # ------------------------------------------------------------------
    def generate_reply(
        self,
        email: Any,
        sentiment: str = None,
        priority: str = None,
    ) -> Optional[str]:
        subject = getattr(email, "subject", "") or ""
        body = getattr(email, "body", "") or ""
        from_address = getattr(email, "from_address", "") or ""

        # Limit body length for safety
        body_snippet = body[:2000]

        if not sentiment:
            sentiment = getattr(email, "sentiment", None) or "neutral"
        if not priority:
            priority = getattr(email, "priority", None) or "medium"

        if not self._initialized:
            return self._generate_fallback_reply(email, sentiment, priority)

        prompt = f"""
You are an AI email assistant. Read the email and write a clear, professional, unique reply.

### EMAIL DETAILS
From: {from_address}
Subject: {subject}

Body:
{body_snippet}

### CONTEXT
Sentiment: {sentiment}
Priority: {priority}

### RULES
1. Identify the purpose of the email (question, complaint, info, promo, spam, etc.).
2. Mention at least ONE specific detail from the email (subject or body).
3. If the email contains questions → answer them clearly.
4. If it is promotional/spam → politely decline but reference its topic.
5. Tone rules:
   - negative + high → empathy + urgency
   - negative + medium → calm + reassuring
   - neutral → clear + direct
   - positive → appreciative
6. Reply should be 6–12 lines.
7. Reply in first person ("I").
8. Start with “Hi …” or “Hello …”.
9. Do NOT use placeholders like [Your Name].
10. Do NOT add any signature; the system will append it.

Now write ONLY the reply email text, without any signature.
""".strip()

        reply_text = self._call_gemini(prompt)
        if not reply_text:
            return self._generate_fallback_reply(email, sentiment, priority)

        # Always append our custom signature
        return reply_text.rstrip() + "\n\n" + CLOSING_SIGNATURE

    # ------------------------------------------------------------------
    # Regenerate reply
    # ------------------------------------------------------------------
    def regenerate_reply(
        self,
        email: Any,
        custom_instructions: str = None,
    ) -> Optional[str]:
        if not self._initialized:
            return None

        subject = getattr(email, "subject", "") or ""
        body = getattr(email, "body", "") or ""
        sentiment = getattr(email, "sentiment", None) or "neutral"
        priority = getattr(email, "priority", None) or "medium"

        prompt = f"""
Generate a different reply to the following email.

Subject: {subject}
Sentiment: {sentiment}
Priority: {priority}

Message:
{body}

Additional instructions:
{custom_instructions or "Provide a fresh alternative but still professional and helpful."}

Write only the reply email text, without any signature.
""".strip()

        reply_text = self._call_gemini(prompt)
        if not reply_text:
            return None

        return reply_text.rstrip() + "\n\n" + CLOSING_SIGNATURE

    # ------------------------------------------------------------------
    # Improve an existing reply
    # ------------------------------------------------------------------
    def improve_reply(
        self,
        original_reply: str,
        improvement_type: str = "more_professional",
    ) -> Optional[str]:
        if not self._initialized:
            return None

        instructions = {
            "more_professional": "Make this reply more polished and formally professional.",
            "more_friendly": "Make this reply friendlier and more conversational.",
            "more_detailed": "Add more helpful detail without making it too long.",
            "more_concise": "Shorten this reply while keeping all important meaning.",
            "more_empathetic": "Increase empathy and emotional understanding.",
        }

        rule = instructions.get(improvement_type, "Improve this reply.")

        prompt = f"""
{rule}

Original reply (without signature):
{original_reply}

Return only the improved reply text, without any signature.
""".strip()

        improved = self._call_gemini(prompt)
        if not improved:
            return None

        return improved.rstrip() + "\n\n" + CLOSING_SIGNATURE

    # ------------------------------------------------------------------
    # Fallback system
    # ------------------------------------------------------------------
    def _generate_fallback_reply(
        self,
        email: Any,
        sentiment: str,
        priority: str,
    ) -> str:
        sentiment = sentiment or "neutral"
        priority = priority or "medium"

        base = self.templates.get(sentiment, {}).get(
            priority,
            "Thank you for your message. I'll review it and get back shortly.",
        )

        reply = base + "\n\n"
        body = getattr(email, "body", "") or ""

        if "?" in body:
            reply += "I'll be happy to answer your questions soon.\n\n"

        reply += CLOSING_SIGNATURE
        return reply


# ----------------------------------------------------------------------
# GLOBAL COMPAT WRAPPERS (your routes expect these)
# ----------------------------------------------------------------------
_ai_reply_generator: Optional[AIReplyGenerator] = None


def _get_or_init_global() -> AIReplyGenerator:
    global _ai_reply_generator
    if _ai_reply_generator is None:
        _ai_reply_generator = AIReplyGenerator()
    return _ai_reply_generator


def init_ai_reply_generator(app=None):
    global _ai_reply_generator
    _ai_reply_generator = _get_or_init_global()


def generate_reply(
    email: Any,
    sentiment: str = None,
    priority: str = None,
) -> Optional[str]:
    return _get_or_init_global().generate_reply(email, sentiment, priority)


def regenerate_reply(
    email: Any,
    custom_instructions: str = None,
) -> Optional[str]:
    return _get_or_init_global().regenerate_reply(email, custom_instructions)


def improve_reply(
    original_reply: str,
    improvement_type: str = "more_professional",
) -> Optional[str]:
    return _get_or_init_global().improve_reply(original_reply, improvement_type)
