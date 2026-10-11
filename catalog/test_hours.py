from datetime import datetime, time, timezone

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from .business import BUSINESS_TIME_ZONE, business_hours
from .models import BusinessSettings, OpeningInterval


class OpeningHoursTests(TestCase):
    def setUp(self):
        self.business = BusinessSettings.objects.create()

    def interval(self, weekday=0, opens="09:00", closes="12:00"):
        return OpeningInterval(business=self.business, weekday=weekday, opens_at=time.fromisoformat(opens), closes_at=time.fromisoformat(closes))

    def now(self, hour, minute=0, second=0, day=12):
        return datetime(2026, 10, day, hour, minute, second, tzinfo=BUSINESS_TIME_ZONE)

    def test_missing_unpublished_and_explicitly_closed_week(self):
        self.assertEqual(business_hours(None)["label"], "Horarios no disponibles")
        self.interval().save()
        state = business_hours(self.business, self.now(10))
        self.assertEqual(state["label"], "Horarios no disponibles")
        self.assertEqual(state["data"]["intervals"], [])
        self.assertContains(self.client.get("/"), "Horarios no disponibles")
        self.assertNotContains(self.client.get("/"), "09:00")
        self.business.hours_initialized = True
        self.business.save()
        state = business_hours(self.business, self.now(10, day=13))
        self.assertEqual(state["label"], "Cerrado")
        self.assertEqual(len(state["week"]), 7)
        self.assertEqual(state["week"][1]["intervals"], [])
        self.business.opening_intervals.all().delete()
        self.assertEqual(business_hours(self.business, self.now(10))["label"], "Cerrado")
        response = self.client.get("/")
        self.assertNotContains(response, "Según horarios publicados")
        self.assertNotContains(response, "Hora de Buenos Aires. Horario semanal publicado por el comercio.")

    def test_multiple_intervals_exact_boundaries_and_buenos_aires_timezone(self):
        self.interval().save()
        self.interval(opens="15:00", closes="18:00").save()
        self.interval(opens="19:00", closes="21:00").save()
        self.business.hours_initialized = True
        for moment, expected in ((self.now(8, 59, 59), False), (self.now(9), True), (self.now(11, 59, 59), True), (self.now(12), False), (self.now(14, 59, 59), False), (self.now(15), True), (self.now(18), False), (self.now(19), True), (self.now(21), False), (self.now(10, day=13), False)):
            with self.subTest(moment=moment):
                self.assertEqual(business_hours(self.business, moment)["open"], expected)
        self.assertTrue(business_hours(self.business, datetime(2026, 10, 12, 12, tzinfo=timezone.utc))["open"])
        self.assertEqual(len(business_hours(self.business, self.now(10))["week"][0]["intervals"]), 3)

    def test_invalid_time_order_no_overnight_and_valid_weekday(self):
        for interval in (self.interval(opens="12:00", closes="12:00"), self.interval(opens="22:00", closes="02:00"), self.interval(weekday=7), self.interval(weekday=-1)):
            with self.assertRaises(ValidationError):
                interval.full_clean()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.interval(opens="12:00", closes="09:00").save()

    def test_overlaps_rejected_adjacent_and_other_days_allowed(self):
        existing = self.interval()
        existing.save()
        existing.full_clean()
        for opens, closes in (("09:00", "12:00"), ("10:00", "11:00"), ("08:00", "13:00"), ("11:00", "13:00")):
            with self.assertRaises(ValidationError):
                self.interval(opens=opens, closes=closes).full_clean()
        self.interval(opens="12:00", closes="15:00").full_clean()
        self.interval(weekday=1).full_clean()


class OpeningHoursAdminTests(TestCase):
    def setUp(self):
        self.business = BusinessSettings.objects.create()
        self.client.force_login(get_user_model().objects.create_superuser("hours-owner", "", "test"))
        self.url = reverse("admin:catalog_businesssettings_change", args=[1])

    def save_intervals(self, rows):
        data = {"address": "", "maps_url": "", "hours_initialized": "on", "opening_intervals-TOTAL_FORMS": len(rows), "opening_intervals-INITIAL_FORMS": sum(bool(row.get("id")) for row in rows)}
        for index, row in enumerate(rows):
            data.update({f"opening_intervals-{index}-{key}": value for key, value in row.items()})
        return self.client.post(self.url, data)

    def row(self, opens="09:00", closes="12:00", **extra):
        return {"weekday": "0", "opens_at": opens, "closes_at": closes, **extra}

    def test_admin_rejects_new_overlaps_and_invalid_order(self):
        response = self.save_intervals([self.row(), self.row("11:00", "15:00")])
        self.assertContains(response, "no pueden superponerse")
        self.assertFalse(OpeningInterval.objects.exists())
        response = self.save_intervals([self.row("12:00", "09:00")])
        self.assertContains(response, "El cierre debe ser posterior")
        self.assertFalse(OpeningInterval.objects.exists())
        response = self.save_intervals([self.row(), self.row("15:00", "18:00")])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(OpeningInterval.objects.count(), 2)
        self.assertTrue(BusinessSettings.objects.get().hours_initialized)

    def test_admin_validates_final_set_including_edits_and_deletions(self):
        self.save_intervals([self.row(), self.row("15:00", "18:00")])
        first, second = OpeningInterval.objects.all()
        response = self.save_intervals([self.row("10:00", "16:00", id=first.pk), self.row("15:00", "18:00", id=second.pk)])
        self.assertContains(response, "no pueden superponerse")
        response = self.save_intervals([self.row("13:00", "16:00", id=first.pk), self.row("18:00", "20:00", id=second.pk)])
        self.assertEqual(response.status_code, 302)
        response = self.save_intervals([self.row("13:00", "16:00", id=first.pk, DELETE="on"), self.row("13:00", "16:00", id=second.pk)])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(OpeningInterval.objects.count(), 1)
        response = self.save_intervals([self.row("13:00", "16:00", id=second.pk), self.row("16:00", "18:00")])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(OpeningInterval.objects.count(), 2)
