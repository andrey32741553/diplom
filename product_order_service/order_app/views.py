from django.contrib.auth.models import User
from django.db import transaction
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from order_app.models import Product, Order

from order_app.serializers import ProductSerializer, ProductDetailSerializer, OrderSerializer, UserSerializer, \
    RegistrationSerializer, OrderDetailSerializer


class TokenViewSet(ModelViewSet):

    queryset = Token.objects.all()
    serializer_class = LogOutSerializer

    @transaction.atomic
    #TODO
    def destroy(self, request, *args, **kwargs):
        deleting_user = request.user
        user_logged = Token.objects.get(user_id=deleting_user)
        user_logged.delete()
        return {"Token": f"{deleting_user}'s token deleted"}


class ProductViewSet(ModelViewSet):
    """ViewSet для продуктов """

    queryset = Product.objects.all()

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
        request_user = self.request.user
        if request_user.is_superuser:
            return super().retrieve(request, *args, **kwargs)
        else:
            instance = self.get_object()
            request_creator = instance
            if request_user != request_creator:
                raise ValidationError({"User-info": "Просматривать можно свои данные!"})
            return super().retrieve(request, *args, **kwargs)


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
        """Получение списка заказов админом. Для остальных только свои заказы"""
        queryset = Order.objects.all()
        user = self.request.user
        if not user.is_superuser and not user.is_staff:
            queryset = queryset.filter(user=user.id)
        return queryset

    def get_permissions(self):
        """Получение прав для действий"""
        if self.action == "create":
            return [IsAuthenticated()]
        return []

    @transaction.atomic
    def retrieve(self, request, *args, **kwargs):
        order_user = request.user
        instance = self.get_object()
        order_creator = instance.user
        if order_user.is_superuser:
            return super().retrieve(request, *args, **kwargs)
        elif order_user != order_creator:
            raise ValidationError({"Order": "Просматривать можно только свои заказы!"})
        return super().retrieve(request, *args, **kwargs)
