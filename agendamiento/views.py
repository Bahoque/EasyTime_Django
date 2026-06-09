from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import IntegrityError
from django.http import JsonResponse
from django.core.paginator import Paginator # Importante para el catálogo
from .models import Cita, Servicio, Notificacion 
from .forms import CitaForm, ServicioForm  # ✅ CORRECCIÓN: Se importó ServicioForm

# ===================================================================
# CATÁLOGO Y AGENDAMIENTO
# ===================================================================

def lista_servicios(request):
    """Muestra el catálogo con paginación de 6 servicios (Ruta corregida)"""
    servicios_list = Servicio.objects.all().order_by('nombre')
    paginator = Paginator(servicios_list, 6) #
    
    page_number = request.GET.get('page')
    servicios = paginator.get_page(page_number)
    
    # El template está en la raíz de templates/ según tu estructura
    return render(request, 'servicios.html', {'servicios': servicios})

@login_required
def agendar_cita(request, servicio_id=None):
    """Permite agendar una cita, opcionalmente con un servicio preseleccionado"""
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
    """Historial de citas del usuario actual"""
    citas = Cita.objects.filter(usuario=request.user).order_by('-fecha_hora')
    return render(request, 'mis_citas.html', {'citas': citas})

# ===================================================================
# SISTEMA DE NOTIFICACIONES
# ===================================================================

@login_required
def obtener_notificaciones(request):
    """Endpoint para el navbar (Actualización en tiempo real)"""
    es_admin_jefe = getattr(request.user, 'rol', None) in ['ADMIN', 'JEFE'] #
    
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
    """Marca como leída una notificación específica"""
    if request.method == 'POST':
        notificacion = get_object_or_404(Notificacion, id=notificacion_id, usuario=request.user)
        notificacion.leida = True
        notificacion.save()
        return JsonResponse({'status': 'ok'}) # Corregida indentación
    
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def ver_notificacion_detalle(request, notificacion_id):
    """
    CAMBIO REALIZADO: Ahora carga el template azul (notificacion_detalle.html) 
    en lugar de saltar directo a la gestión.
    """
    noti = get_object_or_404(Notificacion, id=notificacion_id, usuario=request.user)

    noti.leida = True
    noti.save()

    # Si la notificación tiene cita, la pasamos para que el diseño azul no salga vacío
    return render(request, 'notificacion_detalle.html', {
        'notificacion': noti,
        'cita': noti.cita
    })

@login_required
def ver_todas_las_notificaciones(request):
    """Historial completo de alertas"""
    es_admin_jefe = getattr(request.user, 'rol', None) in ['ADMIN', 'JEFE']
    
    if not (request.user.is_staff or es_admin_jefe):
        messages.error(request, "Acceso denegado")
        return redirect('home')
    
    notificaciones = Notificacion.objects.filter(usuario=request.user).order_by('-fecha')[:50]
    return render(request, 'todas_las_notificaciones.html', {'notificaciones': notificaciones})

@login_required
def marcar_todas_leidas(request):
    """CAMBIO REALIZADO: Añadido namespace 'agendamiento:' para evitar error amarillo"""
    rol_usuario = getattr(request.user, 'rol', None)
    
    if rol_usuario in ['ADMIN', 'JEFE']:
        Notificacion.objects.filter(usuario=request.user, leida=False).update(leida=True)
        messages.success(request, "Todas las notificaciones marcadas como leídas.")
    else:
        messages.error(request, "No tienes permisos de administrador para esta acción.")
        
    return redirect('agendamiento:ver_todas_las_notificaciones')

# ===================================================================
# GESTIÓN Y DETALLES DE CITAS
# ===================================================================

@login_required
def detalle_cita(request, cita_id):
    """
    CAMBIO REALIZADO: Añadido namespace 'agendamiento:' en el redirect 
    para recargar el diseño claro correctamente.
    """
    # Buscamos la cita por su ID
    cita = get_object_or_404(Cita, id=cita_id)
    
    # Si el Administrador cambia el estado en el formulario del detalle
    if request.method == 'POST' and request.user.rol in ['ADMIN', 'JEFE']:
        nuevo_estado = request.POST.get('nuevo_estado')
        if nuevo_estado:
            cita.estado = nuevo_estado
            cita.save()
            # Mensaje de éxito y recarga la página con el namespace
            messages.success(request, f"Estado actualizado a {cita.get_estado_display()}")
            return redirect('agendamiento:detalle_cita', cita_id=cita.id)

    # Renderizamos tu nuevo template de diseño claro
    return render(request, 'detalle_cita.html', {'cita': cita})


# ===================================================================
# ➕ MÓDULO ADMINISTRATIVO DE SERVICIOS (AÑADIDO)
# ===================================================================

def es_administrador(user):
    """Verifica si el usuario logueado pertenece al equipo administrativo"""
    return user.is_authenticated and (user.is_staff or getattr(user, 'rol', None) in ['ADMIN',])

@user_passes_test(es_administrador, login_url='login', redirect_field_name=None)
def crear_servicio(request):
    """Permite registrar un nuevo servicio desde la interfaz operativa sin usar Django Admin"""
    if request.method == 'POST':
        # Pasamos request.FILES de forma obligatoria para capturar la imagen adjunta
        form = ServicioForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, '¡El servicio operativo ha sido creado y guardado con éxito!')
            return redirect('home')
    else:
        form = ServicioForm()
        
    return render(request, 'crear_servicio.html', {'form': form})