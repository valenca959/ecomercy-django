from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models

from address.models import Address


class CustomUser(AbstractUser):

    # Modelo de usuário com tipo: vendedor ou cliente.

    class Type(models.IntegerChoices):
        SELLER = 1, "Vendedor"
        CLIENT = 2, "Cliente"

    base_type = Type.CLIENT

    type = models.PositiveSmallIntegerField(
        choices=Type.choices, default=base_type,
        help_text='Tipo de usuário (1 - Vendedor, 2 - Cliente)')

    # Campos comuns
    email = models.EmailField(verbose_name='e-mail', unique=True)
    username = models.CharField(verbose_name='Nome de Usuário', max_length=50, unique=True)
    address = models.ForeignKey(
        Address, verbose_name='Endereço', on_delete=models.PROTECT,
        blank=True, null=True)

    # Campos do cliente
    first_name = models.CharField(verbose_name='Nome', max_length=50, blank=True)
    last_name = models.CharField(verbose_name='Sobrenome', max_length=100, blank=True)
    cpf = models.CharField(
        verbose_name='CPF', help_text='Sem pontuação', max_length=11,
        blank=True, null=True, unique=True)

    # Campos do vendedor
    seller_name = models.CharField(verbose_name='Nome Vendedor', max_length=100, blank=True)
    cnpj = models.CharField(
        verbose_name='CNPJ', help_text='Sem pontuação', max_length=14,
        blank=True, null=True, unique=True)

    # Relações com modificação para `related_name`
    groups = models.ManyToManyField('auth.Group', related_name='custom_users')
    user_permissions = models.ManyToManyField('auth.Permission', related_name='custom_user_permissions')

    def save(self, *args, **kwargs):
        # Proxies (Client, Seller) sempre gravam o próprio tipo ao serem criados.
        if self._state.adding and self._meta.proxy:
            self.type = self.base_type
        super().save(*args, **kwargs)

    def __str__(self):
        return f'#ID {self.id}, username {self.username}'


class TypedUserManager(UserManager):
    user_type = None

    def get_queryset(self):
        return super().get_queryset().filter(type=self.user_type)


class SellerManager(TypedUserManager):
    user_type = CustomUser.Type.SELLER


class Seller(CustomUser):
    base_type = CustomUser.Type.SELLER
    objects = SellerManager()

    class Meta:
        proxy = True
        verbose_name = 'Vendedor'
        verbose_name_plural = 'Vendedores'
