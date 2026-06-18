from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import IntegrityError
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import Cita, Servicio, Notificacion 
from .forms import CitaForm, ServicioForm

def es_administrador(user):
    return user.is_authenticated and (user.is_staff or getattr(user, 'rol', None) in ['ADMIN'])

def lista_servicios(request):
    from usuarios.views import es_admin
    if request.user.is_authenticated and es_admin(request.user):
        servicios_list = Servicio.objects.all().order_by('nombre')
    else:
        servicios_list = Servicio.objects.filter(activo=True).order_by('nombre')
    paginator = Paginator(servicios_list, 6)
    page_number = request.GET.get('page')
    servicios = paginator.get_page(page_number)
    return render(request, 'servicios.html', {'servicios': servicios})

@login_required
def agendar_cita(request, servicio_id=None):
    servicio_seleccionado = None
    if servicio_id:
        servicio_seleccionado = get_object_or_404(Servicio, id=servicio_id)

    if request.method == 'POST':
        form = CitaForm(request.POST) 
        if form.is_valid():
            try:
                cita = form.save(commit=False)
                cita.usuario = request.user
                cita.save()
                messages.success(request, "¡Cita agendada con éxito!")
                return redirect('mis_citas')
            except IntegrityError: 
                messages.error(request, "Error: Esa fecha y hora ya están ocupadas.")
    else:
        initial_data = {'servicio': servicio_seleccionado} if servicio_seleccionado else {}
        form = CitaForm(initial=initial_data) 
            
    return render(request, 'agendar.html', {
        'form': form, 
        'servicio_seleccionado': servicio_seleccionado
    })

@login_required
def mis_citas(request):
    citas = Cita.objects.filter(usuario=request.user).order_by('-fecha_hora')
    return render(request, 'mis_citas.html', {'citas': citas})

@login_required
def obtener_notificaciones(request):
    es_admin_jefe = getattr(request.user, 'rol', None) in ['ADMIN', 'JEFE']
    if request.user.is_staff or es_admin_jefe:
        notificaciones = Notificacion.objects.filter(
            usuario=request.user, 
            leida=False
        ).order_by('-fecha')[:10]
        datos = [{
            'id': noti.id,
            'mensaje': noti.mensaje,
            'fecha': noti.fecha.strftime('%H:%M'),
        } for noti in notificaciones]
        return JsonResponse({'notificaciones': datos, 'count': len(datos)})
    return JsonResponse({'notificaciones': [], 'count': 0})

@login_required
def marcar_leida(request, notificacion_id):
    if request.method == 'POST':
        notificacion = get_object_or_404(Notificacion, id=notificacion_id, usuario=request.user)
        notificacion.leida = True
        notificacion.save()
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def ver_notificacion_detalle(request, notificacion_id):
    noti = get_object_or_404(Notificacion, id=notificacion_id, usuario=request.user)
    noti.leida = True
    noti.save()
    return render(request, 'notificacion_detalle.html', {
        'notificacion': noti,
        'cita': noti.cita
    })

@login_required
def ver_todas_las_notificaciones(request):
    es_admin_jefe = getattr(request.user, 'rol', None) in ['ADMIN', 'JEFE']
    if not (request.user.is_staff or es_admin_jefe):
        messages.error(request, "Acceso denegado")
        return redirect('home')
    notificaciones = Notificacion.objects.filter(usuario=request.user).order_by('-fecha')[:50]
    return render(request, 'todas_las_notificaciones.html', {'notificaciones': notificaciones})

@login_required
def marcar_todas_leidas(request):
    rol_usuario = getattr(request.user, 'rol', None)
    if rol_usuario in ['ADMIN', 'JEFE']:
        Notificacion.objects.filter(usuario=request.user, leida=False).update(leida=True)
        messages.success(request, "Todas las notificaciones marcadas como leídas.")
    else:
        messages.error(request, "No tienes permisos para esta acción.")
    return redirect('agendamiento:ver_todas_las_notificaciones')

@login_required
def detalle_cita(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id)
    if request.method == 'POST' and request.user.rol in ['ADMIN', 'JEFE']:
        nuevo_estado = request.POST.get('nuevo_estado')
        if nuevo_estado:
            cita.estado = nuevo_estado
            cita.save()
            messages.success(request, f"Estado actualizado a {cita.get_estado_display()}")
            return redirect('agendamiento:detalle_cita', cita_id=cita.id)
    return render(request, 'detalle_cita.html', {'cita': cita})

@user_passes_test(es_administrador, login_url='login', redirect_field_name=None)
def crear_servicio(request):
    if request.method == 'POST':
        form = ServicioForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, '¡El servicio ha sido creado con éxito!')
            return redirect('servicios')
    else:
        form = ServicioForm()
    return render(request, 'crear_servicio.html', {'form': form})

@user_passes_test(es_administrador, login_url='login', redirect_field_name=None)
def editar_servicio(request, servicio_id):
    servicio = get_object_or_404(Servicio, id=servicio_id)
    if request.method == 'POST':
        form = ServicioForm(request.POST, request.FILES, instance=servicio)
        if form.is_valid():
            form.save()
            messages.success(request, f'Servicio "{servicio.nombre}" actualizado correctamente.')
            return redirect('servicios')
    else:
        form = ServicioForm(instance=servicio)
    return render(request, 'editar_servicio.html', {
        'form': form,
        'servicio': servicio
    })