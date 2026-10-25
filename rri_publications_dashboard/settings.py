"""
Django settings for rri_publications_dashboard project.
"""

import os
from pathlib import Path

from .env import (
    get_allowed_hosts,
    get_bool,
    get_int,
    get_secret_key,
    get_secure_proxy_ssl_header,
    load_env_file,
    validate_email_config,
)

# --- BASE DIRECTORIES ---
BASE_DIR = Path(__file__).resolve().parent.parent

# --- ENVIRONMENT CONFIGURATION ---
load_env_file(BASE_DIR / ".env")

# --- CORE SECURITY SETTINGS ---
DEBUG = get_bool("DEBUG", default=False)
SECRET_KEY = get_secret_key(debug=DEBUG)
ALLOWED_HOSTS = get_allowed_hosts(debug=DEBUG)

# HTTPS and Cookie Security
# In development (DEBUG=True), default to HTTP-friendly values.
# In production (DEBUG=False), secure cookies default to True unless overridden.
SESSION_COOKIE_SECURE = get_bool("SESSION_COOKIE_SECURE", default=not DEBUG)
CSRF_COOKIE_SECURE = get_bool("CSRF_COOKIE_SECURE", default=not DEBUG)
SECURE_SSL_REDIRECT = get_bool("SECURE_SSL_REDIRECT", default=False)
SECURE_HSTS_SECONDS = get_int("SECURE_HSTS_SECONDS", default=0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = get_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False)
SECURE_HSTS_PRELOAD = get_bool("SECURE_HSTS_PRELOAD", default=False)
SECURE_PROXY_SSL_HEADER = get_secure_proxy_ssl_header()

# --- FILE UPLOADS & RESOURCE LIMITS ---
# Maximum memory size (in bytes) before uploads stream to disk (default: 5 MB)
FILE_UPLOAD_MAX_MEMORY_SIZE = get_int("FILE_UPLOAD_MAX_MEMORY_SIZE", default=5 * 1024 * 1024)
# Maximum size (in bytes) of request body data accepted before RequestDataTooBig (default: 5 MB)
DATA_UPLOAD_MAX_MEMORY_SIZE = get_int("DATA_UPLOAD_MAX_MEMORY_SIZE", default=5 * 1024 * 1024)
# Maximum file size (in bytes) accepted for Web of Science exports (default: 5 MB)
MAX_WOS_FILE_SIZE = get_int("MAX_WOS_FILE_SIZE", default=5 * 1024 * 1024)
# Maximum publication records accepted per Web of Science upload batch (default: 500)
MAX_WOS_RECORDS = get_int("MAX_WOS_RECORDS", default=500)

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
            "builtins": [
                "accounts.templatetags.form_tags",
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


# --- EMAIL CONFIGURATION ---
# Default to console backend in development if unset; default to SMTP in production.
_default_email_backend = (
    "django.core.mail.backends.console.EmailBackend"
    if DEBUG
    else "django.core.mail.backends.smtp.EmailBackend"
)
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND") or _default_email_backend
EMAIL_HOST = os.environ.get("EMAIL_HOST")
EMAIL_PORT = get_int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = get_bool("EMAIL_USE_TLS", default=True)
EMAIL_USE_SSL = get_bool("EMAIL_USE_SSL", default=False)
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@rri.res.in")
SERVER_EMAIL = os.environ.get("SERVER_EMAIL", DEFAULT_FROM_EMAIL)

validate_email_config(
    debug=DEBUG,
    backend=EMAIL_BACKEND,
    host=EMAIL_HOST,
    port=EMAIL_PORT,
    use_tls=EMAIL_USE_TLS,
    use_ssl=EMAIL_USE_SSL,
)


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
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]


# --- DEFAULT AUTO FIELD ---
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --- TAILWIND & THEME ---
TAILWIND_APP_NAME = "theme"
