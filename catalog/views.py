
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Case, IntegerField, Q, Value, When
from django.shortcuts import get_object_or_404, render
from django.views.decorators.cache import never_cache
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_POST

from .cart import calculate_cart, parse_items, product_revision
from .models import Category, Order, Product
from .order_forms import CustomerForm
from .orders import confirmation_key, confirmation_token, prepare_order, public_base_url
from .whatsapp import message_configuration


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
    # Veinte completa filas tanto de cuatro como de cinco columnas.
    page = Paginator(products, 20).get_page(request.GET.get("page"))
    for product in page:
        product.cart_revision = product_revision(product)
    return render(request, "home.html", {
        "categories": categories, "selected_category": selected_category, "query": query, "page": page,
    })


@xframe_options_sameorigin
def cart_page(request):
    panel = request.GET.get("panel") == "1"
    return render(request, "cart_frame.html" if panel else "cart.html", {"cart_panel": panel})


@require_POST
@never_cache
def cart_refresh(request):
    try:
        cart = calculate_cart(parse_items(request.POST.get("items")))
    except ValidationError as error:
        return render(request, "cart_error.html", {"error": error.messages[0]}, status=400)
    return render(request, "cart_contents.html", {"cart": cart, "cart_panel": request.POST.get("panel") == "1"})


def render_review(request, cart, configuration=None, form=None, token=None, review_required=False):
    configuration = configuration if configuration is not None else message_configuration()
    error = ""
    try:
        public_base_url()
    except ValidationError as exception:
        error = exception.messages[0]
    return render(request, "cart_review.html", {
        "cart": cart, "customer_form": form if form is not None else CustomerForm(),
        "confirmation_token": token or confirmation_token(),
        "message_revision": configuration["revision"], "review_required": review_required,
        "whatsapp_configured": bool(settings.WHATSAPP_PHONE), "configuration_error": error,
    })


@require_POST
@never_cache
def cart_review(request):
    try:
        cart = calculate_cart(parse_items(request.POST.get("items")))
    except ValidationError as error:
        return render(request, "cart_error.html", {"error": error.messages[0]}, status=400)
    token = request.POST.get("confirmation_token", "")
    try:
        confirmation_key(token)
    except ValidationError:
        token = confirmation_token()
    return render_review(request, cart, token=token)


@require_POST
@never_cache
def cart_whatsapp(request):
    form = CustomerForm(request.POST)
    try:
        submitted = parse_items(request.POST.get("items"))
    except ValidationError as error:
        return render(request, "cart_error.html", {"error": error.messages[0]}, status=400)
    token = request.POST.get("confirmation_token", "")
    if form.is_valid() and request.POST.get("accepted") == "yes":
        try:
            order, cart, configuration = prepare_order(
                submitted, form.cleaned_data, token, request.POST.get("message_revision", ""),
            )
            if order:
                return render(request, "order_result.html", {"order": order})
            return render_review(request, cart, configuration, form, token, review_required=True)
        except ValidationError as error:
            form.add_error(None, error)
    return render_review(request, calculate_cart(submitted), form=form, token=token)


@never_cache
def order_detail(request, token):
    if request.method not in ("GET", "HEAD"):
        from django.http import HttpResponseNotAllowed
        return HttpResponseNotAllowed(["GET", "HEAD"])
    order = get_object_or_404(Order, token=token)
    response = render(request, "order_detail.html", {"order": order})
    response["X-Robots-Tag"] = "noindex, nofollow, noarchive"
    response["Referrer-Policy"] = "no-referrer"
    return response
