from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .cart import calculate_cart, parse_items, product_revision
from .models import Category, Product


def catalog_list(request):
    categories = Category.objects.filter(is_active=True)
    products = Product.objects.filter(is_active=True, category__is_active=True).select_related("category")
    query = request.GET.get("q", "").strip()[:180]
    category_slug = request.GET.get("categoria", "")
    selected_category = get_object_or_404(categories, slug=category_slug) if category_slug else None
    if selected_category:
        products = products.filter(category=selected_category)
    if query:
        products = products.filter(Q(name__icontains=query) | Q(brand__icontains=query))
    page = Paginator(products, 24).get_page(request.GET.get("page"))
    for product in page:
        product.cart_revision = product_revision(product)
    return render(request, "home.html", {
        "categories": categories, "selected_category": selected_category, "query": query, "page": page,
    })


def cart_page(request):
    return render(request, "cart.html")


@require_POST
@never_cache
def cart_refresh(request):
    try:
        cart = calculate_cart(parse_items(request.POST.get("items")))
    except ValidationError as error:
        return render(request, "cart_error.html", {"error": error.messages[0]}, status=400)
    return render(request, "cart_contents.html", {"cart": cart})
