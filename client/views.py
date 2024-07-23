from rest_framework import viewsets, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from client.models import Client
from client.serializers import ClientSerializer
from address.models import Address
from address.serializers import AddressSerializer

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.object.all()
    serializer_class = ClientSerializer
    
    
    def create(self, request, *args, **kwargs):
        validating_key = []
        user = request.data
        
        client_data = {
            "first_name": user.get('first_name'),
            "last_name": user.get('last_name'),
            "cpf": user.get('cpf'),
            "email": user.get('email'),
            "username": user.get('username'),
            "password": user.get('password'),
            "type": user.get('type'),
        }
        
        client_address_data = {
            "street": user.get('address.street'),
            "city": user.get('address.city'),
            "number": user.get('address.number'),
            "state": user.get('address.state'),
            "district": user.get('address.district'),
            "reference": user.get('address.reference')
            }

        for k, v in client_data.items():
            if v == '':
                validating_key.append(k)
                
        for k, v in client_address_data.items():
            if v == '':
                validating_key.append(k)
                
        if not validating_key:
            client = Client.objects.create(**client_data)
            instance = get_object_or_404(self.queryset, id=client.id)
            instance.set_password('password')
            instance.save()
            
            address = Address.objects.create(**client_address_data)
            address.save()
            instance.address = address
            instance.save()
        else:
            erro_dict={}
            for key in validating_key:
                erro_dict[key] = ' Campo obrigatório'
            
            return Response (erro_dict, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(
            ClientSerializer(
                instance, many=False).data, status=status.HTTP_200_OK)
        
    def update(self, request, *args, **kwargs):
        instance = get_object_or_404(self.queryset, id=kwargs.get('pk'))
        
        client_data = {
            "first_name": request.data.get('first_name', instance.first_name),
            "last_name": request.data.get('last_name', instance.last_name),
            "cpf": request.data.get('cpf', instance.cpf),
            "email": request.data.get('email', instance.email),
            "username": request.data.get('username', instance.username),
            "type": request.data.get('type', instance.type)
        }
        if request.data.get('password'):
            instance.set_password(request.data.get('password'))
            
        client_address_data = {
            "street": request.data.get(
                'address.street', instance.address.street),
            "city": request.data.get(
                'address.city', instance.address.city),
            "number": request.data.get(
                'address.number', instance.address.number),
            "state": request.data.get(
                'address.state', instance.address.state),
            "district":request.data.get(
                'address.district', instance.address.district),
            "reference": request.data.get(
                'address.reference', instance.address.reference)
            }

 
        client_serializer = self.get_serializer(instance, data=client_data)
        address_serializer = AddressSerializer(
            instance.address, data=client_address_data)


        if client_serializer.is_valid(raise_exception=True) :
            client_serializer.save()
        if address_serializer.is_valid(raise_exception=True):
            address_serializer.save()
                
        return Response(client_serializer.data, status=status.HTTP_200_OK)