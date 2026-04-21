from django.db import models


class Item(models.Model):
    """
    Модель товаров
        - name: Наименование товара
        - description: Описание товара
        - price: Цена товара
    """

    name = models.CharField(max_length=60, verbose_name="Наименование")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")

    stock = models.PositiveIntegerField(default=0, verbose_name="Остаток")

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ("name",)

    def __str__(self):
        return f"{self.name} - {self.price}"


class Order(models.Model):
    """
    Модель заказов
        - created_at: Дата создания заказа
        - is_paid: Оплачен ли заказ, по умолчанию False
    """

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата создания заказа"
    )
    is_paid = models.BooleanField(default=False, verbose_name="Оплачен")

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ("-created_at",)

    def __str__(self):
        return f"Order №{self.pk} dated {self.created_at.strftime('%d.%m.%Y')}"

    def total_cost(self):
        return sum(item.subtotal_cost() for item in self.order_items.all())

    def total_quantity(self):
        return sum(item.quantity for item in self.order_items.all())


class OrderItem(models.Model):
    """
    Позиция в заказе
        - order: Заказ
        - item: Товар
        - quantity: Количество товара
        - price: Цена товара (для сохранения текущей стоимости при возможном изменении цены самого товара в будущем)
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="order_items",
        verbose_name="Заказ",
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="order_items",
        verbose_name="Товар",
    )

    quantity = models.PositiveIntegerField(default=0, verbose_name="Количество")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")

    class Meta:
        verbose_name = "Позиция"
        verbose_name_plural = "Позиции"
        constraints = [
            models.UniqueConstraint(
                fields=["item", "order"],
                name="unique_item_order",
            ),
        ]

    def __str__(self):
        return f"{self.item.name} in order №{self.order.pk}"

    def subtotal_cost(self):
        return self.price * self.quantity
