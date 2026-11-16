from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


def _unique_slug(model, base, instance_pk=None):
    base = slugify(base)[:150] or 'item'
    qs = model.objects.all()
    if instance_pk:
        qs = qs.exclude(pk=instance_pk)
    slug, number = base, 2
    while qs.filter(slug=slug).exists():
        slug = f'{base}-{number}'
        number += 1
    return slug


class Category(models.Model):
    name = models.CharField('Nome', max_length=100)
    slug = models.SlugField('Slug', max_length=120, unique=True, blank=True)
    active = models.BooleanField('Ativa', default=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _unique_slug(Category, self.name, self.pk)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='Vendedor',
        on_delete=models.PROTECT, related_name='products')
    category = models.ForeignKey(
        Category, verbose_name='Categoria', on_delete=models.PROTECT, related_name='products')
    name = models.CharField('Nome', max_length=150)
    slug = models.SlugField('Slug', max_length=170, unique=True, blank=True)
    description = models.TextField('Descrição', blank=True)
    price = models.DecimalField('Preço', max_digits=10, decimal_places=2)
    active = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _unique_slug(Product, self.name, self.pk)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('product-detail', kwargs={'slug': self.slug})

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product, verbose_name='Produto', on_delete=models.CASCADE, related_name='variants')
    sku = models.CharField('SKU', max_length=64, unique=True)
    size = models.CharField('Tamanho', max_length=20, blank=True)
    color = models.CharField('Cor', max_length=30, blank=True)
    price = models.DecimalField(
        'Preço próprio', max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='Deixe em branco para usar o preço do produto')
    stock = models.PositiveIntegerField('Estoque', default=0)
    reserved = models.PositiveIntegerField(
        'Reservado', default=0, help_text='Unidades em checkout ou pedidos ainda não pagos')

    class Meta:
        ordering = ['size', 'color', 'sku']
        verbose_name = 'Variação'
        verbose_name_plural = 'Variações'

    def clean(self):
        if self.reserved > self.stock:
            raise ValidationError('A quantidade reservada não pode ser maior que o estoque.')

    @property
    def effective_price(self):
        return self.price if self.price is not None else self.product.price

    @property
    def available(self):
        return max(self.stock - self.reserved, 0)

    def __str__(self):
        parts = [self.product.name, self.size, self.color]
        return ' '.join(part for part in parts if part)


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, verbose_name='Produto', on_delete=models.CASCADE, related_name='images')
    image = models.ImageField('Imagem', upload_to='products/')
    alt = models.CharField('Texto alternativo', max_length=150, blank=True)
    position = models.PositiveSmallIntegerField('Ordem', default=0)

    class Meta:
        ordering = ['position', 'pk']
        verbose_name = 'Imagem'
        verbose_name_plural = 'Imagens'

    def __str__(self):
        return f'Imagem de {self.product.name}'
