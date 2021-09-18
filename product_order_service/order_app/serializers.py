from rest_framework.authtoken.models import Token

from order_app.email_sender import registration_confirm, order_confirm
import asyncio
from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from order_app.models import Product, Order, Position, Price


class UserSerializer(serializers.ModelSerializer):
    """ Сериализатор информации о поставщике """

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_staff')


class RegistrationSerializer(serializers.ModelSerializer):
    """ Сериализатор для регистрации пользователей """

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'is_staff')
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        username = validated_data['username']
        email = validated_data['email']
        password = validated_data['password']
        if username is None:
            raise ValidationError({"username": "Введите имя пользователя!"})
        elif email is None:
            raise ValidationError({"email": "Введите адрес электронной почты!"})
        elif password is None:
            raise ValidationError({"password": "Введите пароль!"})
        emails = [(username, email)]
        asyncio.run(registration_confirm(emails))
        return User.objects.create_user(**validated_data)
    
   
class LogOutSerializer(serializers.ModelSerializer):
    """ Сериализатор для выхода пользователя """

    class Meta:
        model = Token
        fields = ('key',)

    
class PriceSerializer(serializers.ModelSerializer):
    """ Сериализатор цен поставщиков """

    class Meta:
        model = Price
        fields = ('provider', 'price')


class PositionSerializer(serializers.ModelSerializer):
    """ Сериализатор списка позиций """

    class Meta:
        model = Position
        fields = ("provider", "product", "quantity")


class ProductSerializer(serializers.ModelSerializer):
    """Serializer для списка продуктов."""

    providers_info = PriceSerializer(many=True, source='price.all')

    class Meta:
        model = Product
        fields = '__all__'

    def create(self, validated_data):
        providers_list = []
        prices = validated_data.pop(
            'price')
        product_info = super().create(validated_data)
        for price in prices.values():
            for item in price:
                providers_list.append(Price(product=product_info, provider=item['provider'], price=item['price']))
        product_info.save()
        Price.objects.bulk_create(providers_list)
        return product_info


class ProductDetailSerializer(serializers.ModelSerializer):
    """Serializer для каждого продукта"""

    providers_info = PriceSerializer(many=True, source='price.all')

    class Meta:
        model = Product
        fields = '__all__'

    def update(self, instance, validated_data):
        if self.context['request'].user.is_staff or self.context['request'].user.is_superuser:
            my_view = self.context['view']
            product_id = my_view.kwargs.get('pk')
            product_info = Price.objects.get(product=product_id)
            price_info = validated_data.pop('price')
            for value in price_info.values():
                for price in value:
                    product_info.price = price['price']
                    product_info.save()
            instance.description = validated_data.get('description', instance.description)
            instance.save()
            return instance
        else:
            raise ValidationError({"Products": "Поставщик может менять информацию только о своих товарах"})


class OrderSerializer(serializers.ModelSerializer):
    """ Сериализатор списка заказов """

    user = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True,
    )

    products_list = PositionSerializer(many=True, source='position.all')

    class Meta:
        model = Order
        fields = '__all__'

    def create(self, validated_data):
        validated_data['user'] = self.context["request"].user
        positions = validated_data.pop(
            'position')
        positions_objs = []
        validated_data['count'] = 0
        validated_data['total'] = 0
        order = super().create(validated_data)
        for position in positions.values():
            for item in position:
                price = Price.objects.get(product=item['product'].id, provider=item['provider']).price
                validated_data['total'] += price * item['quantity']
                validated_data['count'] += item['quantity']
                positions_objs.append(Position(quantity=item['quantity'],
                                               product=item['product'], order=order, provider=item['provider']))
        order.count = validated_data['count']
        order.total = validated_data['total']
        order.save()
        positions_list = Position.objects.bulk_create(positions_objs)
        order_confirm_for_email = (order, positions_list)
        asyncio.run(order_confirm(order_confirm_for_email))
        return order


class OrderDetailSerializer(serializers.ModelSerializer):
    """ Сериализатор конкретного заказа """

    user = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True,
    )

    products_list = PositionSerializer(many=True, source='position.all')

    class Meta:
        model = Order
        fields = '__all__'

    def update(self, instance, validated_data):
        my_view = self.context['view']
        order_id = my_view.kwargs.get('pk')
        positions = validated_data.pop(
            'position')
        positions_objs = []
        for position in positions.values():
            for item in position:
                price = Price.objects.get(product=item['product'].id, provider=item['provider']).price
                validated_data['total'] += price * item['quantity']
                validated_data['count'] += item['quantity']
                positions_objs.append(Position(quantity=item['quantity'],
                                               product=item['product'], order=order_id, provider=item['provider']))
        instance.count = validated_data.get('count', instance.count)
        instance.total = validated_data.get('total', instance.total)
        instance.save()
        Position.objects.bulk_update(positions_objs)
        return instance
