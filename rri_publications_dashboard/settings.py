"""
Django settings for rri_publications_dashboard project.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

from django.core.exceptions import ImproperlyConfigured

# --- ENVIRONMENT CONFIGURATION ---
# Load variables from .env file if present (without overwriting pre-existing process environment)
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.is_file():
    with open(ENV_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip().strip("'\"")
                os.environ.setdefault(key, val)


def _parse_bool(value, default=False):
    """Explicit boolean parser: true/1/yes/t/on -> True, false/0/no/f/off -> False."""
    if value is None:
        return default
    val = str(value).strip().lower()
    if val in ("true", "1", "yes", "t", "y", "on"):
        return True
    if val in ("false", "0", "no", "f", "n", "off", ""):
        return False
    return default


def _parse_list(value):
    """Parse comma-separated string into a trimmed, non-empty list of strings."""
    if not value:
        return []
    return [item.strip() for item in str(value).split(",") if item.strip()]


# --- BASIC SECURITY SETTINGS ---
DEBUG = _parse_bool(os.environ.get("DEBUG"), default=False)

# SECRET_KEY resolution and fail-closed validation
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or os.environ.get("SECRET_KEY")

if not SECRET_KEY:
    if DEBUG:
        # For local development convenience: ephemeral key generated per process if unset
        import secrets
        SECRET_KEY = f"django-insecure-dev-{secrets.token_urlsafe(50)}"
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
        # In dev: combine configured hosts with dev defaults (avoiding duplicates)
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

# --- APPLICATIONS ---
INSTALLED_APPS = [
    # Django core apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    "tailwind",
    "theme",

    # Your custom apps
    'accounts',
    'publications',
    "django_filters",
    'dashboard',

]


if DEBUG:
    # Add django_browser_reload only in DEBUG mode
    INSTALLED_APPS += ["django_browser_reload"]

AUTH_USER_MODEL = 'accounts.CustomUser'


LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'dashboard:home'
LOGOUT_REDIRECT_URL = 'accounts:login'

# --- MIDDLEWARE ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if DEBUG:
    # Add django_browser_reload middleware only in DEBUG mode
    MIDDLEWARE += [
        "django_browser_reload.middleware.BrowserReloadMiddleware",
    ]

ROOT_URLCONF = 'rri_publications_dashboard.urls'

# --- TEMPLATES ---
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'dashboard.context_processors.dashboard_sidebar',
            ],
        },
    },
]

WSGI_APPLICATION = 'rri_publications_dashboard.wsgi.application'

# --- DATABASE ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# --- PASSWORD VALIDATION ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- INTERNATIONALIZATION ---
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# --- STATIC FILES ---
STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR  / "static",
]

# --- DEFAULT AUTO FIELD ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

TAILWIND_APP_NAME = 'theme'


