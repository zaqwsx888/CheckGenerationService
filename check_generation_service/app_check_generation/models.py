from django.db import models
from django.core.validators import FileExtensionValidator


class Printer(models.Model):
    """Модель принтера."""
    CHECK_TYPE = (
        ('kitchen', 'Кухня'),
        ('client', 'Клиент'),
    )

    name = models.CharField(
        max_length=255,
        verbose_name='Название принтера'
    )
    api_key = models.CharField(
        max_length=255,
        verbose_name='ключ доступа к API'
    )
    check_type = models.CharField(
        choices=CHECK_TYPE,
        max_length=7,
        default='kitchen',
        verbose_name='Тип чека, которые печатает принтер'
    )
    point_id = models.IntegerField(
        db_index=True,
        null=False,
        blank=False,
        verbose_name='Точки, к которым привязаны принтеры'
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Принтер'
        verbose_name_plural = 'Принтеры'


class Check(models.Model):
    """Модель чека."""
    CHECK_TYPE = (
        ('kitchen', 'Кухня'),
        ('client', 'Клиент'),
    )
    STATUS = (
        ('new', 'Новый'),
        ('rendered', 'Отображенный'),
        ('printed', 'Распечатанный'),
    )

    printer = models.ForeignKey(
        Printer,
        on_delete=models.CASCADE,
        related_name='check_model',
        verbose_name='Принтер'
    )
    type = models.CharField(
        choices=CHECK_TYPE,
        max_length=7,
        default='kitchen',
        verbose_name='Тип чека'
    )
    order = models.JSONField(verbose_name='Информация о заказе')
    status = models.CharField(
        choices=STATUS,
        max_length=8,
        default='new',
        verbose_name='Статус чека'
    )
    pdf_file = models.FileField(
        upload_to='pdf/',
        verbose_name='Ссылка на созданный PDF-файл',
        blank=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf', ]),
        ]
    )

    class Meta:
        verbose_name = 'Чек'
        verbose_name_plural = 'Чеки'
