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
]
