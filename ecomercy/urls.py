from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions, routers
from rest_framework_simplejwt.views import TokenBlacklistView, TokenRefreshView

from address.views import AddressViewSet
from authentication.views import LoginView, MeView, SellerViewSet, UserViewSet
from client.views import ClientViewSet
from authentication.web import RateLimitedLoginView, account, signup_client, signup_seller
from catalog import views as catalog_views
from ecomercy.views import home

schema_view = get_schema_view(
    openapi.Info(
        title="Ecomercy API",
        default_version='v1',
        description="API do e-commerce Ecomercy",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

router = routers.DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(r'clients', ClientViewSet, basename='clients')
router.register(r'sellers', SellerViewSet, basename='sellers')
router.register(r'address', AddressViewSet, basename='address')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # Telas (templates)
    path('', home, name='home'),
    path('login/', RateLimitedLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('cadastro/cliente/', signup_client, name='signup-client'),
    path('cadastro/vendedor/', signup_seller, name='signup-seller'),
    path('conta/', account, name='account'),

    # Loja e painel do vendedor
    path('loja/', catalog_views.store_list, name='store'),
    path('loja/produto/<slug:slug>/', catalog_views.product_detail, name='product-detail'),
    path('vendedor/produtos/', catalog_views.seller_product_list, name='seller-products'),
    path('vendedor/produtos/novo/', catalog_views.seller_product_create, name='seller-product-create'),
    path('vendedor/produtos/<int:pk>/editar/', catalog_views.seller_product_edit, name='seller-product-edit'),

    # Redefinição de senha por email
    path('senha/esqueci/',
         auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'),
         name='password_reset'),
    path('senha/enviada/',
         auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'),
         name='password_reset_done'),
    path('senha/redefinir/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('senha/concluida/',
         auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'),
         name='password_reset_complete'),

    # API
    path('api/', include(router.urls)),

    path('api/auth/login/', LoginView.as_view(), name='auth-login'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='auth-refresh'),
    path('api/auth/logout/', TokenBlacklistView.as_view(), name='auth-logout'),
    path('api/auth/me/', MeView.as_view(), name='auth-me'),
]

# Serve as imagens enviadas em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
