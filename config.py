"""بارگذاری تنظیمات از فایل .env و فراهم‌کردن مقادیر پیکربندی."""

import os
from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    """خواندن یک متغیر اجباری؛ در صورت نبود، خطای واضح می‌دهد."""
    value = os.getenv(name)
    if not value:
        raise SystemExit(
            f"خطا: متغیر محیطی «{name}» تنظیم نشده است. "
            f"فایل .env.example را به .env کپی کن و مقدار آن را پر کن."
        )
    return value


# --- متغیرهای اجباری ---
TELEGRAM_BOT_TOKEN = _require("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = _require("TELEGRAM_CHANNEL_ID")
OPENROUTER_API_KEY = _require("OPENROUTER_API_KEY")

# --- تنظیمات OpenRouter ---
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")

# --- تنظیمات اختیاری با مقدار پیش‌فرض ---
MAX_POSTS_PER_RUN = int(os.getenv("MAX_POSTS_PER_RUN", "3"))
# جستجوی وب OpenRouter (با افزودن :online به مدل). هزینه‌ی اضافه دارد؛ پیش‌فرض خاموش.
ENABLE_WEB_SEARCH = os.getenv("ENABLE_WEB_SEARCH", "false").lower() == "true"

# مسیر دیتابیس SQLite برای جلوگیری از ارسال تکراری
DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "posted.db"))

# حداکثر طول caption تلگرام برای sendPhoto (محدودیت رسمی API: 1024 کاراکتر)
TELEGRAM_CAPTION_LIMIT = 1024

# مهلت زمانی درخواست‌های HTTP (ثانیه)
HTTP_TIMEOUT = 15

# فقط خبرهایی که در این بازه (ساعت) منتشر شده‌اند در نظر گرفته شوند
MAX_ARTICLE_AGE_HOURS = int(os.getenv("MAX_ARTICLE_AGE_HOURS", "48"))
