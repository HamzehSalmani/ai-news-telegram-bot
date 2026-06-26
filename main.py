"""نقطه‌ی ورود: یک اجرای کامل ایجنت خبری.

ترتیب: دریافت خبرها → فیلتر تکراری‌ها → برای هر خبر جدید:
استخراج تصویر → خلاصه‌سازی فارسی → ارسال به تلگرام → ثبت در دیتابیس.
"""

import logging
import time

import config
import dedup
import image_extractor
import selector
import summarizer
import telegram_poster
from fetcher import fetch_all

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("ai_news_agent")


def run() -> None:
    logger.info("شروع اجرای ایجنت خبری هوش مصنوعی.")
    articles = fetch_all()

    # فقط خبرهای جدید (ارسال‌نشده) را نگه دار
    fresh = [a for a in articles if dedup.is_new(a.link)]
    logger.info("تعداد %d خبر جدید (ارسال‌نشده) پیدا شد.", len(fresh))

    # کاربردی‌ترین‌ها را اولویت بده (مدل/قابلیت/ابزار/سرویس جدید)
    ranked = selector.select_useful(fresh)

    posted_count = 0
    for article in ranked:
        if posted_count >= config.MAX_POSTS_PER_RUN:
            logger.info("به سقف %d پست در این اجرا رسیدیم.", config.MAX_POSTS_PER_RUN)
            break

        logger.info("در حال پردازش: %s", article.title)

        # ۱) خلاصه‌سازی فارسی
        summary = summarizer.summarize(article.title, article.summary, article.link)
        if summary is None:
            logger.info("خلاصه‌سازی ناموفق بود؛ این خبر رد شد.")
            continue

        # ۲) تصویر: اول از خود فید، وگرنه از og:image صفحه‌ی مقاله
        image_url = article.image or image_extractor.extract_image(article.link)

        # ۳) ارسال به تلگرام
        if telegram_poster.post(summary, article.link, image_url):
            dedup.mark_posted(article.link, article.title)
            posted_count += 1
            logger.info("پست ارسال شد ✅ (%d/%d)", posted_count, config.MAX_POSTS_PER_RUN)
            # کمی مکث برای رعایت محدودیت نرخ تلگرام
            time.sleep(3)
        else:
            logger.warning("ارسال به تلگرام ناموفق بود؛ بدون ثبت در دیتابیس رد شد.")

    logger.info("پایان اجرا. تعداد پست‌های ارسال‌شده: %d", posted_count)


if __name__ == "__main__":
    try:
        run()
    except SystemExit:
        raise
    except Exception:  # noqa: BLE001 - لاگ کامل خطای پیش‌بینی‌نشده
        logger.exception("خطای پیش‌بینی‌نشده در اجرای ایجنت.")
        raise
