from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from usuarios.models import User 
from agendamiento.models import Cita
from inventario.models import DetalleVenta
from django.utils import timezone
from django.db.models import Count, Sum
from django.db.models.functions import ExtractHour
import locale

def es_admin_o_superuser(user):
    return user.is_authenticated and (user.is_superuser or getattr(user, 'rol', None) == 'ADMIN')

@user_passes_test(es_admin_o_superuser, login_url='home')
def dashboard_admin(request):
    ahora = timezone.now()
    mes_actual = ahora.month
    ano_actual = ahora.year

    MESES_ES = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }

    total_usuarios = User.objects.count()
    total_citas = Cita.objects.count()
    citas_hoy = Cita.objects.filter(fecha_hora__date=ahora.date()).count()
    proximas_citas = Cita.objects.filter(fecha_hora__gte=ahora).order_by('fecha_hora')[:5]
    ultimos_usuarios = User.objects.all().order_by('-date_joined')[:5]

    servicio_top = (
        Cita.objects.filter(fecha_hora__month=mes_actual, fecha_hora__year=ano_actual)
        .values('servicio__nombre') 
        .annotate(total=Count('id'))
        .order_by('-total')
        .first()
    )

    hora_pico_query = (
        Cita.objects.filter(fecha_hora__month=mes_actual, fecha_hora__year=ano_actual)
        .annotate(hora=ExtractHour('fecha_hora'))
        .values('hora')
        .annotate(total_citas=Count('id'))
        .order_by('-total_citas')
        .first()
    )

    hora_formateada = None
    if hora_pico_query:
        h = hora_pico_query['hora']
        periodo = "PM" if h >= 12 else "AM"
        h_12 = h - 12 if h > 12 else (12 if h == 0 else h)
        hora_formateada = f"{h_12:02d}:00 {periodo}"

    producto_top = (
        DetalleVenta.objects.filter(
            venta__fecha_venta__month=mes_actual,
            venta__fecha_venta__year=ano_actual,
            venta__pagado=True
        )
        .values('producto__nombre')
        .annotate(total_vendido=Sum('cantidad'))
        .order_by('-total_vendido')
        .first()
    )

    estados_citas = (
        Cita.objects.filter(fecha_hora__month=mes_actual, fecha_hora__year=ano_actual)
        .values('estado')
        .annotate(total=Count('id'))
    )
    labels_citas = [e['estado'] for e in estados_citas]
    data_citas = [e['total'] for e in estados_citas]

    productos_ventas = (
        DetalleVenta.objects.filter(
            venta__fecha_venta__month=mes_actual,
            venta__fecha_venta__year=ano_actual,
            venta__pagado=True
        )
        .values('producto__nombre')
        .annotate(total_vendido=Sum('cantidad'))
        .order_by('-total_vendido')[:5]
    )
    labels_productos = [p['producto__nombre'] for p in productos_ventas]
    data_productos = [p['total_vendido'] for p in productos_ventas]

    context = {
        'total_usuarios': total_usuarios,
        'total_citas': total_citas,
        'citas_hoy': citas_hoy,
        'proximas_citas': proximas_citas,
        'ultimos_usuarios': ultimos_usuarios,
        'servicio_top': servicio_top,
        'hora_pico': hora_formateada,
        'total_citas_hora': hora_pico_query['total_citas'] if hora_pico_query else 0,
        'producto_top': producto_top,
        'mes_nombre': MESES_ES[mes_actual],
        'labels_citas': labels_citas,
        'data_citas': data_citas,
        'labels_productos': labels_productos,
        'data_productos': data_productos,
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