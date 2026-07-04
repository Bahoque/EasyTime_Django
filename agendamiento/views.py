from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import Cita, Servicio, Notificacion, Operario
from .forms import CitaForm, ServicioForm, OperarioForm, ProductoFacturaForm

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
    from inventario.models import Producto, Venta
    servicio_seleccionado = None
    if servicio_id:
        servicio_seleccionado = get_object_or_404(Servicio, id=servicio_id)

    productos = Producto.objects.filter(activo=True, stock_actual__gt=0)
    carrito = Venta.objects.filter(cliente=request.user, pagado=False).first()
    items_carrito = carrito.items_venta.all() if carrito else []

    if request.method == 'POST':
        form = CitaForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    cita = form.save(commit=False)
                    cita.usuario = request.user
                    cita.save()

                    from inventario.models import Factura, DetalleFactura
                    factura = Factura.objects.create(
                        cliente=request.user,
                        cita=cita,
                        estado='PENDIENTE'
                    )

                    # Productos desde el carrito
                    items_carrito_ids = request.POST.getlist('item_carrito_id')
                    cantidades_carrito = request.POST.getlist('cantidad_carrito')
                    for item_id, cant in zip(items_carrito_ids, cantidades_carrito):
                        try:
                            from inventario.models import DetalleVenta
                            item = DetalleVenta.objects.get(
                                id=item_id,
                                venta__cliente=request.user,
                                venta__pagado=False
                            )
                            cantidad = int(cant)
                            if cantidad > 0:
                                DetalleFactura.objects.create(
                                    factura=factura,
                                    producto=item.producto,
                                    cantidad=cantidad,
                                    precio_unitario=item.precio_unitario
                                )
                        except Exception:
                            continue

                    # Productos nuevos
                    productos_ids = request.POST.getlist('producto_id')
                    cantidades = request.POST.getlist('cantidad')
                    for pid, cant in zip(productos_ids, cantidades):
                        try:
                            if not pid:
                                continue
                            producto = Producto.objects.get(id=pid, activo=True)
                            cantidad = int(cant)
                            if cantidad > 0 and producto.stock_actual >= cantidad:
                                DetalleFactura.objects.create(
                                    factura=factura,
                                    producto=producto,
                                    cantidad=cantidad,
                                    precio_unitario=producto.precio_venta
                                )
                        except (Producto.DoesNotExist, ValueError):
                            continue

                    return redirect('agendamiento:pasarela_cita', factura_id=factura.id)

            except IntegrityError:
                messages.error(request, "Error: Esa fecha y hora ya están ocupadas.")
    else:
        initial_data = {'servicio': servicio_seleccionado} if servicio_seleccionado else {}
        form = CitaForm(initial=initial_data)

    return render(request, 'agendar.html', {
        'form': form,
        'servicio_seleccionado': servicio_seleccionado,
        'productos': productos,
        'items_carrito': items_carrito,
    })

@login_required
def pasarela_cita(request, factura_id):
    from inventario.models import Factura, DetalleFactura
    factura = get_object_or_404(Factura, id=factura_id, cliente=request.user, estado='PENDIENTE')

    if request.method == 'POST':
        with transaction.atomic():
            for item in factura.items.all():
                if item.producto.stock_actual < item.cantidad:
                    messages.error(request, f"Stock insuficiente para {item.producto.nombre}")
                    return redirect('agendamiento:pasarela_cita', factura_id=factura.id)
                item.producto.stock_actual -= item.cantidad
                item.producto.save()

            from inventario.models import DetalleVenta
            for item_factura in factura.items.all():
                DetalleVenta.objects.filter(
                    venta__cliente=request.user,
                    venta__pagado=False,
                    producto=item_factura.producto
                ).delete()

            factura.estado = 'PAGADA'
            factura.save()
            if factura.cita:
                factura.cita.estado = 'CONFIRMADA'
                factura.cita.save()

        messages.success(request, f"¡Pago exitoso! Tu cita está confirmada. Factura {factura.numero}")
        return redirect('agendamiento:ver_factura', factura_id=factura.id)

    return render(request, 'pasarela_cita.html', {'factura': factura})

@login_required
def ver_factura(request, factura_id):
    from inventario.models import Factura
    factura = get_object_or_404(Factura, id=factura_id, cliente=request.user)
    return render(request, 'factura.html', {'factura': factura})

