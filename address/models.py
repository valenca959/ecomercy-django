from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

UF_CHOICES = [
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG',
    'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO',
]


def validate_uf(value):
    if value not in UF_CHOICES:
        raise ValidationError('UF inválida. Use a sigla de um dos 27 estados.')


class Address(models.Model):
    street = models.CharField(
        verbose_name='Rua/Av.',
        max_length=100,
        help_text='Nome da rua ou avenida'
    )
    number = models.CharField(
        verbose_name='Número',
        max_length=10,
        validators=[RegexValidator(regex=r'^\d+$', message='Número deve conter apenas dígitos.')],
        help_text='Número da residência ou edifício'
    )
    complement = models.CharField(
        verbose_name='Complemento',
        max_length=50,
        blank=True,
        help_text='Apartamento, casa, fundos etc.'
    )
    city = models.CharField(
        verbose_name='Cidade',
        max_length=50,
        help_text='Nome da cidade'
    )
    state = models.CharField(
        verbose_name='UF',
        max_length=2,
        validators=[validate_uf],
        help_text='Sigla do estado (ex: SP)'
    )
    district = models.CharField(
        verbose_name='Bairro',
        max_length=50,
        help_text='Nome do bairro'
    )
    zipcode = models.CharField(
        verbose_name='CEP',
        max_length=8,
        validators=[RegexValidator(regex=r'^\d{8}$', message='CEP deve conter 8 dígitos.')],
        help_text='Código de Endereçamento Postal'
    )
    reference = models.CharField(
        verbose_name='Ponto de Referência',
        max_length=100,
        blank=True,
        help_text='Ponto de referência para localização'
    )

    class Meta:
        verbose_name = 'Endereço'
        verbose_name_plural = 'Endereços'
        ordering = ['city', 'district', 'street']

    def __str__(self):
        street_number = f'{self.street}, {self.number}'
        if self.complement:
            street_number += f' - {self.complement}'
        return f'{street_number}, {self.district}, {self.city} - {self.state} - CEP: {self.zipcode}'
