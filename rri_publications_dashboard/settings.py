"""
Django settings for rri_publications_dashboard project.
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

# --- BASE DIRECTORIES ---
BASE_DIR = Path(__file__).resolve().parent.parent


# --- ENVIRONMENT LOADING & HELPERS ---
def _load_env_file(env_path: Path) -> None:
    """Load environment variables from a .env file without overwriting existing environment."""
    if not env_path.is_file():
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip().strip("'\"")
                os.environ.setdefault(key, val)


_load_env_file(BASE_DIR / ".env")


def _parse_bool(name: str, value: str | None, default: bool = False) -> bool:
    """Strict boolean parser for environment variables.

    Returns default if value is None or empty.
    Raises ImproperlyConfigured for invalid/unrecognized boolean strings.
    """
    if value is None or str(value).strip() == "":
        return default
    normalized = str(value).strip().lower()
    if normalized in ("true", "1", "yes", "t", "on"):
        return True
    if normalized in ("false", "0", "no", "f", "off"):
        return False
    raise ImproperlyConfigured(
        f"Invalid boolean value for environment variable '{name}': '{value}'. "
        f"Allowed values are 'true', 'false', '1', '0', 'yes', 'no', 't', 'f', 'on', 'off'."
    )


def _parse_list(value: str | None) -> list[str]:
    """Parse comma-separated string into a trimmed, non-empty list of strings."""
    if not value:
        return []
    return [item.strip() for item in str(value).split(",") if item.strip()]


# --- CORE SECURITY SETTINGS ---
DEBUG = _parse_bool("DEBUG", os.environ.get("DEBUG"), default=False)

# SECRET_KEY resolution and fail-closed validation
# DJANGO_SECRET_KEY is canonical; SECRET_KEY is supported for legacy/deployment compatibility.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or os.environ.get("SECRET_KEY")

# Stable fallback key used ONLY in development (DEBUG=True) when no environment key is provided.
# A fixed dev fallback avoids generating a new ephemeral key per process restart, which would
# invalidate sessions and CSRF tokens across reloads.
DEV_SECRET_KEY_FALLBACK = "django-insecure-development-only-fallback-key-do-not-use-in-production"

if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = DEV_SECRET_KEY_FALLBACK
    else:
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY environment variable is required when DEBUG is False."
        )
elif not DEBUG:
    if SECRET_KEY.startswith("django-insecure-") or len(SECRET_KEY) < 50:
        raise ImproperlyConfigured(
            "Insecure DJANGO_SECRET_KEY detected in production. A secure, random key of at least 50 characters is required."
        )

# ALLOWED_HOSTS resolution and non-wildcard production enforcement
raw_allowed_hosts = os.environ.get("ALLOWED_HOSTS", "")
parsed_hosts = _parse_list(raw_allowed_hosts)

if DEBUG:
    dev_hosts = ["localhost", "127.0.0.1", "[::1]"]
    if parsed_hosts:
        ALLOWED_HOSTS = list(dict.fromkeys(parsed_hosts + dev_hosts))
    else:
        ALLOWED_HOSTS = dev_hosts
else:
    if not parsed_hosts:
        raise ImproperlyConfigured(
            "ALLOWED_HOSTS environment variable is required and cannot be empty when DEBUG is False."
        )
    if "*" in parsed_hosts:
        raise ImproperlyConfigured(
            "Wildcard '*' in ALLOWED_HOSTS is not permitted in production (when DEBUG is False)."
        )
    ALLOWED_HOSTS = parsed_hosts


# --- APPLICATION DEFINITION ---
INSTALLED_APPS = [
    # Django core apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party apps
    "tailwind",
    "theme",
    "django_filters",

    # Local project apps
    "accounts",
    "publications",
    "dashboard",
]

if DEBUG:
    # Add django_browser_reload only in DEBUG mode
    INSTALLED_APPS += ["django_browser_reload"]


# --- MIDDLEWARE ---
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

if DEBUG:
    # Add django_browser_reload middleware only in DEBUG mode
    MIDDLEWARE += [
        "django_browser_reload.middleware.BrowserReloadMiddleware",
    ]


# --- URLS & WSGI ---
ROOT_URLCONF = "rri_publications_dashboard.urls"
WSGI_APPLICATION = "rri_publications_dashboard.wsgi.application"


# --- TEMPLATES ---
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "dashboard.context_processors.dashboard_sidebar",
            ],
        },
    },
]


# --- AUTHENTICATION & USERS ---
AUTH_USER_MODEL = "accounts.CustomUser"

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "accounts:login"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# --- DATABASE ---
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# --- INTERNATIONALIZATION ---
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# --- STATIC FILES ---
STATIC_URL = "/static/"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]


# --- DEFAULT AUTO FIELD ---
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --- TAILWIND & THEME ---
TAILWIND_APP_NAME = "theme"
