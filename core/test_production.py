import json
import os
import subprocess
import sys

from django.contrib.auth import get_user_model
from django.test import Client, SimpleTestCase, TestCase, override_settings


class ProductionSettingsTests(SimpleTestCase):
    def load_settings(self, **values):
        environment = {k: v for k, v in os.environ.items() if not k.startswith("DJANGO_")}
        environment.update(DJANGO_SECRET_KEY="isolated-settings-test-only", **values)
        result = subprocess.run([
            sys.executable, "-c",
            "import json; from config import settings as s; "
            "print(json.dumps([s.DEBUG,s.SESSION_COOKIE_SECURE,s.CSRF_COOKIE_SECURE,"
            "s.SECURE_PROXY_SSL_HEADER,s.CSRF_TRUSTED_ORIGINS,s.USE_X_FORWARDED_HOST]))",
        ], env=environment, text=True, capture_output=True, check=True)
        return json.loads(result.stdout)

    def test_production_defaults_secure_cookies_without_implicit_proxy_trust(self):
        self.assertEqual(self.load_settings(), [False, True, True, None, [], False])

    def test_development_keeps_local_cookie_behavior(self):
        self.assertEqual(self.load_settings(DJANGO_DEBUG="1"),
                         [True, False, False, None, [], False])

    def test_proxy_trust_requires_explicit_opt_in(self):
        actual = self.load_settings(
            DJANGO_TRUST_PROXY_HTTPS="1",
            DJANGO_CSRF_TRUSTED_ORIGINS=" https://dulceysalado.ar, ",
        )
        self.assertEqual(actual, [False, True, True, ["HTTP_X_FORWARDED_PROTO", "https"],
                                  ["https://dulceysalado.ar"], False])


@override_settings(
    DEBUG=False,
    ALLOWED_HOSTS=["dulceysalado.ar"],
    SESSION_COOKIE_SECURE=True,
    CSRF_COOKIE_SECURE=True,
    SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO", "https"),
    CSRF_TRUSTED_ORIGINS=["https://dulceysalado.ar"],
)
class ProxiedAdminSecurityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        get_user_model().objects.create_superuser(
            username="isolated-admin", password="test-only-secure-login-2026",
            email="admin@example.invalid",
        )

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True, HTTP_HOST="dulceysalado.ar",
                             HTTP_X_FORWARDED_PROTO="https")

    def login_data(self):
        response = self.client.get("/admin/login/")
        self.assertTrue(response.cookies["csrftoken"]["secure"])
        return {
            "username": "isolated-admin", "password": "test-only-secure-login-2026",
            "csrfmiddlewaretoken": self.client.cookies["csrftoken"].value, "next": "/admin/",
        }

    def test_valid_https_login_and_secure_session(self):
        response = self.client.post("/admin/login/", self.login_data(),
                                    HTTP_ORIGIN="https://dulceysalado.ar")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/admin/")
        self.assertTrue(response.cookies["sessionid"]["secure"])
        self.assertTrue(response.cookies["sessionid"]["httponly"])
        self.assertEqual(self.client.get("/admin/").status_code, 200)

    def test_missing_csrf_is_rejected(self):
        self.assertEqual(self.client.post("/admin/login/", {
            "username": "isolated-admin", "password": "test-only-secure-login-2026",
        }, HTTP_ORIGIN="https://dulceysalado.ar").status_code, 403)

    def test_foreign_origin_is_rejected_even_with_a_valid_token(self):
        response = self.client.post("/admin/login/", self.login_data(),
                                    HTTP_ORIGIN="https://attacker.example")
        self.assertEqual(response.status_code, 403)

    def test_unknown_host_is_rejected(self):
        self.assertEqual(self.client.get("/", HTTP_HOST="attacker.example").status_code, 400)

    def test_production_error_does_not_expose_debug_traceback(self):
        response = self.client.get("/nonexistent-production-check/")
        self.assertEqual(response.status_code, 404)
        self.assertNotContains(response, "Using the URLconf", status_code=404)
