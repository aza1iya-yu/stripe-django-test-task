import stripe
from django.conf import settings
from django.core.validators import MaxValueValidator
from django.db import models

stripe.api_key = settings.STRIPE_SECRET_KEY


class Discount(models.Model):
    """
    Модель скидок
        - name: Наименование скидки
        - amount: Размер скидки в процентах
        - code: Код для клиента
        - stripe_coupon_id: ID купона
        - stripe_promotion_code_id: ID промокода
    """

    name = models.CharField(max_length=40, verbose_name="Наименование")
    amount = models.PositiveIntegerField(
        default=0,
        verbose_name="Скидка, %",
        validators=[MaxValueValidator(100)],
    )
    code = models.CharField(max_length=100, verbose_name="Код для клиента")

    stripe_coupon_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="ID купона Stripe",
    )
    stripe_promotion_code_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="ID промокода Stripe",
    )

    class Meta:
        verbose_name = "Скидка"
        verbose_name_plural = "Скидки"

    def __str__(self):
        return f"{self.code} -{self.amount}%"

    def get_stripe_discount_dict(self):
        return {"coupon": self.stripe_coupon_id}

    def save(self, *args, **kwargs):
        if not self.stripe_coupon_id:
            coupon = stripe.Coupon.create(
                name=self.name,
                percent_off=self.amount,
            )
            self.stripe_coupon_id = coupon.id

        if not self.stripe_promotion_code_id:
            promotion_code = stripe.PromotionCode.create(
                promotion={"type": "coupon", "coupon": coupon.id},
                code=self.code,
            )
            self.stripe_promotion_code_id = promotion_code.id

        return super().save(*args, **kwargs)


class Tax(models.Model):
    """
    Модель налогов
        - name: Наименование налога
        - rate: Размер налога
        - stripe_tax_rate_id: ID налога
    """

    name = models.CharField(max_length=50, verbose_name="Наименование")
    rate = models.PositiveIntegerField(
        default=0,
        verbose_name="Налог, %",
        validators=[MaxValueValidator(100)],
    )

    stripe_tax_rate_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="ID налога Stripe",
    )

    class Meta:
        verbose_name = "Налог"
        verbose_name_plural = "Налоги"

    def __str__(self):
        return f"{self.name} -{self.rate}%"

    def get_stripe_tax_rate_dict(self):
        return {"tax_rate": [self.stripe_tax_rate_id]}

    def save(self, *args, **kwargs):
        if not self.stripe_tax_rate_id:
            currency = self.items.currency
            api_key = settings.STRIPE_KEYS[currency]["secret"]

            tax_rate = stripe.TaxRate.create(
                api_key=api_key,
                display_name=self.name,
                percentage=self.rate,
                inclusive=False,
            )
            self.stripe_tax_rate_id = tax_rate.id
        return super().save(*args, **kwargs)


class Item(models.Model):
    """
    Модель товаров
        - name: Наименование товара
        - description: Описание товара
        - price: Цена товара в выбранной валюте
        - stock: Остаток товара
        - tax: Налог
    """

    class CurrencyChoices(models.TextChoices):
        USD = "usd", "USD"
        EUR = "eur", "EUR"

    name = models.CharField(max_length=60, verbose_name="Наименование")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")

    currency = models.CharField(
        max_length=3,
        choices=CurrencyChoices.choices,
        default=CurrencyChoices.USD,
        verbose_name="Валюта,",
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")

    stock = models.PositiveIntegerField(default=0, verbose_name="Остаток")

    tax = models.ForeignKey(
        Tax,
        on_delete=models.SET_NULL,
        related_name="items",
        blank=True,
        null=True,
    )

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
        - discount: Скидка
    """

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата создания заказа"
    )
    is_paid = models.BooleanField(default=False, verbose_name="Оплачен")

    discount = models.ForeignKey(
        Discount,
        on_delete=models.SET_NULL,
        related_name="orders",
        blank=True,
        null=True,
    )

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
