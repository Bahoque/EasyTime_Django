from django.urls import path
from . import views

app_name = 'agendamiento'

urlpatterns = [
    path('api/notificaciones/', views.obtener_notificaciones, name='obtener_notificaciones'),
    path('notificaciones/marcar-todas/', views.marcar_todas_leidas, name='marcar_todas_leidas'),
    path('notificacion/<int:notificacion_id>/detalle/', views.ver_notificacion_detalle, name='ver_notificacion_detalle'),
    path('notificaciones/todas/', views.ver_todas_las_notificaciones, name='ver_todas_las_notificaciones'),
    path('cita/<int:cita_id>/detalle/', views.detalle_cita, name='detalle_cita'),
    path('servicios/crear/', views.crear_servicio, name='crear_servicio'),
    path('servicios/<int:servicio_id>/editar/', views.editar_servicio, name='editar_servicio'),
    # Operarios
    path('operarios/', views.lista_operarios, name='lista_operarios'),
    path('operarios/crear/', views.crear_operario, name='crear_operario'),
    path('operarios/<int:operario_id>/editar/', views.editar_operario, name='editar_operario'),
    path('operarios/<int:operario_id>/toggle/', views.toggle_operario, name='toggle_operario'),
    path('api/operarios-disponibles/', views.operarios_disponibles, name='operarios_disponibles'),
    # Facturas
    path('factura/<int:factura_id>/', views.ver_factura, name='ver_factura'),
    path('factura/<int:factura_id>/pdf/', views.descargar_factura_pdf, name='descargar_factura_pdf'),
    path('pasarela-cita/<int:factura_id>/', views.pasarela_cita, name='pasarela_cita'),
]