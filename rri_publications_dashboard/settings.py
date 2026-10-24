"""
Django settings for rri_publications_dashboard project.
"""

import os
from pathlib import Path

from .env import get_allowed_hosts, get_bool, get_secret_key, load_env_file

# --- BASE DIRECTORIES ---
BASE_DIR = Path(__file__).resolve().parent.parent

# --- ENVIRONMENT CONFIGURATION ---
load_env_file(BASE_DIR / ".env")

# --- CORE SECURITY SETTINGS ---
DEBUG = get_bool("DEBUG", default=False)
SECRET_KEY = get_secret_key(debug=DEBUG)
ALLOWED_HOSTS = get_allowed_hosts(debug=DEBUG)

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
