from authentication.serializers import BaseUserWriteSerializer
from client.models import Client


class ClientWriteSerializer(BaseUserWriteSerializer):
    required_fields = ('first_name', 'last_name', 'cpf')

    class Meta(BaseUserWriteSerializer.Meta):
        model = Client
