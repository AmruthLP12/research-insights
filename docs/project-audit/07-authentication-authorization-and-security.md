# Authentication, Authorization, and Security Review: RRI Publications Dashboard

## 1. Security Architecture and Defense-in-Depth Assessment

This defensive security audit evaluates the RRI Publications Dashboard against Django security standards and the OWASP Top 10 framework. The review examines source code, settings modules, URL routing, middleware configurations, and data persistence patterns.

```
+-----------------------------------------------------------------------------------+
|                             External Network Boundary                             |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|  1. Gateway & Settings:                                                           |
|     - SECRET_KEY: Hardcoded insecure key in settings.py                 [HIGH RISK]|
|     - DEBUG: Hardcoded True in settings.py                              [HIGH RISK]|
|     - ALLOWED_HOSTS: Wildcard '*' permits arbitrary Host headers        [HIGH RISK]|
|     - SSL / HSTS / Secure Cookies: Disabled                            [LOW RISK] |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|  2. Middleware Layer:                                                             |
|     - SecurityMiddleware: Present                                       [PASS]    |
|     - SessionMiddleware: Session cookies active (HttpOnly)              [PASS]    |
|     - CsrfViewMiddleware: Enforced on POST requests                     [PASS]    |
|     - XFrameOptionsMiddleware: Denies framing (SAMEORIGIN)              [PASS]    |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|  3. Authentication & Authorization:                                               |
|     - Dashboard Views (21 CBVs): Zero authentication required        [MEDIUM RISK]|
|     - Role Enforcement: CustomUser.role completely unenforced        [MEDIUM RISK]|
|     - WoS File Ingestion: Upload, review, save protected by login       [PASS]    |
|     - WoS Completion Screen: Missing @login_required                     [LOW RISK]|
|     - Password Reset: Unconfigured SMTP causes 500 error                 [LOW RISK]|
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|  4. Data Layer & Application Logic:                                               |
|     - File Ingestion: Unbounded upload size & session bloat           [MEDIUM RISK]|
|     - SQL Injection: 0 raw SQL queries; 100% parameterized ORM          [PASS]    |
|     - XSS Defense: Django auto-escaping & safe json_script tag          [PASS]    |
|     - Object Deletion: User deletion cascades to all publications    [MEDIUM RISK]|
+-----------------------------------------------------------------------------------+
```

---

## 2. Authentication and Account Lifecycle

