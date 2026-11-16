from authentication.views import OwnedUserViewSet
from client.models import Client
from client.serializers import ClientWriteSerializer


class ClientViewSet(OwnedUserViewSet):
    queryset = Client.objects.select_related('address')
    write_serializer_class = ClientWriteSerializer
