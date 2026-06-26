"""انتخاب کاربردی‌ترین خبرها از بین کاندیداها.

هدف: خبرهایی که به‌روز نگه‌مان می‌دارند را اولویت بده — مدل جدید، قابلیت/امکان
جدید مدل‌ها، ابزار/سرویس/API جدید، انتشار مهم فنی. خبرهای کلی و کم‌فایده مثل
سیاست‌گذاری، سرمایه‌گذاری، دعوای حقوقی، تبلیغ رویداد، و تحلیل‌های عمومی را کنار بگذار.
"""

from __future__ import annotations

import json
import logging
import re

from openai import OpenAIError

import config
from fetcher import Article
from summarizer import _extract_json, _get_client

logger = logging.getLogger(__name__)

# نشانه‌های متنیِ خبر «غیرکاربردی» برای فیلتر اولیه‌ی ارزان (پیش از تماس با مدل).
# اگر عنوان آشکارا تبلیغ رویداد یا خبر مالی/سیاسی باشد، همان‌جا حذف می‌شود.
_NOISE_PATTERNS = (
    "pricing ends", "early bird", "register now", "buy tickets", "ticket",
    "summit", "conference", "webinar", "join us", "save the date",
    "raises $", "funding round", "series a", "series b", "series c",
    "valuation", "ipo", "lawsuit", "sues", "court", "regulation",
    "regulator", "lobby", "election", "op-ed", "opinion",
)

_SELECT_PROMPT = (
    "تو سردبیر یک کانال خبری هوش مصنوعی هستی که مخاطبش می‌خواهد «به‌روز و کاربردی» بماند. "
    "از فهرست عنوان‌های زیر، فقط خبرهای واقعاً کاربردی را انتخاب کن؛ یعنی:\n"
    "- مدل جدید یا نسخه‌ی جدید یک مدل\n"
    "- قابلیت/امکان جدید مدل‌ها\n"
    "- ابزار، سرویس، API یا اپ جدید مرتبط با AI\n"
    "- انتشار مهم فنی (open-source، weights، SDK، بنچمارک مهم)\n\n"
    "این‌ها را انتخاب نکن: سیاست‌گذاری/قانون‌گذاری، سرمایه‌گذاری و خبرهای مالی، "
    "دعوای حقوقی، تبلیغ رویداد/کنفرانس، و تحلیل‌ها و نظرهای کلی (مثل «کشور X می‌خواهد روی AI کار کند»).\n\n"
    "فقط یک آرایه‌ی JSON از شماره‌ی خبرهای انتخابی برگردان، به‌ترتیب اولویت کاربردی‌بودن، "
    'مثل {"selected": [3, 7, 1]}. اگر هیچ خبر کاربردی‌ای نبود، آرایه‌ی خالی بده.'
)


def _passes_keyword_filter(title: str) -> bool:
    """فیلتر اولیه‌ی ارزان: حذف عنوان‌هایی که آشکارا غیرکاربردی‌اند."""
    low = title.lower()
    return not any(p in low for p in _NOISE_PATTERNS)


def select_useful(articles: list[Article]) -> list[Article]:
    """خبرها را بر اساس کاربردی‌بودن مرتب و فیلتر می‌کند.

    اگر تماس با مدل ناموفق بود، به فیلتر کلمات کلیدی + ترتیب اولیه (جدیدترین) برمی‌گردد.
    """
    if not articles:
        return []

    # ۱) فیلتر اولیه‌ی ارزان
    candidates = [a for a in articles if _passes_keyword_filter(a.title)]
    if not candidates:
        candidates = list(articles)  # اگر همه فیلتر شدند، چیزی را از دست نده

    # برای صرفه‌جویی، حداکثر ۳۰ عنوان اول (جدیدترین‌ها) را به مدل بده
    candidates = candidates[:30]

    listing = "\n".join(f"{i}. {a.title}" for i, a in enumerate(candidates))
    user_content = f"فهرست خبرها:\n{listing}"

    try:
        response = _get_client().chat.completions.create(
            model=config.OPENROUTER_MODEL,
            max_tokens=200,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _SELECT_PROMPT},
                {"role": "user", "content": user_content},
            ],
        )
        text = (response.choices[0].message.content or "").strip()
        data = _extract_json(text)
        indices = data.get("selected", [])
        ordered = [candidates[i] for i in indices if isinstance(i, int) and 0 <= i < len(candidates)]
        if ordered:
            logger.info("انتخابگر: %d خبر کاربردی از %d کاندیدا انتخاب شد.", len(ordered), len(candidates))
            return ordered
        logger.info("انتخابگر چیزی برنگرداند؛ از ترتیب پیش‌فرض استفاده می‌شود.")
    except (OpenAIError, json.JSONDecodeError, ValueError, KeyError, TypeError) as exc:
        logger.warning("انتخابگر کاربردی ناموفق بود؛ فالبک به فیلتر ساده: %s", exc)

    # فالبک: همان کاندیداهای فیلترشده با ترتیب اولیه (جدیدترین اول)
    return candidates