@login_required
def descargar_factura_pdf(request, factura_id):
    from inventario.models import Factura
    from django.http import HttpResponse
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle
    import os
    from django.conf import settings as django_settings

    factura = get_object_or_404(Factura, id=factura_id, cliente=request.user)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Factura_{factura.numero}.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    p.setFillColor(colors.HexColor("#459fe9"))
    p.rect(0, height - 100, width, 100, fill=True, stroke=False)

    logo_path = os.path.join(django_settings.BASE_DIR, 'static', 'img', 'favicon.ico')
    if os.path.exists(logo_path):
        p.drawImage(logo_path, 40, height - 75, width=40, height=40, mask='auto')

    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 22)
    p.drawString(90, height - 50, "EasyTime")
    p.setFont("Helvetica", 10)
    p.drawString(90, height - 68, "Servicio profesional de lavado vehicular")

    p.setFont("Helvetica-Bold", 14)
    p.drawRightString(width - 40, height - 45, f"FACTURA {factura.numero}")
    p.setFont("Helvetica", 10)
    p.drawRightString(width - 40, height - 62, f"Fecha: {factura.fecha_emision.strftime('%d/%m/%Y %H:%M')}")
    p.drawRightString(width - 40, height - 78, f"Estado: {factura.get_estado_display()}")

    y = height - 130
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 11)
    p.drawString(40, y, "INFORMACIÓN DEL CLIENTE")
    y -= 18
    p.setFont("Helvetica", 10)
    p.drawString(40, y, f"Cliente: {factura.cliente.get_full_name() or factura.cliente.username}")
    y -= 15
    p.drawString(40, y, f"Correo: {factura.cliente.email}")

    if factura.cita:
        y -= 25
        p.setFont("Helvetica-Bold", 11)
        p.drawString(40, y, "DETALLE DEL SERVICIO")
        y -= 18
        p.setFont("Helvetica", 10)
        p.drawString(40, y, f"Servicio: {factura.cita.servicio.nombre}")
        y -= 15
        p.drawString(40, y, f"Operario: {factura.cita.operario or 'No asignado'}")
        y -= 15
        p.drawString(40, y, f"Fecha y hora: {factura.cita.fecha_hora.strftime('%d/%m/%Y %H:%M')}")
        y -= 15
        p.drawString(40, y, f"Placa: {factura.cita.placa_vehiculo}")
        y -= 15
        p.drawString(40, y, f"Duración estimada: {factura.cita.servicio.duracion_estimada}")

    y -= 30
    p.setFont("Helvetica-Bold", 11)
    p.drawString(40, y, "RESUMEN DE COBRO")
    y -= 15

    data = [['Descripción', 'Cantidad', 'Precio Unit.', 'Subtotal']]

    if factura.cita:
        data.append([
            factura.cita.servicio.nombre,
            '1',
            f"${factura.cita.servicio.precio:,.0f}",
            f"${factura.cita.servicio.precio:,.0f}"
        ])

    for item in factura.items.all():
        data.append([
            item.producto.nombre,
            str(item.cantidad),
            f"${item.precio_unitario:,.0f}",
            f"${item.subtotal:,.0f}"
        ])

    data.append(['', '', 'TOTAL', f"${factura.total:,.0f}"])

    tabla = Table(data, colWidths=[250, 70, 100, 100])
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#459fe9")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -2), 0.5, colors.HexColor("#dee2e6")),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#f8f9fa")),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor("#f8f9fa")]),
        ('PADDING', (0, 0), (-1, -1), 8),
    ])
    tabla.setStyle(style)
    w_t, h_t = tabla.wrap(width - 80, height)
    tabla.drawOn(p, 40, y - h_t)

    y_footer = 40
    p.setFont("Helvetica", 8)
    p.setFillColor(colors.grey)
    p.drawCentredString(width / 2, y_footer, "EasyTime — Bogotá, Colombia | contacto@easytime.com")
    p.drawCentredString(width / 2, y_footer - 12, f"Factura generada el {factura.fecha_emision.strftime('%d/%m/%Y %H:%M')}")

    p.showPage()
    p.save()
    return response

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

# ===================================================================
# GESTIÓN DE OPERARIOS
# ===================================================================

@user_passes_test(es_administrador, login_url='login', redirect_field_name=None)
def lista_operarios(request):
    operarios = Operario.objects.all().order_by('nombre')
    return render(request, 'operarios/lista_operarios.html', {'operarios': operarios})

@user_passes_test(es_administrador, login_url='login', redirect_field_name=None)
def crear_operario(request):
    if request.method == 'POST':
        form = OperarioForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Operario creado correctamente.')
            return redirect('agendamiento:lista_operarios')
    else:
        form = OperarioForm()
    return render(request, 'operarios/form_operario.html', {
        'form': form,
        'titulo': 'Nuevo Operario'
    })

@user_passes_test(es_administrador, login_url='login', redirect_field_name=None)
def editar_operario(request, operario_id):
    operario = get_object_or_404(Operario, id=operario_id)
    if request.method == 'POST':
        form = OperarioForm(request.POST, request.FILES, instance=operario)
        if form.is_valid():
            form.save()
            messages.success(request, f'Operario "{operario.nombre}" actualizado correctamente.')
            return redirect('agendamiento:lista_operarios')
    else:
        form = OperarioForm(instance=operario)
    return render(request, 'operarios/form_operario.html', {
        'form': form,
        'titulo': 'Editar Operario',
        'operario': operario
    })

@user_passes_test(es_administrador, login_url='login', redirect_field_name=None)
def toggle_operario(request, operario_id):
    operario = get_object_or_404(Operario, id=operario_id)
    if request.method == 'POST':
        operario.activo = not operario.activo
        operario.save()
        estado = "activado" if operario.activo else "inhabilitado"
        messages.success(request, f'Operario {operario.nombre} {estado} correctamente.')
    return redirect('agendamiento:lista_operarios')

@login_required
def operarios_disponibles(request):
    servicio_id = request.GET.get('servicio_id')
    fecha_hora_str = request.GET.get('fecha_hora')

    if not servicio_id or not fecha_hora_str:
        return JsonResponse({'operarios': []})

    try:
        from django.utils.dateparse import parse_datetime
        from django.utils import timezone
        servicio = Servicio.objects.get(id=servicio_id, activo=True)
        fecha_hora = parse_datetime(fecha_hora_str)
        if fecha_hora and timezone.is_naive(fecha_hora):
            fecha_hora = timezone.make_aware(fecha_hora)

        operarios_activos = Operario.objects.filter(activo=True)
        disponibles = []
        for op in operarios_activos:
            if op.esta_disponible(fecha_hora, servicio.duracion_estimada):
                disponibles.append({
                    'id': op.id,
                    'nombre': f"{op.nombre} {op.apellido}",
                    'especialidad': op.especialidad or ''
                })

        return JsonResponse({'operarios': disponibles})
    except Exception as e:
        return JsonResponse({'operarios': [], 'error': str(e)})