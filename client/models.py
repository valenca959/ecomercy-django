from django.db import models

from authentication.models import CustomUser

class ClientManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(type=CustomUser.Type.CLIENT)
    
class Client(CustomUser):
    base_type = CustomUser.Type.CLIENT
    object = ClientManager()
    
    class Meta:
        proxy = True