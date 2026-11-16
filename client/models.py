from authentication.models import CustomUser, TypedUserManager


class ClientManager(TypedUserManager):
    user_type = CustomUser.Type.CLIENT


class Client(CustomUser):
    base_type = CustomUser.Type.CLIENT
    objects = ClientManager()

    class Meta:
        proxy = True
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
