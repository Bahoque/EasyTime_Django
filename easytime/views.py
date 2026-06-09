from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from usuarios.models import User 
from agendamiento.models import Cita
from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import ExtractHour

# NOTA: Asegúrate de que este import coincida con el nombre real de tu modelo de ventas/productos
# Si no manejas ventas todavía, puedes comentar las líneas relacionadas al producto_top.
# from inventario.models import ProductoVendido 

# 🔹 CORRECCIÓN DE SEGURIDAD: Cambiado de lambda u: u.is_staff a lambda u: u.is_superuser
# Esto garantiza que SOLO el superusuario pueda acceder a este panel de métricas.
@user_passes_test(lambda u: u.is_superuser)
def dashboard_admin(request):
    # 1. Obtener rango del mes actual para los filtros
    ahora = timezone.now()
    mes_actual = ahora.month
    ano_actual = ahora.year

    # 2. Métricas básicas que ya tenías
    total_usuarios = User.objects.count()
    total_citas = Cita.objects.count()
    citas_hoy = Cita.objects.filter(fecha_hora__date=ahora.date()).count()
    proximas_citas = Cita.objects.filter(fecha_hora__gte=ahora).order_by('fecha_hora')[:5]
    ultimos_usuarios = User.objects.all().order_by('-date_joined')[:5]

    # 3. MÉTRICA: Servicio más escogido del mes
    servicio_top = (
        Cita.objects.filter(fecha_hora__month=mes_actual, fecha_hora__year=ano_actual)
        .values('servicio__nombre') 
        .annotate(total=Count('id'))
        .order_by('-total')
        .first()
    )

    # 4. MÉTRICA: Horario en que más citas salen (Hora Pico del mes)
    hora_pico_query = (
        Cita.objects.filter(fecha_hora__month=mes_actual, fecha_hora__year=ano_actual)
        .annotate(hora=ExtractHour('fecha_hora'))
        .values('hora')
        .annotate(total_citas=Count('id'))
        .order_by('-total_citas')
        .first()
    )

    # Formatear la hora militar (ej: 14) a un formato más comercial (02:00 PM)
    hora_formateada = None
    if hora_pico_query:
        h = hora_pico_query['hora']
        periodo = "PM" if h >= 12 else "AM"
        h_12 = h - 12 if h > 12 else (12 if h == 0 else h)
        hora_formateada = f"{h_12:02d}:00 {periodo}"

    # 5. MÉTRICA: Producto más vendido (Descomentar cuando tengas el modelo conectado)
    producto_top = None
    """
    producto_top = (
        ProductoVendido.objects.filter(fecha_venta__month=mes_actual, fecha_venta__year=ano_actual)
        .values('producto__nombre')
        .annotate(total_vendido=Count('id'))
        .order_by('-total_vendido')
        .first()
    )
    """

    context = {
        'total_usuarios': total_usuarios,
        'total_citas': total_citas,
        'citas_hoy': citas_hoy,
        'proximas_citas': proximas_citas,
        'ultimos_usuarios': ultimos_usuarios,
        
        # Nuevas variables de métricas
        'servicio_top': servicio_top,
        'hora_pico': hora_formateada,
        'total_citas_hora': hora_pico_query['total_citas'] if hora_pico_query else 0,
        'producto_top': producto_top,
        'mes_nombre': ahora.strftime('%B').capitalize(),
    }
    return render(request, 'dashboard.html', context)

def home(request):
    return render(request, 'home.html')

@login_required
def gestion_citas(request):
    from usuarios.views import es_admin
    if not es_admin(request.user):
        return redirect('home')
    citas = Cita.objects.all().order_by('-fecha_hora')
    return render(request, 'gestion_citas.html', {'citas': citas})