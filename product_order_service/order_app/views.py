import bios

from django.contrib.auth.models import User
from django.db import transaction, IntegrityError
from django.http import JsonResponse

from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from order_app.email_sender import cancelled_status_message, changed_status_message
from order_app.models import Product, Order, Price, Category
from order_app.serializers import ProductSerializer, ProductDetailSerializer, OrderSerializer, UserSerializer, \
    RegistrationSerializer, OrderDetailSerializer, CategorySerializer


class ProductViewSet(ModelViewSet):
    """ViewSet для продуктов """

    queryset = Product.objects.filter(providers_info__is_active=True)

    def get_serializer_class(self):
        if self.action in ["list", "create"]:
            return ProductSerializer
        elif self.action in ["retrieve", "update"]:
            return ProductDetailSerializer

    def get_permissions(self):
        """Получение прав для действий"""
        if self.action in ["create", "update"]:
            return [IsAdminUser()]
        return []

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """ Метод импорта файла yaml """
        up_file = request.FILES['file']
        my_dict = bios.read(up_file.name, file_type='yaml')
        provider = my_dict['shop'].encode('cp1251').decode('utf-8')
        provider = User.objects.get(username=provider)

        if request.user.is_staff and str(request.user) == provider.username:

            for item in my_dict['goods']:
                description_list = []
                product = item['name'].encode('cp1251').decode('utf-8')
                category = item['category']
                price = item['price']
                description = item['parameters']

                for key, value in description.items():
                    key = key.encode('cp1251').decode('utf-8')
                    if type(value) == str:
                        value = value.encode('cp1251').decode('utf-8')
                    else:
                        value = value
                    description_dict = {key: value}
                    description_list.append(description_dict)

                try:
                    product_existence = Product.objects.get(name=product)

                    price_info = Price.objects.get(product_id=product_existence.id, provider_id=provider.id)
                    product_existence.name = product
                    product_existence.description = description_list
                    product_existence.category.id = category
                    product_existence.save()
                    price_info.product_id = product_existence.id
                    price_info.provider_id = request.user.id
                    price_info.price = price
                    price_info.save()

                    for data in my_dict['categories']:
                        if data['id'] not in Category.objects.values_list('id', flat=True):
                            Category.objects.create(id=data['id'], name=data['name'].encode('cp1251').decode('utf-8'))

                except (Product.DoesNotExist, IntegrityError):
                    product = Product.objects.create(name=product, category_id=category, description=description_list)
                    Price.objects.create(product_id=product.id, provider_id=provider.id, price=price)
            return Response(data={"file": f"{up_file.name} uploaded"})

        else:
            return Response(data={"User": f"Пользователь {request.user} не является поставщиком, либо неправильно "
                                          "указано имя поставщика в прайсе"})


class UserViewSet(ModelViewSet):
    """ ViewSet для данных пользователя """

    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action in ["list", "retrieve", "update"]:
            return UserSerializer

    def get_permissions(self):
        """Получение прав для действий"""
        if self.action == "update":
            return [IsAdminUser()]
        return []

    @transaction.atomic
    def retrieve(self, request, *args, **kwargs):
        """ Метод исключает возможность просмотреть чужие данные """
        request_user = self.request.user
        if request_user.is_superuser:
            return super().retrieve(request, *args, **kwargs)
        else:
            instance = self.get_object()
            request_creator = instance
            if request_user != request_creator:
                return Response(data={"User-info": "Просматривать можно свои данные!"})
            return super().retrieve(request, *args, **kwargs)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        """ Метод для смены статуса поставщика (принимает/не принимает заказы) """
        instance = self.get_object()
        user = request.user
        serializer = UserSerializer(instance, data=request.data, partial=True)
        if user.is_staff:
            if serializer.is_valid():
                serializer.save()
            return JsonResponse(data=serializer.data)
        else:
            return Response(data={"User": "Менять статус могут только поставщики!"})


class RegistrationViewSet(ModelViewSet):
    """ ViewSet для регистрации """

    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return RegistrationSerializer


class OrderViewSet(ModelViewSet):
    """ViewSet для заказов"""

    queryset = Order.objects.all()

    def get_serializer_class(self):
        if self.action in ["list", "create"]:
            return OrderSerializer
        elif self.action in ["retrieve", "update"]:
            return OrderDetailSerializer

    def get_queryset(self):
        """ Метод, который делает запрос и выводит для поставщика только то, что у него заказали, а для покупателей
         только их заказы"""
        user = self.request.user
        if user.is_staff:
            queryset = Order.objects.filter(position__provider=user.id)
        elif user.is_authenticated:
            queryset = Order.objects.filter(user=user.id)
        return queryset

    def get_permissions(self):
        """Получение прав для действий"""
        if self.action == "create":
            return [IsAuthenticated()]
        return []

    @transaction.atomic
    def retrieve(self, request, *args, **kwargs):
        """ Метод, который не позволяет просматривать чужие заказы """
        order_user = request.user
        instance = self.get_object()
        order_creator = instance.user
        if order_user.is_superuser:
            return super().retrieve(request, *args, **kwargs)
        elif order_user != order_creator:
            return Response(data={"Order": "Просматривать можно только свои заказы!"})
        return super().retrieve(request, *args, **kwargs)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        """ Метод, который позволяет удалить записи со статусом "отменён" и "выполнен" """
        if request.user.is_staff:
            request_user = request.user
            instance = self.get_object()
            provider = instance.user
            status = instance.status
            if request_user != provider or status != 'CANCELLED' or status != 'DONE':
                return Response(data={"Order": "Удалять можно только свои записи и со статусом 'Отменён', "
                                               "либо 'Выполнен'!"})
            return super().destroy(request, *args, **kwargs)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        """ Метод, позволяющий покупателю менять статус на "отменён" и отправить сообщение поставщику об отмене.
         Поставщик может ставить любой статус и отправить письмо о смене статуса покупателю"""
        instance = self.get_object()
        user = request.user
        serializer = OrderSerializer(instance, data=request.data, partial=True)
        if user.is_staff:
            if serializer.is_valid():
                serializer.save()
                changed_status_message(instance, user)
            return JsonResponse(data=serializer.data)
        elif not user.is_superuser and user.is_authenticated:
            if request.data['status'] != 'CANCELLED':
                return Response(data={"Order": "Пользователь может менять статус только на 'Отменён'!"})
            else:
                if serializer.is_valid():
                    serializer.save()
                    cancelled_status_message(instance, user)
                return JsonResponse(data=serializer.data)


class CategoryView(ModelViewSet):
    """ Класс для просмотра категорий """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
