from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase
from django.urls import reverse
from accounts.permissions import RoleRequiredMixin, has_role, role_required

User = get_user_model()


class RolePermissionsTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.admin_user = User.objects.create_user(
            username="admin_user", password="password123", role="admin"
        )
        self.staff_user = User.objects.create_user(
            username="staff_user", password="password123", role="viewer", is_staff=True
        )
        self.superuser = User.objects.create_superuser(
            username="superuser", password="password123", role="viewer"
        )
        self.standard_user = User.objects.create_user(
            username="standard_user", password="password123", role="user"
        )
        self.viewer_user = User.objects.create_user(
            username="viewer_user", password="password123", role="viewer"
        )

    def test_has_role_helper(self):
        # Anonymous
        class Anonymous:
            is_authenticated = False

        self.assertFalse(has_role(Anonymous(), ["admin", "user"]))

        # Roles
        self.assertTrue(has_role(self.admin_user, ["admin"]))
        self.assertTrue(has_role(self.standard_user, ["admin", "user"]))
        self.assertFalse(has_role(self.viewer_user, ["admin", "user"]))

        # Staff and superuser overrides
        self.assertTrue(has_role(self.staff_user, ["admin"]))
        self.assertTrue(has_role(self.superuser, ["admin"]))

    def test_role_required_decorator(self):
        @role_required("admin", "user")
        def sample_view(request):
            return "OK"

        # Authenticated with permitted role
        req = self.factory.get("/")
        req.user = self.standard_user
        self.assertEqual(sample_view(req), "OK")

        # Authenticated with insufficient role
        req.user = self.viewer_user
        with self.assertRaises(PermissionDenied):
            sample_view(req)

        # Anonymous user redirects to login
        req.user = self.factory.get("/").user if hasattr(self.factory.get("/"), "user") else None
        from django.contrib.auth.models import AnonymousUser
        req.user = AnonymousUser()
        resp = sample_view(req)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp.url)


class FormTagsFilterTestCase(TestCase):
    def test_add_class_filter(self):
        from accounts.templatetags.form_tags import add_class
        from django import forms

        class SampleForm(forms.Form):
            name = forms.CharField(widget=forms.TextInput(attrs={"class": "initial-class"}))
            email = forms.EmailField()

        form = SampleForm()
        # Field with existing class
        rendered_name = str(add_class(form["name"], "extra-class"))
        self.assertIn('class="initial-class extra-class"', rendered_name)

        # Field without existing class
        rendered_email = str(add_class(form["email"], "new-class"))
        self.assertIn('class="new-class"', rendered_email)

        # Non-field object fallback
        self.assertEqual(add_class("raw_string", "some-class"), "raw_string")


class PasswordResetWorkflowTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="researcher",
            email="researcher@rri.res.in",
            password="password123",
            role="user",
        )

    def test_password_reset_get_renders_form(self):
        # Verify GET does not raise TemplateSyntaxError (e.g. from add_class filter)
        response = self.client.get(reverse("accounts:password_reset"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="email"')
        self.assertContains(response, 'type="email"')

    def test_password_reset_post_existing_user_sends_email(self):
        response = self.client.post(
            reverse("accounts:password_reset"),
            {"email": "researcher@rri.res.in"},
        )
        self.assertRedirects(response, reverse("accounts:password_reset_done"))

        # Verify email was dispatched
        from django.core import mail
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ["researcher@rri.res.in"])
        self.assertIn("Password reset", email.subject)

    def test_password_reset_post_nonexistent_email_does_not_leak_or_send(self):
        response = self.client.post(
            reverse("accounts:password_reset"),
            {"email": "nonexistent@unknown.com"},
        )
        # Consistent redirect prevents user enumeration
        self.assertRedirects(response, reverse("accounts:password_reset_done"))

        from django.core import mail
        self.assertEqual(len(mail.outbox), 0)


class EmailAndSecurityConfigTestCase(TestCase):
    def test_validate_email_config_rejects_tls_and_ssl_simultaneously(self):
        from django.core.exceptions import ImproperlyConfigured
        from rri_publications_dashboard.env import validate_email_config

        with self.assertRaises(ImproperlyConfigured):
            validate_email_config(
                debug=False,
                backend="django.core.mail.backends.smtp.EmailBackend",
                host="smtp.example.com",
                port=587,
                use_tls=True,
                use_ssl=True,
            )

    def test_validate_email_config_rejects_missing_host_in_production(self):
        from django.core.exceptions import ImproperlyConfigured
        from rri_publications_dashboard.env import validate_email_config

        with self.assertRaises(ImproperlyConfigured):
            validate_email_config(
                debug=False,
                backend="django.core.mail.backends.smtp.EmailBackend",
                host="",
                port=587,
                use_tls=True,
                use_ssl=False,
            )

    def test_validate_email_config_permits_valid_prod_and_dev_settings(self):
        from rri_publications_dashboard.env import validate_email_config

        # Valid production
        validate_email_config(
            debug=False,
            backend="django.core.mail.backends.smtp.EmailBackend",
            host="smtp.rri.res.in",
            port=587,
            use_tls=True,
            use_ssl=False,
        )

        # Valid dev with console backend
        validate_email_config(
            debug=True,
            backend="django.core.mail.backends.console.EmailBackend",
            host="",
            port=1025,
            use_tls=False,
            use_ssl=False,
        )

    def test_get_secure_proxy_ssl_header_parsing(self):
        import os
        from unittest.mock import patch
        from rri_publications_dashboard.env import get_secure_proxy_ssl_header

        with patch.dict(os.environ, {"USE_X_FORWARDED_PROTO": "True"}):
            self.assertEqual(
                get_secure_proxy_ssl_header(),
                ("HTTP_X_FORWARDED_PROTO", "https"),
            )

        with patch.dict(os.environ, {"USE_X_FORWARDED_PROTO": "False"}):
            self.assertIsNone(get_secure_proxy_ssl_header())
