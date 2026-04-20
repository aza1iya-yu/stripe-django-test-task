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

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ("name",)

    def __str__(self):
        return f"{self.name} - {self.price}"
