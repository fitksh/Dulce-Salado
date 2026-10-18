from .business import business_hours
from .models import BusinessSettings, Category


def business_information(request):
    business = BusinessSettings.objects.prefetch_related("opening_intervals").first()
    return {
        "business": business,
        "business_hours": business_hours(business),
        "categories": Category.objects.filter(is_active=True),
    }
