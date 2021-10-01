from django.contrib import admin
from django.urls import path, include
# from .spectacular import urlpatterns as doc_urls
from rest_framework import routers

from order_app.views import ProductViewSet, OrderViewSet
from .yasg import urlpatterns as doc_urls


router = routers.DefaultRouter()
router.register("products", ProductViewSet, basename="products")
router.register("orders", OrderViewSet, basename="orders")


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('order_app.urls')),
    path('api/v1/', include(router.urls)),
    path('api/v1/auth/', include('rest_framework_social_oauth2.urls')),
    path('api/v1/auth/', include('djoser.urls')),
    path('api/v1/auth/', include('djoser.urls.authtoken'))
]

urlpatterns += doc_urls
