"""ارسال پست به کانال تلگرام از طریق Bot API."""

from __future__ import annotations

import html
import logging
import time

import requests

import config
from summarizer import Summary

logger = logging.getLogger(__name__)

_API_BASE = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}"


def build_message(summary: Summary, source_url: str) -> str:
    """ساخت متن پیام با فرمت HTML (مناسب parse_mode=HTML تلگرام).

    از HTML استفاده می‌کنیم چون با متن فارسی و لینک‌ها دردسر کمتری از Markdown دارد.
    """
    title = html.escape(summary.title)
    bullets = "\n".join(f"🔹 {html.escape(b)}" for b in summary.bullets)
    source = html.escape(source_url)

    return (
        f"<b>{title}</b>\n\n"
        f"{bullets}\n\n"
        f'🔗 <a href="{source}">منبع خبر</a>\n'
        f"#هوش_مصنوعی #AI"
    )


def _request(method: str, payload: dict) -> bool:
    """یک درخواست به Bot API می‌فرستد و خطای 429 را با احترام به retry_after مدیریت می‌کند."""
    url = f"{_API_BASE}/{method}"
    for attempt in range(3):
        try:
            resp = requests.post(url, data=payload, timeout=config.HTTP_TIMEOUT)
        except requests.RequestException as exc:
            logger.warning("ارسال به تلگرام ناموفق بود (%s): %s", method, exc)
            return False

        if resp.status_code == 429:
            retry_after = resp.json().get("parameters", {}).get("retry_after", 5)
            logger.info("محدودیت نرخ تلگرام؛ %d ثانیه صبر می‌کنیم.", retry_after)
            time.sleep(retry_after + 1)
            continue

        if resp.ok:
            return True

        logger.warning("تلگرام خطا برگرداند (%s): %s", method, resp.text)
        return False

    return False


def post(summary: Summary, source_url: str, image_url: str | None) -> bool:
    """پست را به کانال می‌فرستد.

    - اگر عکس داشته باشیم و متن در کپشن جا شود → sendPhoto با کپشن.
    - اگر عکس داشته باشیم ولی متن طولانی باشد → sendPhoto با کپشن کوتاه + sendMessage کامل.
    - اگر عکس نداشته باشیم → فقط sendMessage.
    """
    message = build_message(summary, source_url)

    if image_url and len(message) <= config.TELEGRAM_CAPTION_LIMIT:
        return _request(
            "sendPhoto",
            {
                "chat_id": config.TELEGRAM_CHANNEL_ID,
                "photo": image_url,
                "caption": message,
                "parse_mode": "HTML",
            },
        )

    if image_url:
        # کپشن خیلی بلند است: عکس را با تیتر بفرست، سپس متن کامل را جدا بفرست.
        short_caption = html.escape(summary.title)[: config.TELEGRAM_CAPTION_LIMIT]
        photo_ok = _request(
            "sendPhoto",
            {
                "chat_id": config.TELEGRAM_CHANNEL_ID,
                "photo": image_url,
                "caption": short_caption,
            },
        )
        text_ok = _request(
            "sendMessage",
            {
                "chat_id": config.TELEGRAM_CHANNEL_ID,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
        )
        return photo_ok or text_ok

    # بدون عکس: فقط پیام متنی
    return _request(
        "sendMessage",
        {
            "chat_id": config.TELEGRAM_CHANNEL_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        },
    )
