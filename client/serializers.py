from rest_framework import serializers

from client.models import Client
from address.serializers import AddressSerializer

class ClientSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Client
        fields = (
            'id',
            "first_name",
            "last_name",
            "cpf",
            "email",
            "username",
            "password",
            'type',
            "address",
            )
    
    password = serializers.CharField(write_only=True, required=False)
    address = AddressSerializer(many=False, required=False)
    