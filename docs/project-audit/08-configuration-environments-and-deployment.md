# Configuration, Environments, and Deployment: RRI Publications Dashboard

## 1. Environment Configuration and Settings Architecture

The application currently utilizes a single, monolithic settings module located at [`rri_publications_dashboard/settings.py`](../../rri_publications_dashboard/settings.py). 

### 1.1 The Settings-to-Environment Disconnect

```
.env / .env.example                                      settings.py
+------------------------------------+                   +------------------------------------+
| PORT=9000                          |                   | SECRET_KEY = 'django-insecure-...' |
| DOMAIN=example.com                 |        X          | DEBUG = True                       |
| DEBUG=True                         |  (Not Loaded)     | ALLOWED_HOSTS = ['*']              |
| DJANGO_SECRET_KEY=...              |                   | DATABASES = { 'ENGINE': 'sqlite3' }|
| ALLOWED_HOSTS=localhost,...        |                   | STATIC_ROOT: <MISSING>             |
+------------------------------------+                   +------------------------------------+
```

- **Discrepancy**: A detailed [`.env.example`](../../.env.example) and local [`.env`](../../.env) exist at the repository root, and [`makefile:6-10`](../../makefile#L6-L10) exports these variables for Make commands.
- **Root Problem**: [`rri_publications_dashboard/settings.py`](../../rri_publications_dashboard/settings.py) does **not** import `os.environ`, `python-dotenv`, or `django-environ`. All core parameters (`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`) are hardcoded directly in Python source code.
- **Consequence**: Changing values in `.env` (such as setting `DEBUG=False` or updating `ALLOWED_HOSTS`) has zero effect on the running Django application.

---

## 2. Environment Variable Inventory

Based on [`.env.example`](../../.env.example) and [`makefile`](../../makefile):

| Variable Name | Declared Example Value | Intended Purpose | Actually Ingested by `settings.py`? | Recommended Production Configuration |
| :--- | :--- | :--- | :--- | :--- |
| `PORT` | `9000` | Port for the development or application server | No (Used only by `makefile:51`) | Ingest via environment for container/Gunicorn binding |
| `DOMAIN` | `example.com` | Target server domain for Apache configuration | No (Used only by `makefile:144`) | Use to construct `ALLOWED_HOSTS` and CSRF trusted origins |
| `HOST` | `0.0.0.0` | Network binding interface for `runserver` | No (Used only by `makefile:51`) | Standard host bind interface |
| `VENV` | `venv` | Virtual environment directory name | No (Used only by `makefile:18`) | Path to Python virtualenv |
| `SITE_NAME` | `pub` | Apache configuration site prefix | No (Used only by `makefile:155`) | Site configuration descriptor |
| `DEBUG` | `True` | Django debug mode flag | **No** (Hardcoded `True` in `settings.py:14`) | Must parse boolean from environment (`False` in prod) |
| `APP_ENV` | `Development` | Environment tier descriptor | No (Unused) | Informational environment tag |
| `APP_VERSION` | `1.0.0` | Semantic application release version | No (Unused) | Sentry / release tracking |
| `BUILD_DATE` | `30-01-2026` | Build timestamp | No (Unused) | Build artifact tracking |
| `SITE_FULL_URL` | `http://127.0.0.1:${PORT}` | Fully qualified domain URL | No (Unused) | Required for absolute links in emails |
| `DJANGO_SECRET_KEY` | `django-insecure-secret-key` | Cryptographic signing secret | **No** (Hardcoded in `settings.py:13`) | Must load securely from secret store / environment |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1,[::1],example.com` | Permitted HTTP Host headers | **No** (Hardcoded `['*']` in `settings.py:15`)| Parse comma-delimited string from environment |

---

## 3. Static and Media File Configuration

### 3.1 Static Files

Configured in [`rri_publications_dashboard/settings.py:104-110`](../../rri_publications_dashboard/settings.py#L104-L110):
```python
STATIC_URL = "/static/"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
```

- **The Missing `STATIC_ROOT` Problem**:
  - `STATIC_ROOT` is **not defined** anywhere in `settings.py`.
  - When executing `make collectstatic` or `python manage.py collectstatic --noinput`, Django halts with a fatal configuration exception:
    ```
    django.core.exceptions.ImproperlyConfigured: You're using the staticfiles app without having set the STATIC_ROOT setting to a filesystem path.
    ```
  - **Required Fix**: Add `STATIC_ROOT = BASE_DIR / "staticfiles"` to `settings.py`.

### 3.2 Media Files
- **Status**: Completely unconfigured. `MEDIA_URL` and `MEDIA_ROOT` are absent from `settings.py`.
- **Current Impact**: Web of Science file uploads in `wos_upload` are processed directly from in-memory buffers (`request.FILES["wos_file"]`) and are never written to permanent media storage. However, if future features require persistent document or PDF attachments, media configuration will be required.

---

## 4. Application Servers and Process Management

### 4.1 Development Server Execution
The project provides several GNU Make automation recipes:
- `make run`: Executes `python manage.py runserver 0.0.0.0:9000`.
- `make tailwind`: Executes `python manage.py tailwind start` (runs PostCSS watcher).
- `make dev-all`: Spawns the Tailwind watcher in the background and runs the Django development server synchronously ([`makefile:117-121`](../../makefile#L117-L121)).

### 4.2 Production Server Execution (WSGI / ASGI)
- **WSGI Entry Point**: [`rri_publications_dashboard/wsgi.py:16`](../../rri_publications_dashboard/wsgi.py#L16) exposes standard `application = get_wsgi_application()`. Compatible with Gunicorn, uWSGI, and Apache `mod_wsgi`.
- **ASGI Entry Point**: [`rri_publications_dashboard/asgi.py:16`](../../rri_publications_dashboard/asgi.py#L16) exposes `application = get_asgi_application()`. Compatible with Uvicorn or Daphne, though no asynchronous consumers or WebSockets are currently implemented.

---

## 5. Deployment Procedures and Pipeline Verification

### 5.1 The Broken Apache Deployment Pipeline

The repository provides a deployment target in [`makefile:142-160`](../../makefile#L142-L160):

```makefile
conf:
	@DOMAIN=$(DOMAIN) SERVER_ALIAS=$(SERVER_ALIAS) ADMIN_EMAIL=$(ADMIN_EMAIL) \
	PORT=$(PORT) VENV_PATH=$(VENV_PATH) $(PY) generate_apache_conf.py

deploy-server: tailwind-build collectstatic conf ensure_port
	@sudo rsync -av $(SITE_NAME)_core_$(PORT).conf /etc/apache2/sites-available/
	@sudo a2ensite $(SITE_NAME)_core_$(PORT).conf
	@sudo systemctl restart apache2
```

#### Defect Analysis:
1. `generate_apache_conf.py` **does not exist** in the repository root. Running `make conf` fails with `[Errno 2] No such file or directory`.
2. `collectstatic` fails due to missing `STATIC_ROOT`.
3. Consequently, `make deploy-server` is entirely inoperable in the repository's current state.

### 5.2 Scheduled Tasks and Cron Jobs

The Makefile defines cron management recipes:
```makefile
cron_add:
	$(PY) manage.py crontab add
cron_remove:
	$(PY) manage.py crontab remove
cron_show:
	$(PY) manage.py crontab show
```
- **Defect Analysis**: `django-crontab` is neither declared in `requirements.txt` nor registered in `INSTALLED_APPS`. Invoking any cron make target raises `django.core.management.base.CommandError: Unknown command: 'crontab'`.

---

## 6. Logging and Observability

- **Current Logging Configuration**: The project has zero custom `LOGGING` dictionary defined in `settings.py`.
- **Behavior**: Django falls back to default console logging:
  - When `DEBUG=True`, exceptions emit HTML tracebacks to the browser and log to standard output.
  - When `DEBUG=False`, unhandled 500 errors fail silently or attempt to send an email to `ADMINS` (which will fail due to the unconfigured SMTP server).
- **Recommendation**: Implement a structured JSON or rotating file logger writing to `/var/log/rri_dashboard/django.log` with distinct handlers for security, database queries, and upload errors.

