from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from address.models import Address
from authentication.models import CustomUser, Seller
from client.models import Client


def _only_digits(value, length, label):
    if not value:
        return None
    if not (value.isdigit() and len(value) == length):
        raise forms.ValidationError(f'{label} deve conter {length} dígitos.')
    return value


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ('street', 'number', 'complement', 'city', 'state', 'district', 'zipcode', 'reference')


class BaseAccountForm(forms.ModelForm):
    required_fields = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in self.required_fields:
            self.fields[name].required = True

    def clean_cpf(self):
        return _only_digits(self.cleaned_data.get('cpf'), 11, 'CPF')

    def clean_cnpj(self):
        return _only_digits(self.cleaned_data.get('cnpj'), 14, 'CNPJ')


class ClientProfileForm(BaseAccountForm):
    required_fields = ('first_name', 'last_name', 'cpf')

    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'cpf')


class SellerProfileForm(BaseAccountForm):
    required_fields = ('seller_name', 'cnpj')

    class Meta:
        model = CustomUser
        fields = ('email', 'seller_name', 'cnpj')


class BaseSignupForm(BaseAccountForm):
    password1 = forms.CharField(label='Senha', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirme a senha', widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get('password1')
        password2 = cleaned.get('password2')

        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'As senhas não coincidem.')

        if password1:
            candidate = self.Meta.model(
                username=cleaned.get('username'),
                email=cleaned.get('email'),
                first_name=cleaned.get('first_name'),
                last_name=cleaned.get('last_name'),
            )
            try:
                validate_password(password1, user=candidate)
            except ValidationError as exc:
                self.add_error('password1', exc)

        return cleaned

    def save(self, commit=True, address=None):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.address = address
        if commit:
            user.save()
        return user


class ClientSignupForm(BaseSignupForm):
    required_fields = ('first_name', 'last_name', 'cpf')

    class Meta:
        model = Client
        fields = ('username', 'email', 'first_name', 'last_name', 'cpf')


class SellerSignupForm(BaseSignupForm):
    required_fields = ('seller_name', 'cnpj')

    class Meta:
        model = Seller
        fields = ('username', 'email', 'seller_name', 'cnpj')
