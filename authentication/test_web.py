from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from address.models import Address
from authentication.models import CustomUser, Seller

PASSWORD = 'SenhaForte!2026'

ADDRESS_POST = {
    'address-street': 'Rua das Flores',
    'address-number': '10',
    'address-complement': '',
    'address-city': 'Recife',
    'address-state': 'PE',
    'address-district': 'Boa Viagem',
    'address-zipcode': '51020000',
    'address-reference': '',
}

CLIENT_POST = {
    **ADDRESS_POST,
    'username': 'ana',
    'email': 'ana@example.com',
    'first_name': 'Ana',
    'last_name': 'Silva',
    'cpf': '12345678901',
    'password1': PASSWORD,
    'password2': PASSWORD,
}

SELLER_POST = {
    **ADDRESS_POST,
    'username': 'loja',
    'email': 'loja@example.com',
    'seller_name': 'Loja X',
    'cnpj': '12345678000199',
    'password1': PASSWORD,
    'password2': PASSWORD,
}


class WebSignupTests(TestCase):

    def setUp(self):
        cache.clear()

    def test_signup_pages_load(self):
        self.assertEqual(self.client.get('/cadastro/cliente/').status_code, 200)
        self.assertEqual(self.client.get('/cadastro/vendedor/').status_code, 200)

    def test_client_signup_creates_and_logs_in(self):
        response = self.client.post('/cadastro/cliente/', CLIENT_POST)

        self.assertRedirects(response, '/')
        user = CustomUser.objects.get(username='ana')
        self.assertEqual(user.type, CustomUser.Type.CLIENT)
        self.assertTrue(user.check_password(PASSWORD))
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_seller_signup_creates_seller(self):
        self.client.post('/cadastro/vendedor/', SELLER_POST)

        self.assertEqual(Seller.objects.get(username='loja').type, CustomUser.Type.SELLER)

    def test_password_mismatch_is_rejected(self):
        data = {**CLIENT_POST, 'password2': 'OutraSenha!2026'}
        response = self.client.post('/cadastro/cliente/', data)

        self.assertEqual(response.status_code, 200)
        self.assertIn('password2', response.context['form'].errors)
        self.assertFalse(CustomUser.objects.filter(username='ana').exists())

    def test_invalid_state_is_rejected(self):
        data = {**CLIENT_POST, 'address-state': 'XX'}
        response = self.client.post('/cadastro/cliente/', data)

        self.assertIn('state', response.context['address_form'].errors)
        self.assertFalse(Address.objects.exists())


class AccountTests(TestCase):

    def setUp(self):
        cache.clear()
        self.client.post('/cadastro/cliente/', CLIENT_POST)

    def test_account_updates_name_and_address(self):
        data = {**CLIENT_POST, 'first_name': 'Aninha', 'address-city': 'Olinda'}
        response = self.client.post('/conta/', data)

        self.assertRedirects(response, '/conta/')
        user = CustomUser.objects.get(username='ana')
        self.assertEqual(user.first_name, 'Aninha')
        self.assertEqual(user.address.city, 'Olinda')

    def test_account_requires_login(self):
        self.client.logout()
        response = self.client.get('/conta/')

        self.assertEqual(response.status_code, 302)


class WebLoginThrottleTests(TestCase):

    def setUp(self):
        cache.clear()
        self.client.post('/cadastro/cliente/', CLIENT_POST)
        self.client.logout()

    def test_blocks_after_repeated_failures(self):
        for _ in range(5):
            self.client.post('/login/', {'username': 'ana', 'password': 'errada'})

        response = self.client.post('/login/', {'username': 'ana', 'password': PASSWORD})

        self.assertEqual(response.status_code, 429)


class AddressInUseTests(TestCase):

    def setUp(self):
        cache.clear()
        self.client.post('/cadastro/cliente/', CLIENT_POST)
        self.user = CustomUser.objects.get(username='ana')
        admin = CustomUser.objects.create_superuser('admin', 'admin@example.com', PASSWORD)
        self.api = APIClient()
        self.api.force_authenticate(admin)

    def test_delete_address_in_use_returns_409(self):
        response = self.api.delete(f'/api/address/{self.user.address.pk}/')

        self.assertEqual(response.status_code, 409)
        self.assertTrue(Address.objects.filter(pk=self.user.address.pk).exists())
