from order_app.email_sender import send_message_reg_confirm, order_confirm, message_to_provider

from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from order_app.models import Product, Order, Position, Price, Category


class UserSerializer(serializers.ModelSerializer):
    """ Сериализатор информации о поставщике """

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_staff', 'is_active')


class RegistrationSerializer(serializers.ModelSerializer):
    """ Сериализатор для регистрации пользователей """

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'is_staff')
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        """ Метод регистрирующий пользователя и отправляющий сообщение о регистрации """
        username = validated_data['username']
        email = validated_data['email']
        password = validated_data['password']
        if username is None:
            raise ValidationError({"username": "Введите имя пользователя!"})
        elif email is None:
            raise ValidationError({"email": "Введите адрес электронной почты!"})
        elif password is None:
            raise ValidationError({"password": "Введите пароль!"})
        emails = (username, email)
        send_message_reg_confirm(emails)
        return User.objects.create_user(**validated_data)


class PriceSerializer(serializers.ModelSerializer):
    """ Сериализатор цен поставщиков """

    provider = UserSerializer(read_only=True)

    class Meta:
        model = Price
        fields = ('provider', 'price')


class PositionSerializer(serializers.ModelSerializer):
    """ Сериализатор списка позиций """

    class Meta:
        model = Position
        fields = '__all__'
        read_only_fields = ('order',)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name',)
        read_only_fields = ('id',)


class ProductSerializer(serializers.ModelSerializer):
    """Serializer для списка продуктов."""

    providers_info = PriceSerializer(many=True, source='price.all')
    category = serializers.StringRelatedField()

    class Meta:
        model = Product
        fields = '__all__'


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
        """ Метод создания заказов с отправкой сообщения покупателю с подтверждением и поставщикам о новом заказе """
        validated_data['user'] = self.context["request"].user
        positions = validated_data.pop(
            'position')
        positions_objs = []
        validated_data['count'] = 0
        validated_data['total'] = 0
        order = super().create(validated_data)
        for position in positions.values():
            for item in position:
                provider = User.objects.get(username=item['provider'])
                if not provider.is_active:
                    raise ValidationError({"Provider": f"Поставщик {str(provider).capitalize()} не принимает заказы."})
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
        order_confirm(order_confirm_for_email)
        message_to_provider(order_confirm_for_email)
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
        """ Метод позволяющий внести изменения в заказ """
        user = self.context['request'].user
        if not user.is_staff and user.is_authenticated:
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
            if validated_data['status'] == 'CANCELLED':
                instance.status = validated_data.get('status', instance.status)
                instance.count = validated_data.get('count', instance.count)
                instance.total = validated_data.get('total', instance.total)
                instance.save()
                Position.objects.bulk_update(positions_objs)
                return instance
            else:
                raise ValidationError({"Order": "Авторизованный пользователь может менять статус только на 'Отменён'"})
        elif user.is_staff:
            instance.status = validated_data.get('status', instance.status)
            instance.save()
            return instance
        else:
            raise ValidationError({"Order": "Менять статус заказа может только админ"})
