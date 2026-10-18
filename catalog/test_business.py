from urllib.parse import parse_qs, urlsplit

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from .models import BusinessSettings
from .whatsapp_templates import DEFAULT_MESSAGE_TEMPLATE, DEFAULT_PRODUCT_TEMPLATE


class BusinessSettingsTests(TestCase):
    def test_unconfigured_address_has_no_maps_link(self):
        for url in (reverse("home"), reverse("cart")):
            response = self.client.get(url)
            self.assertContains(response, "todavía no está disponible")
            self.assertNotContains(response, "Abrir en Google Maps")
            self.assertContains(response, '<details id="ubicacion" class="location-panel" data-header-panel>')
        business = BusinessSettings.objects.create()
        for address in ("", "   "):
            business.address = address
            business.maps_url = "https://maps.app.goo.gl/test"
            business.save()
            response = self.client.get(reverse("home"))
            self.assertContains(response, "todavía no está disponible")
            self.assertNotContains(response, "Abrir en Google Maps")

    def test_legacy_location_redirects_open_the_catalog_disclosure(self):
        self.assertEqual(reverse("directions"), "/ubicacion/")
        for url in ("/como-llegar/", "/ubicacion/"):
            self.assertRedirects(self.client.get(url), "/?ubicacion=1#ubicacion", status_code=301)
        response = self.client.get("/", {"ubicacion": "1"})
        self.assertContains(response, '<details id="ubicacion" class="location-panel" data-header-panel open>')
        self.assertNotContains(self.client.get("/", {"ubicacion": "0"}), 'data-header-panel open>')

    def test_address_and_maps_search_are_encoded_and_escaped(self):
        business = BusinessSettings.objects.create(address='Dirección de test 123, Córdoba & "Centro" <local>')
        query = parse_qs(urlsplit(business.location_url).query)
        self.assertEqual(query, {"api": ["1"], "query": [business.address]})
        for name in ("home", "cart"):
            response = self.client.get(reverse(name))
            self.assertContains(response, "Córdoba &amp; &quot;Centro&quot; &lt;local&gt;")
            self.assertContains(response, 'aria-label="Abrir en Google Maps (se abre en otra pestaña)"')
            self.assertContains(response, 'target="_blank" rel="noopener noreferrer"')
            self.assertNotContains(response, "📍")
            self.assertContains(response, '<circle cx="12" cy="10" r="2.5"/>', count=2)
            self.assertNotContains(response, "google.com/maps/embed")

    def test_exact_maps_link_is_used_in_both_public_headers(self):
        business = BusinessSettings.objects.create(address="Dirección real", maps_url="https://maps.app.goo.gl/test")
        for name in ("home", "cart"):
            self.assertContains(self.client.get(reverse(name)), f'href="{business.maps_url}"')

    def test_footer_links_directly_to_maps_and_handles_missing_address(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, 'class="footer-location-unavailable" aria-disabled="true"')
        self.assertNotContains(response, 'class="footer-location"')
        business = BusinessSettings.objects.create(address="Dirección de prueba", maps_url="https://maps.app.goo.gl/test")
        for name in ("home", "cart"):
            response = self.client.get(reverse(name))
            self.assertContains(response, f'class="footer-location" href="{business.maps_url}" target="_blank" rel="noopener noreferrer"')
            self.assertNotContains(response, "data-open-location")

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
        inline = {"opening_intervals-TOTAL_FORMS": "0", "opening_intervals-INITIAL_FORMS": "0",
                  "whatsapp_message_template": DEFAULT_MESSAGE_TEMPLATE, "whatsapp_product_template": DEFAULT_PRODUCT_TEMPLATE}
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

    def test_removed_location_page_does_not_embed_external_resources(self):
        for name in ("home", "cart"):
            response = self.client.get(reverse(name))
            self.assertNotContains(response, "google.com/maps/embed")
            self.assertNotContains(response, "maps/embed")
            self.assertNotContains(response, 'data-open-location')
            self.assertTemplateNotUsed(response, "directions.html")
