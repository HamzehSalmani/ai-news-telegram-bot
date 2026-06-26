"""استخراج تصویر شاخص (og:image) از صفحه‌ی مقاله."""

from __future__ import annotations

import logging

import requests
from bs4 import BeautifulSoup

import config

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; AINewsBot/1.0; +https://example.com/bot)"
    )
}


def _is_valid_image_url(url: str) -> bool:
    return isinstance(url, str) and url.startswith(("http://", "https://"))


def extract_image(article_url: str) -> str | None:
    """تصویر شاخص مقاله را برمی‌گرداند؛ اگر پیدا نشد None.

    ابتدا og:image و سپس twitter:image را بررسی می‌کند.
    """
    if not _is_valid_image_url(article_url):
        return None

    try:
        resp = requests.get(
            article_url, headers=_HEADERS, timeout=config.HTTP_TIMEOUT
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("دریافت صفحه برای استخراج عکس ناموفق بود (%s): %s", article_url, exc)
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    for prop in ("og:image", "og:image:url", "twitter:image"):
        tag = soup.find("meta", attrs={"property": prop}) or soup.find(
            "meta", attrs={"name": prop}
        )
        if tag and tag.get("content"):
            img_url = tag["content"].strip()
            if _is_valid_image_url(img_url):
                return img_url

    return None
