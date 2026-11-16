from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase

from authentication.models import CustomUser, Seller
from client.models import Client

PASSWORD = 'SenhaForte!2026'

ADDRESS = {
    'street': 'Rua das Flores',
    'number': '10',
    'complement': '',
    'city': 'Recife',
    'state': 'PE',
    'district': 'Boa Viagem',
    'zipcode': '51020000',
    'reference': '',
}

CLIENT_DATA = {
    'username': 'ana',
    'email': 'ana@example.com',
    'password': PASSWORD,
    'first_name': 'Ana',
    'last_name': 'Silva',
    'cpf': '12345678901',
    'address': ADDRESS,
}

SELLER_DATA = {
    'username': 'loja',
    'email': 'loja@example.com',
    'password': PASSWORD,
    'seller_name': 'Loja X',
    'cnpj': '12345678000199',
    'address': ADDRESS,
}


class SignupTests(APITestCase):

    def test_cliente_signup_hashes_password_and_sets_type(self):
        response = self.client.post('/api/clients/', CLIENT_DATA, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = CustomUser.objects.get(username='ana')
        self.assertEqual(user.type, CustomUser.Type.CLIENT)
        self.assertTrue(user.check_password(PASSWORD))
        self.assertNotIn('password', response.data)

    def test_vendedor_signup_sets_seller_type(self):
        response = self.client.post('/api/sellers/', SELLER_DATA, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Seller.objects.get(username='loja').type, CustomUser.Type.SELLER)
        self.assertFalse(Client.objects.filter(username='loja').exists())

    def test_weak_password_is_rejected(self):
        data = {**CLIENT_DATA, 'password': '123'}
        response = self.client.post('/api/clients/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)


class LoginTests(APITestCase):

    def setUp(self):
        cache.clear()
        self.client.post('/api/clients/', CLIENT_DATA, format='json')

    def test_login_returns_tokens_and_type(self):
        response = self.client.post(
            '/api/auth/login/', {'username': 'ana', 'password': PASSWORD}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertEqual(response.data['type'], CustomUser.Type.CLIENT)

    def test_wrong_password_is_rejected(self):
        response = self.client.post(
            '/api/auth/login/', {'username': 'ana', 'password': 'errada'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PermissionTests(APITestCase):

    def setUp(self):
        cache.clear()
        self.client.post('/api/clients/', CLIENT_DATA, format='json')
        other = {**CLIENT_DATA, 'username': 'bia', 'email': 'bia@example.com', 'cpf': '98765432100'}
        self.client.post('/api/clients/', other, format='json')

    def login_as(self, username):
        response = self.client.post(
            '/api/auth/login/', {'username': username, 'password': PASSWORD}, format='json')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def test_anonymous_cannot_list_clients(self):
        response = self.client.get('/api/clients/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_client_sees_only_self(self):
        self.login_as('ana')
        response = self.client.get('/api/clients/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], 'ana')

    def test_client_cannot_read_another_client(self):
        self.login_as('ana')
        other_id = CustomUser.objects.get(username='bia').pk
        response = self.client.get(f'/api/clients/{other_id}/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_me_returns_logged_user(self):
        self.login_as('ana')
        response = self.client.get('/api/auth/me/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'ana')
