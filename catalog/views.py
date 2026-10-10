
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Case, IntegerField, Q, Value, When
from django.shortcuts import get_object_or_404, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .cart import calculate_cart, parse_items, product_revision
from .models import Category, Product
from .whatsapp import PRICE_WARNING, whatsapp_message, whatsapp_url


def catalog_list(request):
    categories = Category.objects.filter(is_active=True)
    products = Product.objects.filter(is_active=True, category__is_active=True).select_related("category")
    query = request.GET.get("q", "").strip()[:180]
    category_slug = request.GET.get("categoria", "")
    selected_category = get_object_or_404(categories, slug=category_slug) if category_slug else None
    if selected_category:
        products = products.filter(category=selected_category)
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(brand__icontains=query) | Q(description__icontains=query)
        ).annotate(search_rank=Case(
            When(name__icontains=query, then=Value(0)),
            When(brand__icontains=query, then=Value(1)),
            default=Value(2), output_field=IntegerField(),
        )).order_by("search_rank", "name", "pk")
    page = Paginator(products, 24).get_page(request.GET.get("page"))
    for product in page:
        product.cart_revision = product_revision(product)
    return render(request, "home.html", {
        "categories": categories, "selected_category": selected_category, "query": query, "page": page,
    })


def cart_page(request):
    return render(request, "cart.html")


def directions_page(request):
    return render(request, "directions.html")


@require_POST
@never_cache
def cart_refresh(request):
    try:
        cart = calculate_cart(parse_items(request.POST.get("items")))
    except ValidationError as error:
        return render(request, "cart_error.html", {"error": error.messages[0]}, status=400)
    return render(request, "cart_contents.html", {"cart": cart})


def render_review(request, cart, ready_url=""):
    return render(request, "cart_review.html", {
        "cart": cart, "warning": PRICE_WARNING, "message": whatsapp_message(cart),
        "whatsapp_configured": bool(settings.WHATSAPP_PHONE), "ready_url": ready_url,
    })


@require_POST
@never_cache
def cart_review(request):
    try:
        cart = calculate_cart(parse_items(request.POST.get("items")))
    except ValidationError as error:
        return render(request, "cart_error.html", {"error": error.messages[0]}, status=400)
    return render_review(request, cart)


@require_POST
@never_cache
def cart_whatsapp(request):
    try:
        submitted = parse_items(request.POST.get("items"))
        cart = calculate_cart(submitted)
    except ValidationError as error:
        return render(request, "cart_error.html", {"error": error.messages[0]}, status=400)
    changed = any(before.get("revision") != after["revision"] for before, after in zip(submitted, cart["items"]))
    if changed and not cart["notices"]:
        cart["notices"].append("Revisá la información actual del catálogo antes de continuar.")
    ready = request.POST.get("accepted") == "yes" and cart["valid"] and not changed
    return render_review(request, cart, whatsapp_url(whatsapp_message(cart)) if ready else "")
