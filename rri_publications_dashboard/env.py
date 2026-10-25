"""
Environment configuration helpers for the RRI Publications Dashboard.

Provides robust, fail-closed loading and parsing of environment variables
for Django settings without third-party dependencies.
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

# Stable fallback key used ONLY in development (DEBUG=True) when no secret key
# is configured in the environment. Using a fixed dev fallback avoids generating
# a new random key per process start, which would invalidate active sessions and
# CSRF tokens across local reloads.
DEV_SECRET_KEY_FALLBACK = "django-insecure-development-only-fallback-key-do-not-use-in-production"

# Accepted boolean string representations
TRUE_STRINGS = frozenset(("true", "1", "yes", "t", "on"))
FALSE_STRINGS = frozenset(("false", "0", "no", "f", "off"))


def load_env_file(env_path: Path) -> None:
    """Load key-value pairs from a .env file into os.environ.

    Existing process environment variables take precedence and are not overwritten.
    """
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


def parse_bool(name: str, value: str | None, default: bool = False) -> bool:
    """Strict boolean parser for an environment variable value.

    Returns default if value is None or empty.
    Raises ImproperlyConfigured for invalid or unrecognized boolean strings.
    """
    if value is None or str(value).strip() == "":
        return default

    normalized = str(value).strip().lower()
    if normalized in TRUE_STRINGS:
        return True
    if normalized in FALSE_STRINGS:
        return False

    raise ImproperlyConfigured(
        f"Invalid boolean value for environment variable '{name}': '{value}'. "
        f"Allowed values are 'true', 'false', '1', '0', 'yes', 'no', 't', 'f', 'on', 'off'."
    )


def get_bool(name: str, default: bool = False) -> bool:
    """Retrieve an environment variable and parse it as a strict boolean."""
    return parse_bool(name, os.environ.get(name), default=default)


def get_int(name: str, default: int = 0) -> int:
    """Retrieve an environment variable and parse it as an integer."""
    raw = os.environ.get(name)
    if raw is None or str(raw).strip() == "":
        return default
    try:
        return int(str(raw).strip())
    except ValueError:
        raise ImproperlyConfigured(
            f"Invalid integer value for environment variable '{name}': '{raw}'"
        )


def parse_list(value: str | None) -> list[str]:
    """Parse a comma-separated string into a trimmed, non-empty list of strings."""
    if not value:
        return []
    return [item.strip() for item in str(value).split(",") if item.strip()]


def get_list(name: str, default: list[str] | None = None) -> list[str]:
    """Retrieve a comma-separated environment variable as a list of strings."""
    raw = os.environ.get(name)
    if raw is None:
        return default if default is not None else []
    return parse_list(raw)


def get_secret_key(debug: bool = False) -> str:
    """Resolve and validate the Django SECRET_KEY.

    DJANGO_SECRET_KEY is canonical. SECRET_KEY is checked for backward compatibility
    with existing deployment environments.

    In production (DEBUG=False):
        - Fails closed if the secret is missing, under 50 characters, or starts
          with 'django-insecure-'.

    In development (DEBUG=True):
        - Falls back to a stable, fixed development key if unset.
    """
    key = os.environ.get("DJANGO_SECRET_KEY") or os.environ.get("SECRET_KEY")

    if not key:
        if debug:
            return DEV_SECRET_KEY_FALLBACK
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY environment variable is required when DEBUG is False."
        )

    if not debug:
        if key.startswith("django-insecure-") or len(key) < 50:
            raise ImproperlyConfigured(
                "Insecure DJANGO_SECRET_KEY detected in production. "
                "A secure, random key of at least 50 characters is required."
            )

    return key


def get_allowed_hosts(debug: bool = False) -> list[str]:
    """Resolve and validate ALLOWED_HOSTS.

    In production (DEBUG=False):
        - Fails closed if ALLOWED_HOSTS is empty or contains wildcard '*'.

    In development (DEBUG=True):
        - Defaults to localhost/loopback hosts and merges them with any configured hosts.
    """
    raw_hosts = os.environ.get("ALLOWED_HOSTS", "")
    parsed_hosts = parse_list(raw_hosts)

    if debug:
        dev_hosts = ["localhost", "127.0.0.1", "[::1]", "testserver"]
        if parsed_hosts:
            return list(dict.fromkeys(parsed_hosts + dev_hosts))
        return dev_hosts

    if not parsed_hosts:
        raise ImproperlyConfigured(
            "ALLOWED_HOSTS environment variable is required and cannot be empty when DEBUG is False."
        )

    if "*" in parsed_hosts:
        raise ImproperlyConfigured(
            "Wildcard '*' in ALLOWED_HOSTS is not permitted in production (when DEBUG is False)."
        )

    return parsed_hosts


def validate_email_config(
    debug: bool,
    backend: str,
    host: str | None,
    port: int,
    use_tls: bool,
    use_ssl: bool,
) -> None:
    """Validate email configuration parameters for conflicts and required values."""
    if use_tls and use_ssl:
        raise ImproperlyConfigured(
            "EMAIL_USE_TLS and EMAIL_USE_SSL are mutually exclusive. Set only one to True."
        )

    if not (1 <= port <= 65535):
        raise ImproperlyConfigured(
            f"Invalid EMAIL_PORT: '{port}'. Port must be between 1 and 65535."
        )

    if not debug and "smtp" in backend.lower():
        if not host:
            raise ImproperlyConfigured(
                "EMAIL_HOST environment variable is required in production when using the SMTP backend."
            )


def get_secure_proxy_ssl_header() -> tuple[str, str] | None:
    """Return SECURE_PROXY_SSL_HEADER if USE_X_FORWARDED_PROTO is True, else None."""
    if get_bool("USE_X_FORWARDED_PROTO", default=False):
        return ("HTTP_X_FORWARDED_PROTO", "https")
    return None
