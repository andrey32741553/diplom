import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT
from rest_framework.test import APIRequestFactory, force_authenticate

from order_app.models import Product, Order
from order_app.views import OrderViewSet


@pytest.mark.django_db
def test_create_order_by_authenticated_user(authenticated_client, import_file_with_products):
    """ Тест создания заказа авторизованным пользователем """
    import_file_with_products
    factory = APIRequestFactory()
    product = Product.objects.all()
    provider = User.objects.get(username="Связной")
    url = reverse("orders-list")
    order = {"products_list": [{
        "product": product[0].id,
        "provider": provider.id,
        "quantity": 2
    },
        {
            "product": product[1].id,
            "provider": provider.id,
            "quantity": 3
        }]
    }
    view = OrderViewSet.as_view({'post': 'create'})
    request = factory.post(url, order, format='json', HTTP_AUTHORIZATION=f'Token {authenticated_client[1]}')
    force_authenticate(request, user=authenticated_client[0], token=authenticated_client[1])
    response = view(request)
    assert response.status_code == HTTP_201_CREATED


def test_cancel_order(create_order_by_authenticated_user, authenticated_client):
    """ Тест отмены заказа авторизованным пользователем """
    factory = APIRequestFactory()
    user_order = Order.objects.get(user=authenticated_client[0])
    url = reverse('orders-detail', args=(user_order.id,))
    cancelled = {'status': 'CANCELLED'}
    view = OrderViewSet.as_view({'patch': 'partial_update'})
    change_status = factory.patch(url, cancelled, format='json', HTTP_AUTHORIZATION=f'Token {authenticated_client[1]}')
    force_authenticate(change_status, user=authenticated_client[0], token=authenticated_client[1])
    response = view(change_status, pk=user_order.id)
    assert response.status_code == HTTP_200_OK


@pytest.mark.django_db
def test_change_order_status_by_provider(create_order_by_authenticated_user, provider, authenticated_client):
    """ Тест изменения статуса заказа поставщиком на 'выполнен' c последующим удалением"""
    factory = APIRequestFactory()
    user_order = Order.objects.get(user=authenticated_client[0])
    url = f'api/v1/orders/{user_order}'
    new_status = {'status': 'DONE'}
    view = OrderViewSet.as_view({'patch': 'partial_update'})
    change_status = factory.patch(url, new_status, format='json', HTTP_AUTHORIZATION=f'Token {provider[1]}')
    force_authenticate(change_status, user=provider[0], token=provider[1])
    response = view(change_status, pk=user_order.id)
    assert response.status_code == HTTP_200_OK
    delete_order = factory.delete(url, format='json', HTTP_AUTHORIZATION=f'Token {provider[1]}')
    view = OrderViewSet.as_view({'delete': 'destroy'})
    resp = view(delete_order, pk=user_order.id)
    assert resp.status_code == HTTP_200_OK


@pytest.mark.django_db
def test_get_list_of_orders_by_authenticated_client(create_order_by_authenticated_user, authenticated_client):
    """ Тест получения списка заказов авторизованным пользователем """
    create_order_by_authenticated_user
    url = reverse("orders-list")
    factory = APIRequestFactory()
    view = OrderViewSet.as_view({'get': 'list'})
    request = factory.get(url)
    force_authenticate(request, user=authenticated_client[0], token=authenticated_client[1])
    response = view(request)
    assert response.status_code == HTTP_200_OK
