from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView

from catalog.views import (
    cart_page,
    cart_refresh,
    cart_review,
    cart_whatsapp,
    catalog_list,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", catalog_list, name="home"),
    path("ubicacion/", RedirectView.as_view(url="/?ubicacion=1#ubicacion", permanent=True), name="directions"),
    path("como-llegar/", RedirectView.as_view(url="/?ubicacion=1#ubicacion", permanent=True)),
    path("carrito/", cart_page, name="cart"),
    path("carrito/recalcular/", cart_refresh, name="cart_refresh"),
    path("carrito/revisar/", cart_review, name="cart_review"),
    path("carrito/whatsapp/", cart_whatsapp, name="cart_whatsapp"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
