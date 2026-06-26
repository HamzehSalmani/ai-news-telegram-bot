# ایجنت خبری هوش مصنوعی برای تلگرام 🤖📰

ایجنتی که در زمان‌های مشخص به‌صورت خودکار، جدیدترین خبرهای هوش مصنوعی را از منابع معتبر می‌گیرد،
آن‌ها را با یک مدل زبانی (از طریق **OpenRouter**) به فارسیِ روان و بالت‌پوینت خلاصه می‌کند و همراه با عکس و رفرنس در کانال تلگرامت منتشر می‌کند.

## امکانات
- دریافت خبر از فیدهای RSS معتبر (OpenAI، DeepMind، TechCrunch، The Verge و …) + جستجوی وب تکمیلی
- خلاصه‌سازی فارسی روان و بی‌طرف به‌صورت بالت‌پوینت
- استخراج خودکار تصویر اصلی مقاله (`og:image`)
- جلوگیری از ارسال خبر تکراری (دیتابیس SQLite)
- زمان‌بندی خودکار با `cron`

---

## پیش‌نیازها
- یک سرور لینوکسی (یا هر سیستمی که همیشه روشن است) با **Python 3.10 یا بالاتر**
- یک کانال تلگرام که ادمین آن هستی
- کلید API از OpenRouter (برای مدل خلاصه‌سازی)

---

## مرحله ۱ — ساخت بات تلگرام
1. در تلگرام به [@BotFather](https://t.me/BotFather) پیام بده.
2. دستور `/newbot` را بفرست و نام و یوزرنیم بات را انتخاب کن.
3. BotFather یک **توکن** به تو می‌دهد، چیزی شبیه:
   `123456789:ABCdefGhIJKlmNoPQRsTUVwxyz`
   این همان `TELEGRAM_BOT_TOKEN` است. آن را جایی امن نگه دار.

## مرحله ۲ — افزودن بات به کانال
1. وارد کانالت شو → **Manage Channel** → **Administrators** → **Add Admin**.
2. بات را به‌عنوان ادمین اضافه کن و حتماً دسترسی **Post Messages** را روشن کن.

## مرحله ۳ — گرفتن آیدی کانال
- **کانال عمومی:** آیدی همان یوزرنیم با @ است، مثلاً `@my_ai_channel`.
- **کانال خصوصی:** به آیدی عددی نیاز داری (شبیه `-1001234567890`). برای گرفتنش:
  1. یک پیام در کانال بفرست.
  2. این آدرس را در مرورگر باز کن (توکن بات را جایگزین کن):
     `https://api.telegram.org/bot<TOKEN>/getUpdates`
  3. در خروجی، مقدار `chat.id` کانالت همان آیدی عددی است.

## مرحله ۴ — کلید OpenRouter
1. وارد [openrouter.ai](https://openrouter.ai) شو و حساب بساز.
2. مقداری اعتبار شارژ کن (مدل‌های Flash خیلی ارزان هستند).
3. از [openrouter.ai/keys](https://openrouter.ai/keys) یک کلید بساز.
4. این همان `OPENROUTER_API_KEY` است (با `sk-or-` شروع می‌شود).

---

## مرحله ۵ — نصب و تنظیم پروژه
روی سرور:

```bash
# کلون یا کپی پروژه، سپس وارد پوشه شو
cd Ai_news_agent

# ساخت محیط مجازی و نصب وابستگی‌ها
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# ساخت فایل .env از روی نمونه و پر کردن مقادیر
cp .env.example .env
nano .env   # توکن بات، آیدی کانال و کلید Anthropic را وارد کن
```

محتوای `.env` باید این‌گونه پر شود:

```
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyz
TELEGRAM_CHANNEL_ID=@my_ai_channel
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxx
OPENROUTER_MODEL=google/gemini-2.5-flash
MAX_POSTS_PER_RUN=3
ENABLE_WEB_SEARCH=false
```

---

## مرحله ۶ — تست دستی
```bash
source venv/bin/activate
python main.py
```
اگر همه‌چیز درست باشد، باید ۱ تا ۳ خبر فارسی همراه با عکس در کانالت ظاهر شود.
اجرای دوبارهٔ بلافاصله نباید خبر تکراری بفرستد (به‌خاطر دیتابیس `posted.db`).

---

## مرحله ۷ — زمان‌بندی خودکار با cron
برای اجرای خودکار (مثلاً هر ۶ ساعت یک‌بار):

```bash
crontab -e
```

این خط را اضافه کن (مسیرها را با مسیر واقعی پروژه و venv جایگزین کن):

```cron
0 */6 * * * cd /home/USER/Ai_news_agent && /home/USER/Ai_news_agent/venv/bin/python main.py >> agent.log 2>&1
```

> 💡 برای زمان‌بندی متفاوت از [crontab.guru](https://crontab.guru) کمک بگیر.
> مثلاً `0 9,15,21 * * *` یعنی هر روز ساعت ۹ صبح، ۳ بعدازظهر و ۹ شب.

لاگ اجراها در فایل `agent.log` ذخیره می‌شود.

---

## تنظیمات قابل‌تغییر (`.env`)
| متغیر | توضیح | پیش‌فرض |
|------|-------|--------|
| `MAX_POSTS_PER_RUN` | حداکثر تعداد خبر در هر اجرا | `3` |
| `OPENROUTER_MODEL` | مدل OpenRouter (جایگزین‌ها: `google/gemini-2.0-flash-001`، `openai/gpt-4o-mini`، `anthropic/claude-3.5-haiku`) | `google/gemini-2.5-flash` |
| `ENABLE_WEB_SEARCH` | جستجوی وب تکمیلی (مدل را `:online` می‌کند، هزینه‌ی اضافه دارد) | `false` |
| `MAX_ARTICLE_AGE_HOURS` | فقط خبرهای جدیدتر از این بازه (ساعت) | `48` |

برای افزودن/حذف منابع خبری، فایل `feeds.py` را ویرایش کن.

---

## ساختار پروژه
| فایل | نقش |
|------|-----|
| `config.py` | خواندن تنظیمات از `.env` |
| `feeds.py` | لیست فیدهای RSS |
| `fetcher.py` | دریافت خبرها (RSS + جستجوی وب) |
| `image_extractor.py` | استخراج تصویر مقاله |
| `summarizer.py` | خلاصه‌سازی فارسی با مدل OpenRouter |
| `dedup.py` | جلوگیری از ارسال تکراری (SQLite) |
| `telegram_poster.py` | ارسال پست به تلگرام |
| `main.py` | اجرای کامل ایجنت |

---

## عیب‌یابی
- **خطای «متغیر محیطی تنظیم نشده»:** فایل `.env` را بساز و مقادیر را پر کن.
- **پست در کانال ظاهر نمی‌شود:** مطمئن شو بات ادمین کانال است و دسترسی Post Messages دارد و `TELEGRAM_CHANNEL_ID` درست است.
- **خبری ارسال نمی‌شود:** احتمالاً همه‌ی خبرها قبلاً ارسال شده‌اند یا قدیمی‌تر از `MAX_ARTICLE_AGE_HOURS` هستند. برای تست از نو، فایل `posted.db` را پاک کن.
- **خطای کلید OpenRouter:** اعتبار کلید و موجودی حساب را در [openrouter.ai/credits](https://openrouter.ai/credits) بررسی کن.
