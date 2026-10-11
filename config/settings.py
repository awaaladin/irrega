"""Routine Irrigation Technology settings. Configure through .env (see .env.example)."""
import os
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
# ENV_FILE=.env.production python manage.py ...   (remote database; the default .env is for local development)
load_dotenv(BASE_DIR / os.environ.get("ENV_FILE", ".env"))


def env(key, default=""):
    return os.environ.get(key, default)


SECRET_KEY = env("SECRET_KEY", "dev-only-insecure-key-change-me")
DEBUG = env("DEBUG", "1") == "1"
ALLOWED_HOSTS = [h for h in env("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",") if h]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "apps.core",
    "apps.accounts",
    "apps.farms",
    "apps.engine",
    "apps.providers",
    "apps.decisions",
    "apps.assistant",
    "apps.notifications",
    "apps.billing",
    "apps.partners",
    "apps.demo",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.SimpleRateLimitMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context.shell",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# SQLite for local dev. DATABASE_URL=postgres://... for Postgres/Supabase.
# This project lives in its own `irriga` schema under a restricted role (search_path is pinned on the role), so it never
# sees other apps' tables in a shared database. Use DB_MODE=session to run migrations through the session-mode pooler.
_db = env("DATABASE_URL_SESSION") if env("DB_MODE") == "session" and env("DATABASE_URL_SESSION") else env("DATABASE_URL")
_testing = "test" in sys.argv  # tests must never reach a real database
if _db.startswith("postgres") and not _testing:
    u = urlparse(_db)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": u.path.lstrip("/") or "postgres",
            "USER": unquote(u.username or ""),
            "PASSWORD": unquote(u.password or ""),
            "HOST": u.hostname,
            "PORT": u.port or 5432,
            "CONN_MAX_AGE": 0,  # serverless: do not hold connections between requests
            "DISABLE_SERVER_SIDE_CURSORS": True,  # required by transaction-mode poolers (pgbouncer / Supavisor)
            "OPTIONS": {"sslmode": "require", "connect_timeout": 15},
        }
    }
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = ["apps.accounts.backends.EmailOrPhoneBackend"]
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
]

LANGUAGE_CODE = "en"
TIME_ZONE = "Africa/Lagos"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
WHITENOISE_USE_FINDERS = True  # serve app/static straight from source: no collectstatic step on serverless hosts
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Providers
ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = env("ANTHROPIC_MODEL", "claude-sonnet-5-5")
SATELLITE_PROVIDER = env("SATELLITE_PROVIDER", "simulated")  # simulated | sentinelhub
SENTINELHUB_CLIENT_ID = env("SENTINELHUB_CLIENT_ID")
SENTINELHUB_CLIENT_SECRET = env("SENTINELHUB_CLIENT_SECRET")
WEATHER_STALE_HOURS = int(env("WEATHER_STALE_HOURS", "6"))
DEMO_MODE = env("DEMO_MODE", "1") == "1"

CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "SAMEORIGIN"
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"  # map tile providers require a Referer

if not DEBUG:
    if SECRET_KEY.startswith("dev-only") or len(SECRET_KEY) < 50:
        raise RuntimeError("Set a strong SECRET_KEY (python -c \"import secrets; print(secrets.token_urlsafe(64))\").")
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")  # Vercel terminates TLS
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    CSRF_TRUSTED_ORIGINS = [o for o in env("CSRF_TRUSTED_ORIGINS", "https://*.vercel.app").split(",") if o]
