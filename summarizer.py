"""خلاصه‌سازی خبر به فارسیِ روان و بالت‌پوینت با استفاده از OpenRouter."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

from openai import OpenAI, OpenAIError

import config

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "تو ادمین یک کانال تلگرامی خبر هوش مصنوعی هستی و خبرها را خودمونی و صمیمی برای مخاطب فارسی‌زبان تعریف می‌کنی. "
    "لحن باید دوستانه و ساده باشد، انگار داری برای یک رفیق خبر را تعریف می‌کنی؛ نه خشک و رسمی. "
    "از زبان محاوره‌ای سبک و روان استفاده کن (مثلاً «اومده»، «می‌تونه»، «قراره») ولی شلخته و بی‌ادب نشو. "
    "اصطلاحات تخصصی را در صورت لزوم با حروف لاتین در پرانتز بیاور. "
    "دقیق بمان و چیزی از خودت اضافه نکن؛ فقط واقعیت‌های مهم خبر را با لحن خودمونی منتقل کن. "
    'فقط و فقط یک شیء JSON معتبر برگردان، بدون هیچ متن اضافه، با این ساختار: '
    '{"title": "تیتر کوتاه و گیرای فارسی حداکثر ۱۲ کلمه", '
    '"bullets": ["بالت ۱", "بالت ۲", "بالت ۳"]}. '
    "بین ۳ تا ۵ بالت بده؛ هر بالت یک جمله‌ی کوتاه و خودمونی."
)


@dataclass
class Summary:
    title: str
    bullets: list[str]


_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=config.OPENROUTER_API_KEY,
            base_url=config.OPENROUTER_BASE_URL,
        )
    return _client


def _extract_json(text: str) -> dict:
    """استخراج شیء JSON از خروجی مدل (با حذف احتمالی code fence)."""
    cleaned = text.strip()
    # حذف ```json ... ``` در صورت وجود
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # تلاش برای پیدا کردن اولین بلوک {...}
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def summarize(title: str, summary_text: str, link: str) -> Summary | None:
    """خبر را خلاصه می‌کند. در صورت خطا None برمی‌گرداند تا اجرای کلی متوقف نشود."""
    user_content = (
        f"عنوان اصلی خبر: {title}\n\n"
        f"متن/خلاصه‌ی منبع:\n{summary_text or '(متن کامل در دسترس نیست؛ از عنوان استفاده کن.)'}\n\n"
        f"لینک منبع: {link}\n\n"
        "این خبر را طبق دستورالعمل به فارسی خلاصه کن و خروجی JSON را بده. "
        "مجموع کل متن (تیتر + بالت‌ها) باید کوتاه و زیر ۸۰۰ کاراکتر بماند تا در کپشن تلگرام جا شود."
    )

    try:
        response = _get_client().chat.completions.create(
            model=config.OPENROUTER_MODEL,
            max_tokens=1000,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
        )
    except OpenAIError as exc:
        logger.warning("خطای OpenRouter در خلاصه‌سازی؛ این خبر رد شد: %s", exc)
        return None

    text = (response.choices[0].message.content or "").strip()
    if not text:
        logger.warning("خروجی خالی از مدل؛ این خبر رد شد.")
        return None

    try:
        data = _extract_json(text)
        bullets = [str(b).strip() for b in data.get("bullets", []) if str(b).strip()]
        title_fa = str(data.get("title", "")).strip()
        if not title_fa or not bullets:
            raise ValueError("title یا bullets خالی است")
        return Summary(title=title_fa, bullets=bullets)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("پارس خروجی مدل ناموفق بود؛ این خبر رد شد: %s", exc)
        return None
