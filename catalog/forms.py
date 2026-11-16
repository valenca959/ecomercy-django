from django import forms
from django.forms import inlineformset_factory

from catalog.models import Category, Product, ProductImage, ProductVariant


class StoreFilterForm(forms.Form):
    SORT_CHOICES = [
        ('', 'Relevância'),
        ('recent', 'Mais recentes'),
        ('price_asc', 'Menor preço'),
        ('price_desc', 'Maior preço'),
        ('name', 'Nome'),
    ]

    q = forms.CharField(label='Buscar', required=False)
    category = forms.ModelChoiceField(
        label='Categoria', queryset=Category.objects.filter(active=True),
        required=False, empty_label='Todas')
    min_price = forms.DecimalField(
        label='Preço mínimo', required=False, min_value=0, max_digits=10, decimal_places=2)
    max_price = forms.DecimalField(
        label='Preço máximo', required=False, min_value=0, max_digits=10, decimal_places=2)
    sort = forms.ChoiceField(label='Ordenar por', required=False, choices=SORT_CHOICES)


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ('category', 'name', 'description', 'price', 'active')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(active=True)

    def clean_price(self):
        price = self.cleaned_data['price']
        if price <= 0:
            raise forms.ValidationError('O preço deve ser maior que zero.')
        return price


class VariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ('sku', 'size', 'color', 'price', 'stock')

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price <= 0:
            raise forms.ValidationError('O preço deve ser maior que zero.')
        return price


VariantFormSet = inlineformset_factory(
    Product, ProductVariant, form=VariantForm,
    extra=1, min_num=1, validate_min=True, can_delete=True)

ImageFormSet = inlineformset_factory(
    Product, ProductImage, fields=('image', 'alt', 'position'),
    extra=2, can_delete=True)
