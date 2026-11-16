from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from authentication.models import CustomUser, Seller
from authentication.permissions import IsOwnerOrAdmin
from authentication.serializers import (
    LoginSerializer,
    SellerWriteSerializer,
    UserReadSerializer,
)


class OwnedUserViewSet(viewsets.ModelViewSet):
    """
    Cadastro é público. Consulta e edição ficam restritas ao próprio usuário
    ou a administradores. Exclusão é exclusiva de administradores.
    """
    read_serializer_class = UserReadSerializer
    write_serializer_class = None

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return self.read_serializer_class
        return self.write_serializer_class

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        if self.action == 'destroy':
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]

    def get_queryset(self):
        queryset = super().get_queryset()
        if getattr(self, 'swagger_fake_view', False):
            return queryset.none()
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(pk=self.request.user.pk)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """Listagem de todos os usuários, somente para administradores."""
    queryset = CustomUser.objects.select_related('address')
    serializer_class = UserReadSerializer
    permission_classes = [permissions.IsAdminUser]


class SellerViewSet(OwnedUserViewSet):
    queryset = Seller.objects.select_related('address')
    write_serializer_class = SellerWriteSerializer


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'


class MeView(APIView):
    def get(self, request):
        return Response(UserReadSerializer(request.user).data)
