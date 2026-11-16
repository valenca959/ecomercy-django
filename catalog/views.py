from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from authentication.models import CustomUser
from catalog.forms import ImageFormSet, ProductForm, StoreFilterForm, VariantFormSet
from catalog.models import Product

SORT_ORDERS = {
    'recent': '-created_at',
    'price_asc': 'price',
    'price_desc': '-price',
    'name': 'name',
}


def store_list(request):
    form = StoreFilterForm(request.GET or None)
    products = (
        Product.objects.filter(active=True, category__active=True)
        .select_related('category', 'seller')
        .prefetch_related('images')
    )

    if form.is_valid():
        data = form.cleaned_data
        if data['q']:
            products = products.filter(
                Q(name__icontains=data['q']) | Q(description__icontains=data['q']))
        if data['category']:
            products = products.filter(category=data['category'])
        if data['min_price'] is not None:
            products = products.filter(price__gte=data['min_price'])
        if data['max_price'] is not None:
            products = products.filter(price__lte=data['max_price'])
        products = products.order_by(SORT_ORDERS.get(data['sort'], '-created_at'))

    # Mantém os filtros ao trocar de página, sem repetir o parâmetro `page`.
    query = request.GET.copy()
    query.pop('page', None)
    page = Paginator(products, 12).get_page(request.GET.get('page'))

    return render(request, 'catalog/store_list.html', {
        'form': form,
        'page': page,
        'query_string': query.urlencode(),
    })


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related('category', 'seller')
        .prefetch_related('images', 'variants'),
        slug=slug, active=True, category__active=True)
    return render(request, 'catalog/product_detail.html', {'product': product})


def seller_required(view):
    """Exige login e tipo vendedor."""
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if request.user.type != CustomUser.Type.SELLER:
            return HttpResponseForbidden('Esta área é exclusiva para vendedores.')
        return view(request, *args, **kwargs)
    return login_required(wrapper)


@seller_required
def seller_product_list(request):
    products = Product.objects.filter(seller_id=request.user.pk).select_related('category')
    return render(request, 'catalog/seller/product_list.html', {'products': products})


@seller_required
def seller_product_create(request):
    product = Product(seller_id=request.user.pk)
    return _save_product(request, product, 'Cadastrar produto', 'Produto cadastrado.')


@seller_required
def seller_product_edit(request, pk):
    # Vendedor só edita os próprios produtos; outros retornam 404.
    product = get_object_or_404(Product, pk=pk, seller_id=request.user.pk)
    return _save_product(request, product, 'Editar produto', 'Produto atualizado.')


def _save_product(request, product, title, success_message):
    form = ProductForm(request.POST or None, instance=product)
    variants = VariantFormSet(request.POST or None, instance=product, prefix='variants')
    images = ImageFormSet(
        request.POST or None, request.FILES or None, instance=product, prefix='images')

    if request.method == 'POST':
        # Avalia os três antes de decidir, para mostrar todos os erros de uma vez.
        valid = [form.is_valid(), variants.is_valid(), images.is_valid()]
        if all(valid):
            with transaction.atomic():
                product = form.save()
                variants.save()
                images.save()
            messages.success(request, success_message)
            return redirect('seller-products')

    return render(request, 'catalog/seller/product_form.html', {
        'form': form,
        'variants': variants,
        'images': images,
        'title': title,
    })
