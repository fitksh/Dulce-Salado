from urllib.parse import parse_qs, urlsplit

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from .models import BusinessSettings


class BusinessSettingsTests(TestCase):
    def test_unconfigured_address_has_no_maps_link(self):
        response = self.client.get(reverse("directions"))
        self.assertContains(response, "todavía no está disponible")
        self.assertNotContains(response, "Abrir en Google Maps")
        business = BusinessSettings.objects.create()
        for address in ("", "   "):
            business.address = address
            business.maps_url = "https://maps.app.goo.gl/test"
            business.save()
            response = self.client.get(reverse("directions"))
            self.assertContains(response, "todavía no está disponible")
            self.assertNotContains(response, "Abrir en Google Maps")
        self.assertContains(self.client.get("/"), 'href="/como-llegar/"')

    def test_address_and_maps_search_are_encoded_and_escaped(self):
        business = BusinessSettings.objects.create(address='Dirección de test 123, Córdoba & "Centro"')
        query = parse_qs(urlsplit(business.location_url).query)
        self.assertEqual(query, {"api": ["1"], "query": [business.address]})
        response = self.client.get(reverse("directions"))
        self.assertContains(response, "Córdoba &amp; &quot;Centro&quot;")
        self.assertContains(response, "Abrir en Google Maps")

    def test_exact_url_validation_and_precedence(self):
        for url in ("https://maps.app.goo.gl/test", "https://www.google.com/maps/place/Test", "https://maps.google.com/?q=Test", "https://goo.gl/maps/test"):
            business = BusinessSettings(address="Test", maps_url=url)
            business.full_clean()
            self.assertEqual(business.location_url, url)
        for url in ("javascript:alert(1)", "http://maps.app.goo.gl/test", "https://example.com", "https://google.com.evil.test/maps", "https://www.google.com/search?q=Test"):
            with self.subTest(url=url), self.assertRaises(ValidationError):
                BusinessSettings(address="Test", maps_url=url).full_clean()

    def test_database_and_admin_keep_a_single_configuration(self):
        owner = get_user_model().objects.create_superuser("business-owner", "", "test")
        self.client.force_login(owner)
        url = reverse("admin:catalog_businesssettings_add")
        inline = {"opening_intervals-TOTAL_FORMS": "0", "opening_intervals-INITIAL_FORMS": "0"}
        response = self.client.post(url, {"address": "Dirección de test", "maps_url": "", **inline})
        self.assertEqual(response.status_code, 302)
        business = BusinessSettings.objects.get()
        self.assertEqual(business.pk, 1)
        self.assertEqual(self.client.get(url).status_code, 403)
        with self.assertRaises(IntegrityError), transaction.atomic():
            BusinessSettings.objects.create(pk=2, address="No permitida")
        self.assertEqual(self.client.post(reverse("admin:catalog_businesssettings_delete", args=[1]), {"post": "yes"}).status_code, 403)
        response = self.client.post(reverse("admin:catalog_businesssettings_change", args=[1]), {"address": "Dirección corregida", "maps_url": "", **inline})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(BusinessSettings.objects.count(), 1)
        self.assertEqual(BusinessSettings.objects.get().address, "Dirección corregida")

    def test_staff_requires_configuration_permission(self):
        staff = get_user_model().objects.create_user("business-staff", is_staff=True)
        self.client.force_login(staff)
        url = reverse("admin:catalog_businesssettings_changelist")
        self.assertEqual(self.client.get(url).status_code, 403)
        staff.user_permissions.add(Permission.objects.get(codename="view_businesssettings"))
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:catalog_businesssettings_add")).status_code, 403)
