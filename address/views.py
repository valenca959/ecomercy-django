from django.db.models import ProtectedError
from rest_framework import status, viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from address.models import Address
from address.serializers import AddressSerializer


class AddressViewSet(viewsets.ModelViewSet):
    """Endereços são editados pelo próprio usuário; esta rota fica restrita a administradores."""
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [IsAdminUser]

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {'detail': 'Este endereço está em uso por um usuário e não pode ser removido.'},
                status=status.HTTP_409_CONFLICT)
