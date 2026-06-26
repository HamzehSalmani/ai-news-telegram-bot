"""جلوگیری از ارسال خبر تکراری با استفاده از یک دیتابیس SQLite سبک."""

import hashlib
import sqlite3
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit

import config


def _normalize_url(url: str) -> str:
    """نرمال‌سازی URL: حذف query/fragment و اسلش انتهایی تا تکراری‌ها یکسان شوند."""
    parts = urlsplit(url.strip())
    path = parts.path.rstrip("/")
    return urlunsplit((parts.scheme, parts.netloc.lower(), path, "", ""))


def _url_hash(url: str) -> str:
    return hashlib.sha256(_normalize_url(url).encode("utf-8")).hexdigest()


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS posted (
            url_hash  TEXT PRIMARY KEY,
            title     TEXT,
            posted_at TEXT
        )
        """
    )
    return conn


def is_new(url: str) -> bool:
    """آیا این خبر قبلاً ارسال نشده است؟"""
    conn = _connect()
    try:
        cur = conn.execute(
            "SELECT 1 FROM posted WHERE url_hash = ?", (_url_hash(url),)
        )
        return cur.fetchone() is None
    finally:
        conn.close()


def mark_posted(url: str, title: str) -> None:
    """ثبت خبر به‌عنوان ارسال‌شده."""
    conn = _connect()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO posted (url_hash, title, posted_at) VALUES (?, ?, ?)",
            (_url_hash(url), title, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
    finally:
        conn.close()
