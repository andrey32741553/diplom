import os

import pytest
from django.contrib.auth.models import User
from django.core.files import File
from django.urls import reverse

from rest_framework.authtoken.models import Token
from rest_framework.status import HTTP_201_CREATED
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate

from order_app.models import Product
from order_app.views import ProductViewSet, OrderViewSet


@pytest.fixture
def authenticated_client(django_user_model):
    username = "foo"
    password = "bar"
    user = django_user_model.objects.create_user(username=username, password=password, email=os.getenv('MY_EMAIL'))
    token = Token.objects.create(user=user)
    token.save()
    return user, token


@pytest.fixture
def provider(django_user_model):
    user = django_user_model.objects.create_user(username='Связной', password='Связной', email=os.getenv('MY_EMAIL'),
                                                 is_staff=True)
    token = Token.objects.create(user=user)
    token.save()
    return user, token


@pytest.fixture()
@pytest.mark.django_db
def import_file_with_products(provider):
    url = "api/v1/products"
    data = File(open('shop1.yaml'))
    factory = APIRequestFactory()
    view = ProductViewSet.as_view({'post': 'create'})
    request = factory.post(url, {"file": data},
                           format='multipart',
                           content_disposition="attachment; filename=shop1.yaml",
                           HTTP_AUTHORIZATION=f'Token {provider[1]}')
    force_authenticate(request, user=provider[0], token=provider[1])
    view(request)


@pytest.fixture()
@pytest.mark.django_db
def create_order_by_authenticated_user(authenticated_client, import_file_with_products):
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