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


class AuthenticationWorkflowTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="active_user",
            password="correct_password_123",
            role="user",
        )
        self.inactive_user = User.objects.create_user(
            username="inactive_user",
            password="password123",
            role="user",
            is_active=False,
        )

    def test_login_page_renders_form(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="username"')
        self.assertContains(response, 'name="password"')

    def test_login_successful_with_valid_credentials(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "active_user", "password": "correct_password_123"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.id)

    def test_login_with_remember_me_unchecked_sets_zero_expiry(self):
        self.client.post(
            reverse("accounts:login"),
            {
                "username": "active_user",
                "password": "correct_password_123",
                "remember_me": False,
            },
        )
        # When remember_me is unchecked, session expiry is set to expire on browser close
        self.assertTrue(self.client.session.get_expire_at_browser_close())

    def test_login_failed_with_invalid_credentials(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "active_user", "password": "wrong_password"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertContains(response, "Please enter a correct")

    def test_login_inactive_user_fails(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "inactive_user", "password": "password123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_authenticated_user_accessing_login_redirects(self):
        self.client.login(username="active_user", password="correct_password_123")
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 302)

    def test_logout_view(self):
        self.client.login(username="active_user", password="correct_password_123")
        self.assertIn("_auth_user_id", self.client.session)

        response = self.client.post(reverse("accounts:logout"))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("_auth_user_id", self.client.session)


class PasswordResetConfirmAndCompleteTestCase(TestCase):
    def setUp(self):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        self.user = User.objects.create_user(
            username="reset_user",
            email="reset@rri.res.in",
            password="initial_password_123",
            role="user",
        )
        self.token = default_token_generator.make_token(self.user)
        self.uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))

    def test_password_reset_confirm_valid_token_renders_form(self):
        response = self.client.get(
            reverse(
                "accounts:password_reset_confirm",
                kwargs={"uidb64": self.uidb64, "token": self.token},
            ),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context.get("validlink"))
        self.assertContains(response, 'name="new_password1"')

    def test_password_reset_confirm_successful_submission(self):
        # Initial GET to initialize session token and follow redirect to set-password
        self.client.get(
            reverse(
                "accounts:password_reset_confirm",
                kwargs={"uidb64": self.uidb64, "token": self.token},
            )
        )

        response = self.client.post(
            reverse(
                "accounts:password_reset_confirm",
                kwargs={"uidb64": self.uidb64, "token": "set-password"},
            ),
            {
                "new_password1": "brand_new_secret_password_456!",
                "new_password2": "brand_new_secret_password_456!",
            },
        )
        self.assertRedirects(response, reverse("accounts:password_reset_complete"))

        # Confirm password updated by logging in
        login_success = self.client.login(
            username="reset_user", password="brand_new_secret_password_456!"
        )
        self.assertTrue(login_success)

    def test_password_reset_confirm_invalid_token(self):
        response = self.client.get(
            reverse(
                "accounts:password_reset_confirm",
                kwargs={"uidb64": self.uidb64, "token": "invalid-tampered-token"},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context.get("validlink"))
        self.assertContains(response, "invalid or has expired")

    def test_password_reset_token_cannot_be_reused(self):
        from django.contrib.auth.tokens import default_token_generator

        # Initial GET and POST to consume the token
        self.client.get(
            reverse(
                "accounts:password_reset_confirm",
                kwargs={"uidb64": self.uidb64, "token": self.token},
            )
        )
        self.client.post(
            reverse(
                "accounts:password_reset_confirm",
                kwargs={"uidb64": self.uidb64, "token": "set-password"},
            ),
            {
                "new_password1": "brand_new_secret_password_456!",
                "new_password2": "brand_new_secret_password_456!",
            },
        )

        # Attempting to use the old token again fails
        self.user.refresh_from_db()
        self.assertFalse(default_token_generator.check_token(self.user, self.token))

        response = self.client.get(
            reverse(
                "accounts:password_reset_confirm",
                kwargs={"uidb64": self.uidb64, "token": self.token},
            ),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context.get("validlink"))


class PasswordChangeWorkflowTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="change_user",
            password="old_password_123",
            role="user",
        )

    def test_password_change_requires_authentication(self):
        response = self.client.get(reverse("accounts:password_change"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_password_change_renders_form(self):
        self.client.login(username="change_user", password="old_password_123")
        response = self.client.get(reverse("accounts:password_change"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="old_password"')
        self.assertContains(response, 'name="new_password1"')

    def test_password_change_successful(self):
        self.client.login(username="change_user", password="old_password_123")
        response = self.client.post(
            reverse("accounts:password_change"),
            {
                "old_password": "old_password_123",
                "new_password1": "updated_password_789!",
                "new_password2": "updated_password_789!",
            },
        )
        self.assertRedirects(response, reverse("accounts:password_change_done"))

        # Follow redirect and verify password_change_done template renders without error
        done_resp = self.client.get(reverse("accounts:password_change_done"))
        self.assertEqual(done_resp.status_code, 200)
        self.assertContains(done_resp, "Password Updated")

        # Verify new password works
        self.client.logout()
        login_success = self.client.login(
            username="change_user", password="updated_password_789!"
        )
        self.assertTrue(login_success)

    def test_password_change_invalid_old_password(self):
        self.client.login(username="change_user", password="old_password_123")
        response = self.client.post(
            reverse("accounts:password_change"),
            {
                "old_password": "wrong_password",
                "new_password1": "updated_password_789!",
                "new_password2": "updated_password_789!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your old password was entered incorrectly.")
