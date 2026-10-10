import os
import subprocess
import sys

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse


class HomePageTests(TestCase):
    def test_home_renders(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dulce y Salado")


class SettingsTests(SimpleTestCase):
    def test_secret_key_is_required(self):
        for value in (None, "", "   "):
            with self.subTest(value=value):
                environment = os.environ.copy()
                environment.pop("DJANGO_SECRET_KEY", None)
                if value is not None:
                    environment["DJANGO_SECRET_KEY"] = value
                result = subprocess.run(
                    [sys.executable, "manage.py", "check"],
                    env=environment, capture_output=True, text=True, check=False,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Configurá DJANGO_SECRET_KEY", result.stderr)


class AdminAccessTests(TestCase):
    def test_anonymous_redirects_to_login(self):
        response = self.client.get(reverse("admin:index"))
        self.assertRedirects(response, "/admin/login/?next=/admin/")

    def test_non_staff_and_inactive_staff_cannot_access(self):
        for staff, active in ((False, True), (True, False)):
            user = get_user_model().objects.create_user(
                username=f"user-{staff}-{active}", is_staff=staff, is_active=active,
            )
            self.client.force_login(user)
            response = self.client.get(reverse("admin:index"))
            self.assertEqual(response.status_code, 302)
            self.assertIn("/admin/login/", response.url)

    def test_active_staff_can_access_but_has_no_model_permissions(self):
        user = get_user_model().objects.create_user(username="staff", is_staff=True)
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("admin:index")).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:auth_user_changelist")).status_code, 403)

    def test_superuser_can_login_and_manage_users(self):
        get_user_model().objects.create_superuser(
            username="owner", password="test-only-password-582", email="owner@example.invalid",
        )
        response = self.client.post(reverse("admin:login"), {
            "username": "owner", "password": "test-only-password-582", "next": "/admin/",
        })
        self.assertRedirects(response, reverse("admin:index"))
        self.assertEqual(self.client.get(reverse("admin:auth_user_changelist")).status_code, 200)

    def test_bad_password_does_not_authenticate(self):
        get_user_model().objects.create_user(username="staff", is_staff=True, password="correct")
        response = self.client.post(reverse("admin:login"), {
            "username": "staff", "password": "incorrect",
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