1. **User Identity Model**:
   - Implemented via `CustomUser` ([`accounts/models.py:7-17`](../../accounts/models.py#L7-L17)) inheriting from `django.contrib.auth.models.AbstractUser`.
   - Utilizes Django's default PBKDF2 with SHA-256 password hashing.
   - Password strength validation is enforced via standard Django validators (`MinimumLengthValidator`, `CommonPasswordValidator`, `NumericPasswordValidator`, `UserAttributeSimilarityValidator`) in [`settings.py:89-94`](../../rri_publications_dashboard/settings.py#L89-L94).
2. **Session Handling & "Remember Me"**:
   - [`CustomLoginView`](../../accounts/views.py#L6-L18) inspects `remember_me` checkbox from [`CustomAuthenticationForm`](../../accounts/forms.py#L11).
   - If `remember_me` is unchecked, `request.session.set_expiry(0)` forces the session cookie to expire immediately upon browser termination.
   - If checked, the session persists for the default duration (`SESSION_COOKIE_AGE = 1209600` seconds / 2 weeks).
3. **Password Reset Subsystem**:
   - URL routes are declared in [`accounts/urls.py:14-20`](../../accounts/urls.py#L14-L20) utilizing standard Django auth views.
   - **Vulnerability / Operational Failure**: The project specifies no `EMAIL_BACKEND` or SMTP configuration in `settings.py`. Triggering a password reset attempts a connection to `localhost:25`, immediately raising a `ConnectionRefusedError` and returning a 500 server error to the user.

---

## 3. Authorization and Role-Based Access Control (RBAC)

1. **Role Definition vs Enforcement Disconnect**:
   - `CustomUser` declares three discrete institutional roles:
     ```python
     ROLE_CHOICES = (
         ("admin", "Admin"),
         ("user", "User"),
         ("viewer", "Viewer"),
     )
     role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="viewer")
     ```
   - **Critical Architectural Finding**: Across the entire repository, **not a single view, template tag, or service inspects `request.user.role`**. There are zero custom permission classes, zero role mixins, and zero role checks in templates.
   - Any authenticated user with role `"viewer"` can access `/publications/wos/upload/`, review staged records, and commit modifications to the database via `wos_save`.
2. **Public Exposure of Analytical Dashboards**:
   - All 21 views in `dashboard/views.py` inherit directly from `TemplateView`.
   - None implement `LoginRequiredMixin` or permission checks.
   - The entire bibliometric archive—including institutional collaboration data, unpublished manuscript records, department rankings, and author metrics—is accessible to unauthenticated public Internet visitors.

---

## 4. Web Application Security Analysis

1. **Cross-Site Request Forgery (CSRF)**:
   - `CsrfViewMiddleware` is enabled in [`settings.py:53`](../../rri_publications_dashboard/settings.py#L53).
   - All browser-based forms (`login.html`, `upload.html`, `review.html`, `sidebar.html` logout) properly include `{% csrf_token %}`.
   - Cookie security: `CSRF_COOKIE_SECURE` is `False` in development, allowing transmission over cleartext HTTP.
2. **Cross-Site Scripting (XSS)**:
   - Django's template engine enforces HTML auto-escaping by default.
   - JavaScript data hydration uses Django's secure `json_script` template tag (e.g. `{{ document_counts|json_script:"document-counts" }}` in [`dashboard.html:92`](../../dashboard/templates/dashboard/dashboard.html#L92)), safely escaping characters into JSON-encoded `<script type="application/json">` blocks before parsing via `JSON.parse()`.
   - The custom template filter `json_loads` ([`publications/templatetags/json_extras.py:8`](../../publications/templatetags/json_extras.py#L8)) deserializes JSON into native Python objects; it does not emit unescaped raw HTML.
3. **SQL Injection**:
   - Codebase search confirms zero occurrences of `raw()`, `extra()`, or direct `connection.cursor()` executions.
   - 100% of database interactions utilize Django's parameterized ORM querysets and `django-filter` lookups.
4. **File Upload Security & DoS Vulnerability**:
   - In [`publications/views.py:201-218`](../../publications/views.py#L201-L218), `wos_upload` reads the uploaded file directly into memory without checking `request.FILES["wos_file"].size`.
   - The file content is decoded in memory and parsed into dictionaries, which are stored directly into `request.session["wos_records"]`.
   - Because Django sessions are backed by the database table `django_session`, a 20MB file upload will result in an enormous serialized base64 string written to SQLite, potentially degrading database I/O or exhausting database storage limits.

---

## 5. Security Findings Register

| ID | Title | Severity | Confidence | Affected File & Lines | Potential Impact | Realistic Attack Scenario | Recommended Mitigation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **SEC-01** | Hardcoded Insecure `SECRET_KEY` | **High** | Confirmed | [`settings.py:13`](../../rri_publications_dashboard/settings.py#L13) | Session forgery, CSRF token forgery, password reset token tampering | Attacker inspects public repo, extracts `SECRET_KEY`, and crafts forged signed session cookies to gain admin privileges. | Load `SECRET_KEY` from environment via `os.environ.get()` or `django-environ`. Refuse to boot if unset in production. |
| **SEC-02** | Hardcoded `DEBUG = True` and Wildcard `ALLOWED_HOSTS` | **High** | Confirmed | [`settings.py:14-15`](../../rri_publications_dashboard/settings.py#L14-L15) | Sensitive tracebacks, environment exposure, cache poisoning | An error triggered in production exposes full source code, local variables, and system paths. Host header poisoning redirects password reset emails. | Read `DEBUG` and `ALLOWED_HOSTS` from `.env`. Enforce strict host matching when `DEBUG=False`. |
| **SEC-03** | Missing Authentication on All Dashboard Views | **Medium** | Confirmed | [`dashboard/views.py:17-2112`](../../dashboard/views.py#L17-L2112) | Unauthorized access to internal research metrics | Unauthenticated crawler or competitor scrapes proprietary institutional productivity figures, grant collaborations, and scholar rosters. | Apply `LoginRequiredMixin` to base dashboard views or implement explicit public/private view toggles. |
| **SEC-04** | Role-Based Access Control Completely Unenforced | **Medium** | Confirmed | [`accounts/models.py:13`](../../accounts/models.py#L13), [`publications/views.py:200, 302`](../../publications/views.py#L200) | Privilege escalation / unauthorized data entry | A user provisioned with the `"viewer"` role accesses `/publications/wos/upload/` and modifies institutional publication records. | Create a `UserPassesTestMixin` or `role_required("admin")` decorator protecting WoS upload and edit endpoints. |
| **SEC-05** | Unbounded WoS File Upload and Session Bloat | **Medium** | Confirmed | [`publications/views.py:201-218`](../../publications/views.py#L201-L218) | Server memory exhaustion, database session table bloat, Denial of Service | Attacker uploads a 200MB text file; Django parses it into memory and writes a massive payload to `django_session`, locking SQLite. | Enforce file size limit (`DATA_UPLOAD_MAX_MEMORY_SIZE` / manual 5MB check); validate `.txt` extension; store staged records in temporary DB tables rather than session. |
| **SEC-06** | Dangerous Cascade Deletion on Publication Creator | **Medium** | Confirmed | [`publications/models.py:182-185`](../../publications/models.py#L182-L185) | Permanent catastrophic data loss of institutional publications | Institutional admin deletes a departed library staff member account; SQLite cascades and deletes all publications uploaded by that user. | Change foreign key constraint to `on_delete=models.PROTECT` or `models.SET_NULL, null=True`. |
| **SEC-07** | Insecure Session & CSRF Cookie Flags | **Low** | Confirmed | [`settings.py:48-64`](../../rri_publications_dashboard/settings.py#L48-L64) | Session interception via network sniffing (MitM) | Session cookies transmitted over cleartext HTTP can be intercepted on local university Wi-Fi networks. | Set `SESSION_COOKIE_SECURE = True`, `CSRF_COOKIE_SECURE = True`, and `SECURE_SSL_REDIRECT = True` for production. |
| **SEC-08** | Unconfigured Email Backend | **Low** | Confirmed | [`settings.py:1-122`](../../rri_publications_dashboard/settings.py#L1-L122) | Application 500 error on user password reset requests | User attempts to reset forgotten password; Django attempts connection to localhost:25, crashes, and exposes error page. | Configure `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'` for dev, or SMTP credentials via `.env`. |
| **SEC-09** | Missing Authentication on WoS Success Page | **Informational** | Confirmed | [`publications/views.py:365`](../../publications/views.py#L365) | Information disclosure of staging completion state | Anonymous visitor navigating to `/publications/wos/success/` views completion screen intended for library officers. | Add `@login_required` decorator to `wos_success`. |

