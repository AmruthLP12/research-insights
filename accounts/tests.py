from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase
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
