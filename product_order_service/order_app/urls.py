from django.urls import path

from rest_framework.urlpatterns import format_suffix_patterns

from order_app.views import ProductViewSet, UserViewSet, OrderViewSet, RegistrationViewSet, CategoryView

urlpatterns = format_suffix_patterns([
    path('products/', ProductViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('products/<int:pk>/', ProductViewSet.as_view({'get': 'retrieve', 'put': 'update'})),
    path('providers/', UserViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('orders/', OrderViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('orders/<int:pk>/', OrderViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update',
                                                   'delete': 'destroy'})),
    path('user-info/', UserViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('user-info/<int:pk>/', UserViewSet.as_view({'get': 'retrieve', 'delete': 'destroy', 'patch': 'partial_update'})),
    path('categories/', CategoryView.as_view({'get': 'list'})),
    path('registration/', RegistrationViewSet.as_view({'post': 'create'})),
])
