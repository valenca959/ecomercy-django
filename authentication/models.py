from django.db import models

from django.contrib.auth.models import AbstractUser
from address.models import Address

class CustomUser(AbstractUser):

    #Modelo de usuário personalizado com tipo e campos adicionais para clientes e vendedores.
    
    class Type(models.IntegerChoices):
        SELLER = 1, "Vendedor"
        CLIENT = 2, "Cliente"
        
    base_type = Type.CLIENT
    
    type = models.PositiveSmallIntegerField(
        choices=Type.choices, default=base_type, 
        help_text='Tipo de usuário (1 - Vendedor, 2 - Cliente)')
    
    # Campos Comuns
    email = models.EmailField(verbose_name='e-mail')
    username = models.CharField(verbose_name='Nome de Usuário', max_length=50,
        unique=True)
    address = models.ForeignKey(
        Address, verbose_name='Endereço', on_delete=models.CASCADE, 
        blank=True, null=True)

    # Campos do cliente
    first_name = models.CharField(verbose_name='Nome', max_length=20, 
        blank=True, null=True)
    last_name = models.CharField(verbose_name='Sobrenome', max_length=30, 
        blank=True, null=True)
    cpf = models.CharField(
        verbose_name='CPF', help_text='Sem pontuação', max_length=11, 
        blank=True, null=True)
    
    # Campos do Vendedor
    seller_name = models.CharField(verbose_name='Nome Vendedor', max_length=100,
        blank=True, null=True)
    cnpj = models.CharField(verbose_name='CNPJ', max_length=14, 
        blank=True, null=True)
    
    # Relações com modificação para `related_name`
    groups = models.ManyToManyField('auth.Group', related_name='custom_users')
    user_permissions = models.ManyToManyField('auth.Permission', related_name='custom_user_permissions')
    
    def __str__(self):
        return f'#ID {self.id}, username {self.username}'
