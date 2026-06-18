from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views
from agendamiento import views as agend_views
from inventario import views as inv_views
from pqrs import views as pqrs_views
from usuarios import views as usuarios_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('gestion-citas/', views.gestion_citas, name='gestion_citas'),
    path('dashboard/', views.dashboard_admin, name='dashboard'), 
    
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/logout/', usuarios_views.custom_logout, name='logout'),
    path('registrarse/', usuarios_views.registro_cliente, name='registro'),
    path('perfil/', usuarios_views.mi_perfil, name='mi_perfil'),
    
    path('servicios/', agend_views.lista_servicios, name='servicios'),
    path('agendar/', agend_views.agendar_cita, name='agendar'),
    path('agendar/<int:servicio_id>/', agend_views.agendar_cita, name='agendar_con_servicio'),
    path('mis-citas/', agend_views.mis_citas, name='mis_citas'),
    
    path('productos/', inv_views.catalogo_productos, name='catalogo_productos'),
    path('productos/crear/', inv_views.crear_producto, name='crear_producto'),
    path('productos/<int:producto_id>/editar/', inv_views.editar_producto, name='editar_producto'),
    path('carrito/', inv_views.ver_carrito, name='ver_carrito'),
    path('comprar/<int:producto_id>/', inv_views.agregar_carrito, name='agregar_carrito'),
    path('eliminar-del-carrito/<int:item_id>/', inv_views.eliminar_del_carrito, name='eliminar_del_carrito'),
    path('pago/<int:venta_id>/', inv_views.pasarela_pago, name='pasarela_pago'),
    path('confirmar-pago/<int:venta_id>/', inv_views.finalizar_compra, name='finalizar_compra'),
    
    path('pqrs/', pqrs_views.mis_pqrs, name='mis_pqrs'),

    path('admin-usuarios/', usuarios_views.lista_usuarios, name='lista_usuarios'),
    path('admin-usuarios/crear/', usuarios_views.crear_usuario, name='crear_usuario'),
    path('admin-usuarios/editar/<int:pk>/', usuarios_views.editar_usuario, name='editar_usuario'),
    path('admin-usuarios/eliminar/<int:pk>/', usuarios_views.eliminar_usuario, name='eliminar_usuario'),
    path('admin-usuarios/reporte-pdf/', usuarios_views.generar_pdf_usuarios, name='generar_pdf_usuarios'),
    path('admin-usuarios/reporte-excel/', usuarios_views.generar_excel_usuarios, name='generar_excel_usuarios'),

    path('agendamiento/', include('agendamiento.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)