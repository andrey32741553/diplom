from django.db import models
from django.contrib.auth.models import User


class OrderStatusChoices(models.TextChoices):
    """Статусы заказа"""

    NEW = "NEW", "Новый"
    IN_PROGRESS = "IN_PROGRESS", "Выполняется"
    DONE = "DONE", "Готов"
    CANCELLED = "CANCELLED", "Отменён"


class Price(models.Model):
    """ Цены на продукты от разных поставщиков """

    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='price')
    provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='price')
    price = models.FloatField("Цена", default=0.00)

    def __str__(self):
        return "Цена на {} {} в {}(ом; е).".format(self.product.name, self.price, self.provider.username)

    class Meta:
        verbose_name = "Наименование"
        verbose_name_plural = "Наименования"


class Product(models.Model):
    """ Модель товаров """

    name = models.CharField("Название", max_length=50)
    description = models.TextField("Описание", default='')
    category = models.ForeignKey('Category', verbose_name='Категория', related_name='products', blank=True,
                                 on_delete=models.CASCADE)
    providers_info = models.ManyToManyField(User, related_name='products', through="Price")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"


class Category(models.Model):
    """ Модель категорий """

    name = models.CharField(max_length=40, verbose_name='Название')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = "Список категорий"
        ordering = ('-name',)

    def __str__(self):
        return self.name


class Order(models.Model):
    """ Модель заказов """

    user = models.ForeignKey(
        User,
        verbose_name="Пользователь",
        on_delete=models.CASCADE,
        related_name="order"
    )
    status = models.TextField(
        OrderStatusChoices.choices,
        default=OrderStatusChoices.NEW
    )
    products_list = models.ManyToManyField(Product, related_name='order', through='Position')
    count = models.PositiveIntegerField(editable=False)
    total = models.FloatField(editable=False)

    def __str__(self):
        return "User: У пользователя {} {} единиц товара в заказе на сумму {}".format(self.user, self.count, self.total)

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"


class Position(models.Model):
    """ Позиции товаров """

    provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='position')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='position')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='position')
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return "Позиция содержит {} {}(шт).".format(self.quantity, self.product.name)

    class Meta:
        verbose_name = "Наименование"
        verbose_name_plural = "Наименования"
