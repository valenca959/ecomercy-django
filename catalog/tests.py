from decimal import Decimal

from django.test import TestCase

from authentication.models import CustomUser, Seller
from catalog.models import Category, Product, ProductVariant
from client.models import Client

PASSWORD = 'SenhaForte!2026'


def make_user(model, username, **extra):
    user = model(username=username, email=f'{username}@example.com', **extra)
    user.set_password(PASSWORD)
    user.save()
    return user


def make_product(seller, category, name='Camiseta', price='99.90', active=True):
    return Product.objects.create(
        seller=seller, category=category, name=name,
        price=Decimal(price), active=active)


def product_post(category, **overrides):
    """Dados de um formulário de produto com uma variação."""
    data = {
        'category': category.pk,
        'name': 'Camiseta Básica',
        'description': 'Algodão',
        'price': '99.90',
        'active': 'on',
        'variants-TOTAL_FORMS': '1',
        'variants-INITIAL_FORMS': '0',
        'variants-MIN_NUM_FORMS': '0',
        'variants-MAX_NUM_FORMS': '1000',
        'variants-0-sku': 'CAM-P-AZ',
        'variants-0-size': 'P',
        'variants-0-color': 'Azul',
        'variants-0-price': '',
        'variants-0-stock': '5',
        'images-TOTAL_FORMS': '0',
        'images-INITIAL_FORMS': '0',
        'images-MIN_NUM_FORMS': '0',
        'images-MAX_NUM_FORMS': '1000',
    }
    data.update(overrides)
    return data


class StoreTests(TestCase):

    def setUp(self):
        self.seller = make_user(Seller, 'loja', seller_name='Loja X', cnpj='12345678000199')
        self.category = Category.objects.create(name='Camisetas')
        self.visible = make_product(self.seller, self.category, 'Camiseta Azul')
        self.hidden = make_product(self.seller, self.category, 'Camiseta Oculta', active=False)

    def test_store_lists_only_active_products(self):
        response = self.client.get('/loja/')

        self.assertContains(response, 'Camiseta Azul')
        self.assertNotContains(response, 'Camiseta Oculta')

    def test_search_filters_by_name(self):
        make_product(self.seller, self.category, 'Calça Jeans')

        response = self.client.get('/loja/', {'q': 'Calça'})

        self.assertContains(response, 'Calça Jeans')
        self.assertNotContains(response, 'Camiseta Azul')

    def test_price_filter(self):
        make_product(self.seller, self.category, 'Barata', price='10.00')

        response = self.client.get('/loja/', {'max_price': '50'})

        self.assertContains(response, 'Barata')
        self.assertNotContains(response, 'Camiseta Azul')

    def test_inactive_product_detail_returns_404(self):
        response = self.client.get(self.hidden.get_absolute_url())

        self.assertEqual(response.status_code, 404)

    def test_product_detail_loads(self):
        response = self.client.get(self.visible.get_absolute_url())

        self.assertEqual(response.status_code, 200)

    def test_slug_is_unique_for_same_name(self):
        second = make_product(self.seller, self.category, 'Camiseta Azul')

        self.assertNotEqual(self.visible.slug, second.slug)


class VariantStockTests(TestCase):

    def test_available_is_stock_minus_reserved(self):
        seller = make_user(Seller, 'loja', seller_name='Loja X', cnpj='12345678000199')
        category = Category.objects.create(name='Camisetas')
        product = make_product(seller, category)
        variant = ProductVariant.objects.create(
            product=product, sku='SKU-1', stock=5, reserved=2)

        self.assertEqual(variant.available, 3)
        self.assertEqual(variant.effective_price, product.price)


class SellerAreaTests(TestCase):

    def setUp(self):
        self.seller = make_user(Seller, 'loja', seller_name='Loja X', cnpj='12345678000199')
        self.buyer = make_user(Client, 'ana', first_name='Ana', last_name='Silva', cpf='12345678901')
        self.category = Category.objects.create(name='Camisetas')

    def test_anonymous_is_redirected_to_login(self):
        response = self.client.get('/vendedor/produtos/')

        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])

    def test_client_cannot_access_seller_area(self):
        self.client.force_login(self.buyer)

        response = self.client.get('/vendedor/produtos/')

        self.assertEqual(response.status_code, 403)

    def test_seller_creates_product_with_variant(self):
        self.client.force_login(self.seller)

        response = self.client.post('/vendedor/produtos/novo/', product_post(self.category))

        self.assertRedirects(response, '/vendedor/produtos/')
        product = Product.objects.get(name='Camiseta Básica')
        self.assertEqual(product.seller, self.seller)
        self.assertEqual(product.variants.count(), 1)
        self.assertEqual(product.variants.first().sku, 'CAM-P-AZ')

    def test_product_requires_at_least_one_variant(self):
        self.client.force_login(self.seller)
        data = product_post(self.category, **{'variants-TOTAL_FORMS': '0'})

        response = self.client.post('/vendedor/produtos/novo/', data)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Product.objects.exists())

    def test_seller_cannot_edit_another_sellers_product(self):
        other = make_user(Seller, 'outra', seller_name='Outra', cnpj='98765432000100')
        product = make_product(other, self.category)
        self.client.force_login(self.seller)

        response = self.client.get(f'/vendedor/produtos/{product.pk}/editar/')

        self.assertEqual(response.status_code, 404)

    def test_seller_lists_only_own_products(self):
        make_product(self.seller, self.category, 'Minha Camiseta')
        other = make_user(Seller, 'outra', seller_name='Outra', cnpj='98765432000100')
        make_product(other, self.category, 'Camiseta Alheia')
        self.client.force_login(self.seller)

        response = self.client.get('/vendedor/produtos/')

        self.assertContains(response, 'Minha Camiseta')
        self.assertNotContains(response, 'Camiseta Alheia')
