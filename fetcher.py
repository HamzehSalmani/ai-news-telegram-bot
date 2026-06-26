"""دریافت خبرها از فیدهای RSS و (به‌صورت اختیاری) جستجوی وب تکمیلی."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from time import mktime

import feedparser

import config
from feeds import RSS_FEEDS

logger = logging.getLogger(__name__)


@dataclass
class Article:
    title: str
    link: str
    summary: str
    published: datetime | None = None
    image: str | None = None  # اگر فید خودش تصویر داشت


def _parse_published(entry) -> datetime | None:
    """تبدیل زمان انتشار فید به datetime با timezone."""
    for key in ("published_parsed", "updated_parsed"):
        t = entry.get(key)
        if t:
            return datetime.fromtimestamp(mktime(t), tz=timezone.utc)
    return None


def _extract_feed_image(entry) -> str | None:
    """اگر آیتم فید media/enclosure تصویری داشت، آن را برمی‌گرداند."""
    # media_content / media_thumbnail (استاندارد Media RSS)
    for key in ("media_content", "media_thumbnail"):
        media = entry.get(key)
        if media and isinstance(media, list):
            url = media[0].get("url")
            if url and url.startswith(("http://", "https://")):
                return url
    # enclosure
    for link in entry.get("links", []):
        if link.get("rel") == "enclosure" and str(link.get("type", "")).startswith("image"):
            return link.get("href")
    return None


def fetch_rss() -> list[Article]:
    """همه‌ی فیدها را می‌خواند، فیلتر سن می‌کند و لیست مرتب‌شده برمی‌گرداند."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=config.MAX_ARTICLE_AGE_HOURS)
    articles: list[Article] = []

    for url in RSS_FEEDS:
        try:
            parsed = feedparser.parse(url)
        except Exception as exc:  # feedparser معمولاً خطا نمی‌اندازد، ولی محتاط باشیم
            logger.warning("خواندن فید ناموفق بود (%s): %s", url, exc)
            continue

        if parsed.bozo and not parsed.entries:
            logger.warning("فید معتبر نبود یا خالی بود: %s", url)
            continue

        for entry in parsed.entries:
            link = entry.get("link")
            title = entry.get("title")
            if not link or not title:
                continue

            published = _parse_published(entry)
            # اگر زمان انتشار مشخص است و قدیمی‌تر از cutoff است، رد کن
            if published and published < cutoff:
                continue

            articles.append(
                Article(
                    title=title.strip(),
                    link=link.strip(),
                    summary=(entry.get("summary") or "").strip(),
                    published=published,
                    image=_extract_feed_image(entry),
                )
            )

    # جدیدترین‌ها اول (آیتم‌های بدون تاریخ ته لیست)
    articles.sort(key=lambda a: a.published or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    logger.info("تعداد %d خبر از RSS دریافت شد.", len(articles))
    return articles


def fetch_web_search() -> list[Article]:
    """جستجوی وب تکمیلی با قابلیت :online از OpenRouter.

    اگر ENABLE_WEB_SEARCH خاموش باشد یا خطایی رخ دهد، لیست خالی برمی‌گرداند.
    این تابع فقط تیتر و لینک را برای پوشش خبرهای تازه‌ای که در فیدها نیستند می‌آورد.
    """
    if not config.ENABLE_WEB_SEARCH:
        return []

    try:
        from openai import OpenAI, OpenAIError
    except ImportError:
        logger.warning("کتابخانه openai نصب نیست؛ جستجوی وب رد شد.")
        return []

    client = OpenAI(
        api_key=config.OPENROUTER_API_KEY,
        base_url=config.OPENROUTER_BASE_URL,
    )

    # افزودن :online تا OpenRouter قبل از پاسخ، وب را جستجو کند
    online_model = config.OPENROUTER_MODEL
    if not online_model.endswith(":online"):
        online_model = f"{online_model}:online"

    try:
        response = client.chat.completions.create(
            model=online_model,
            max_tokens=1500,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "جدیدترین خبرهای مهم حوزه‌ی هوش مصنوعی در ۲۴ ساعت گذشته را جستجو کن. "
                        "فقط خبرهای واقعی و معتبر. خروجی را دقیقاً به این صورت بده، هر خبر در یک خط:\n"
                        "TITLE ||| URL\n"
                        "حداکثر ۵ خبر. هیچ توضیح اضافه‌ای نده."
                    ),
                }
            ],
        )
    except OpenAIError as exc:
        logger.warning("جستجوی وب با OpenRouter ناموفق بود: %s", exc)
        return []

    text = (response.choices[0].message.content or "")

    articles: list[Article] = []
    for line in text.splitlines():
        if "|||" not in line:
            continue
        title, _, link = line.partition("|||")
        title, link = title.strip(), link.strip()
        if link.startswith(("http://", "https://")) and title:
            articles.append(Article(title=title, link=link, summary=""))

    logger.info("تعداد %d خبر از جستجوی وب دریافت شد.", len(articles))
    return articles


def fetch_all() -> list[Article]:
    """ترکیب RSS و جستجوی وب، با حذف لینک‌های تکراری در همین اجرا."""
    seen_links: set[str] = set()
    combined: list[Article] = []

    for article in fetch_rss() + fetch_web_search():
        key = article.link.rstrip("/").lower()
        if key in seen_links:
            continue
        seen_links.add(key)
        combined.append(article)

    return combined
