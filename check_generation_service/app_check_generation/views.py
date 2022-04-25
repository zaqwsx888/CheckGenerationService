import django_rq
from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import FileResponse

from .models import Check, Printer
from .serializers import (
    OrderSerializer, CheckSerializer, ApiKeySerializer, ApiKeyCheckIDSerializer
)


class OrdersAPIView(APIView):
    """Класс генерации pdf-файлов чеков для клиентов и для кухни."""
    @classmethod
    def post(cls, request, format=None):
        order = OrderSerializer(data=request.data)
        order.is_valid(raise_exception=True)
        order = order.data
        checks = Check.objects.filter(order=order)
        if checks:
            return Response(
                {'error': 'Чеки для данного заказа были ранее созданы'},
                status=400
            )
        printers = Printer.objects.filter(point_id=order['point_id'])
        kitchen_printer = printers.filter(check_type='kitchen').first()
        client_printer = printers.filter(check_type='client').first()
        if not (kitchen_printer and client_printer):
            return Response(
                {'error': 'На данной точке принтеры отсутствуют'},
                status=400
            )
        with transaction.atomic():
            kitchen_check = Check.objects.create(
                printer=kitchen_printer,
                type='kitchen',
                order=order,
                status='new',
            )
            client_check = Check.objects.create(
                printer=client_printer,
                type='client',
                order=order,
                status='new'
            )

        if kitchen_check and client_check:
            queue_1 = django_rq.get_queue('default')
            queue_1.enqueue(
                'app_check_generation.tasks.pdf_generation',
                order_data=order,
                check_type='kitchen_check'
            )
            queue_2 = django_rq.get_queue('default')
            queue_2.enqueue(
                'app_check_generation.tasks.pdf_generation',
                order_data=order,
                check_type='client_check'
            )
            return Response(
                {'ok': 'Чеки успешно созданы'}, status=200
            )
        return Response(
            {'error': 'Возникла ошибка при создании чеков'}, status=400
        )


class ChecksAPIView(APIView):
    """Класс передачи id сгенерированного чека по ключу api_key."""
    def get(self, request, format=None):
        data = ApiKeySerializer(data=request.data)
        data.is_valid(raise_exception=True)
        api_key = data.data.get('api_key')
        printer = Printer.objects.filter(api_key=api_key).first()
        if not printer:
            return Response(
                {'error': 'Ошибка авторизации'}, status=401
            )
        queryset = Check.objects.filter(printer=printer, status='rendered')
        return Response(
            {"checks": CheckSerializer(queryset, many=True).data}, status=200
        )


class CheckAPIView(APIView):
    """
    Класс передачи ссылки скачивания pdf файла по параметрам api_key и id чека.
    """
    def get(self, request, format=None):
        data = ApiKeyCheckIDSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        api_key = data.data.get('api_key')
        check_id = data.data.get('check_id')

        printer = Printer.objects.filter(api_key=api_key).first()
        if not printer:
            return Response(
                {'error': 'Ошибка авторизации'}, status=401
            )

        check = Check.objects.filter(pk=check_id, printer=printer).first()
        if not check:
            return Response(
                {'error': 'Данного чека не существует'},
                status=400
            )
        elif not check.status == 'rendered':
            return Response(
                {'error': 'Для данного чека не сгенерирован PDF-файл'},
                status=400
            )
        pdf_file = check.pdf_file.open()
        return FileResponse(pdf_file, content_type='application/pdf')
