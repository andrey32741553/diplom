import pytest

from django.core.files import File
from django.urls import reverse

from rest_framework.status import HTTP_200_OK
from rest_framework.test import APIRequestFactory, force_authenticate

from order_app.models import Product
from order_app.views import ProductViewSet


@pytest.mark.django_db
def test_import_file(provider):
    """ Тест импорта файла  """
    url = reverse("products-list")
    data = File(open('shop1.yaml'))
    factory = APIRequestFactory()
    view = ProductViewSet.as_view({'post': 'create'})
    request = factory.post(url, {"file": data},
                           format='multipart',
                           content_disposition="attachment; filename=shop1.yaml",
                           HTTP_AUTHORIZATION=f'Token {provider[1]}')
    force_authenticate(request, user=provider[0], token=provider[1])
    response = view(request)
    assert response.status_code == HTTP_200_OK


@pytest.mark.django_db
def test_get_list_of_orders_by_authenticated_client(import_file_with_products):
    """ Тест получения списка продуктов любым пользователем """
    import_file_with_products
    url = reverse("products-list")
    factory = APIRequestFactory()
    view = ProductViewSet.as_view({'get': 'list'})
    request = factory.get(url)
    response = view(request)
    assert response.status_code == HTTP_200_OK


@pytest.mark.django_db
def test_get_list_of_orders_by_authenticated_client(import_file_with_products):
    """ Тест получения информации о конкретном продукте любым пользователем """
    import_file_with_products
    product = Product.objects.get(name='Смартфон Apple iPhone XS Max 512GB (золотистый)')
    url = reverse("products-detail", args=(product.id,))
    factory = APIRequestFactory()
    view = ProductViewSet.as_view({'get': 'retrieve'})
    request = factory.get(url)
    response = view(request, pk=product.id)
    assert response.status_code == HTTP_200_OK
