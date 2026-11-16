from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from address.models import Address
from address.serializers import AddressSerializer
from authentication.models import CustomUser, Seller


class UserReadSerializer(serializers.ModelSerializer):
    address = AddressSerializer(read_only=True)

    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'cpf',
                  'type', 'seller_name', 'cnpj', 'address')
        read_only_fields = fields


class BaseUserWriteSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=False, style={'input_type': 'password'})
    address = AddressSerializer(required=False)

    # Campos obrigatórios para cada tipo de usuário (definido nas subclasses)
    required_fields = ()

    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'password', 'first_name', 'last_name',
                  'cpf', 'seller_name', 'cnpj', 'type', 'address')
        read_only_fields = ('id', 'type')

    def validate_cpf(self, value):
        if not value:
            return None
        if not (value.isdigit() and len(value) == 11):
            raise serializers.ValidationError('CPF deve conter 11 dígitos.')
        return value

    def validate_cnpj(self, value):
        if not value:
            return None
        if not (value.isdigit() and len(value) == 14):
            raise serializers.ValidationError('CNPJ deve conter 14 dígitos.')
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        errors = {}

        for field in self.required_fields:
            if not attrs.get(field, getattr(self.instance, field, None)):
                errors[field] = 'Campo obrigatório.'

        if self.instance is None and not attrs.get('password'):
            errors['password'] = 'Campo obrigatório.'

        if attrs.get('password'):
            candidate = self.Meta.model(**{
                k: attrs[k] for k in ('username', 'email', 'first_name', 'last_name')
                if k in attrs
            })
            try:
                validate_password(attrs['password'], user=candidate)
            except DjangoValidationError as exc:
                errors['password'] = list(exc.messages)

        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    def create(self, validated_data):
        address_data = validated_data.pop('address', None)
        password = validated_data.pop('password')

        if address_data:
            validated_data['address'] = Address.objects.create(**address_data)

        user = self.Meta.model(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        address_data = validated_data.pop('address', None)
        password = validated_data.pop('password', None)

        if address_data:
            if instance.address:
                for attr, value in address_data.items():
                    setattr(instance.address, attr, value)
                instance.address.save()
            else:
                instance.address = Address.objects.create(**address_data)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance


class SellerWriteSerializer(BaseUserWriteSerializer):
    required_fields = ('seller_name', 'cnpj')

    class Meta(BaseUserWriteSerializer.Meta):
        model = Seller


class LoginSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['type'] = user.type
        token['username'] = user.username
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['type'] = self.user.type
        return data
