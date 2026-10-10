from .business import business_hours
from .models import BusinessSettings


def business_information(request):
    business = BusinessSettings.objects.prefetch_related("opening_intervals").first()
    return {"business": business, "business_hours": business_hours(business)}
