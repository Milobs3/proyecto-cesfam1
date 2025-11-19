from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.hashers import check_password
from .models import Funcionarios, Dias_Administrativos, Comunicados, Documentos, Logs_Auditoria, Licencias, Roles, Logs_Auditoria, Eventos_Calendario, SolicitudesPermiso, Licencias
from django.db.models import Sum, F
from django.utils import timezone
from datetime import datetime
from .forms import DiasAdministrativosForm
from django.http import JsonResponse
from django.contrib.auth.forms import AuthenticationForm
# --- Funciones de Ayuda (para proteger vistas) ---
def es_admin(user):
    return user.is_superuser

def es_subdireccion(user):
    return user.is_staff or user.is_superuser

# --- 1. Vistas de Autenticación (Login Robusto) ---

def login_view(request):
    if request.method == 'POST':
        # 1. Usa AuthenticationForm: maneja automáticamente request.POST, validación, y autenticación.
        form = AuthenticationForm(request, data=request.POST) 

        if form.is_valid():
            # 2. Si la autenticación es exitosa, obtiene el objeto user.
            user = form.get_user() 
            auth_login(request, user)
            
            # Redirección según Rol
            if user.is_superuser:
                return redirect('roles_gestion')
            else:
                return redirect('dashboard')
        else:
            # 3. Si falla (credenciales incorrectas o campos vacíos), 
            # el objeto 'form' ya contiene los mensajes de error.
            return render(request, 'login.html', {'form': form})
    
    # 4. Si es GET, muestra el formulario vacío.
    form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})          

def logout_view(request):
    auth_logout(request)
    return redirect('login')


# --- 2. Vistas Compartidas (Dashboard y Navegación) ---

@login_required(login_url='login')
def dashboard_view(request):
    """
    Vista única para el Dashboard de Funcionario y Subdirección/Admin.
    Muestra los días restantes y comunicados.
    """
    # 1. Obtener Días Administrativos (Crear si no existen)
    try:
        dias = Dias_Administrativos.objects.get(id_funcionario=request.user)
    except Dias_Administrativos.DoesNotExist:
        # Crear un registro inicial si no existe
        dias = Dias_Administrativos.objects.create(id_funcionario=request.user)

    # 2. Obtener los últimos 3 Comunicados
    comunicados = Comunicados.objects.all().order_by('-fecha_publicacion')[:3]

    # 3. Enviar datos al HTML
    context = {
        'dias_admin': dias.admin_restantes,
        'dias_vacas': dias.vacaciones_restantes,
        'comunicados': comunicados
    }
    # La misma plantilla (dashboard.html) se usa, y el menú se adapta por user.is_staff
    return render(request, 'dashboard.html', context)

@login_required(login_url='login')
def documentos_view(request):
    # Obtener todos los documentos para listarlos
    docs = Documentos.objects.all().order_by('-fecha_carga')
    return render(request, 'documentos.html', {'documentos': docs})

@login_required(login_url='login')
def calendario_view(request):
    # Aquí se listarán los eventos del modelo Eventos_Calendario
    return render(request, 'calendario.html')

@login_required(login_url='login')
def manual_view(request):
    return render(request, 'manual.html')

@login_required(login_url='login')
def gestion_solicitudes_view(request):
    """
    Vista universal para que el Funcionario envíe solicitudes de días.
    La aprobación se gestiona en la vista de RRHH.
    """
    if request.method == 'POST':
        # (Aquí iría la lógica para guardar la solicitud en una nueva tabla de Solicitudes)
        pass # Por ahora, no haremos funcional el POST

    # Renderiza el formulario de solicitud
    return render(request, 'gestion_solicitudes.html')

@login_required(login_url='login')
def gestion_solicitudes_view(request):
    if request.method == 'POST':
        # 1. Obtener los datos del formulario
        tipo = request.POST.get('tipo_permiso')
        inicio_str = request.POST.get('fecha_inicio')
        fin_str = request.POST.get('fecha_fin')
        
        # Convertir strings a objetos date
        fecha_inicio = datetime.strptime(inicio_str, '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(fin_str, '%Y-%m-%d').date()

        # 2. Calcular los días solicitados (diferencia de fechas)
        diferencia = fecha_fin - fecha_inicio
        dias_solicitados = diferencia.days + 1 # +1 para incluir el día de inicio
        
        # 3. Guardar la solicitud en la base de datos
        SolicitudesPermiso.objects.create(
            id_funcionario_solicitante=request.user, # El usuario logueado
            tipo_permiso=tipo,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            dias_solicitados=dias_solicitados,
            estado='Pendiente'
        )
        
        # 4. Redirigir al dashboard para ver el resultado
        return redirect('dashboard')
    
    # Si es GET, simplemente muestra el formulario
    return render(request, 'gestion_solicitudes.html')

# --- 3. Vistas de Subdirección (Protegidas) ---



@user_passes_test(es_subdireccion, login_url='login')
def gestion_documentos_view(request):
    if request.method == 'POST':

        titulo = request.POST.get('titulo')
        categoria = request.POST.get('categoria')
        
        archivo = request.FILES.get('archivo') 


        if titulo and archivo:
            Documentos.objects.create(
                titulo=titulo,
                categoria=categoria,
                ruta_archivo=archivo,
                id_autor_carga=request.user
            )
            
            return redirect('documentos') 
        else:
            return render(request, 'gestion_documentos.html', {'error': 'Debe completar título y adjuntar un archivo.'})
            
    return render(request, 'gestion_documentos.html')

# intranet/views.py

@user_passes_test(es_subdireccion, login_url='login')
def gestion_calendario_view(request):
    if request.method == 'POST':
        # 1. Obtener los datos
        titulo = request.POST.get('titulo')
        tipo_evento = request.POST.get('tipo_evento')
        fecha_inicio = request.POST.get('fecha_inicio')
        
        # 2. Validar y crear
        if titulo and fecha_inicio:
            Eventos_Calendario.objects.create(
                titulo=titulo,
                tipo_evento=tipo_evento,
                fecha_inicio=fecha_inicio
            )
            # 3. Redirige al calendario (RF7)
            return redirect('calendario')
            
    # Se obtienen datos si se necesitan para un selector, pero por ahora solo renderiza
    return render(request, 'gestion_calendario.html')

# intranet/views.py

@user_passes_test(es_subdireccion, login_url='login')
def gestion_dias_view(request):
    funcionarios = Funcionarios.objects.all().order_by('username')
    
    # 1. Lógica de PROCESAMIENTO (POST)
    if request.method == 'POST':
        funcionario_id = request.POST.get('funcionario_id')
        
        # Buscamos o creamos el registro de días
        dias_obj, created = Dias_Administrativos.objects.get_or_create(
            id_funcionario=get_object_or_404(Funcionarios, pk=funcionario_id)
        )
        
        # Le pasamos los datos del formulario (request.POST) al Formulario de Django
        form = DiasAdministrativosForm(request.POST, instance=dias_obj)

        if form.is_valid():
            # Django hace el casteo y la validación. Solo guardamos.
            form.save()
            return redirect('dashboard')
        
        # Si no es válido, se sigue mostrando el formulario con errores (no implementado en este prototipo)
    
    # 2. Lógica de CARGA DE PÁGINA (GET)
    # Creamos un formulario vacío para el primer funcionario (por defecto)
    form = DiasAdministrativosForm() 
    
    context = {
        'funcionarios': funcionarios,
        'form': form # Enviamos el formulario de Django a la plantilla
    }
    return render(request, 'gestion_dias.html', context)
# intranet/views.py

# intranet/views.py (Reemplazar gestion_licencias_view)

@user_passes_test(es_subdireccion, login_url='login')
def gestion_licencias_view(request):
    if request.method == 'POST':
        # 1. Obtener los datos y el archivo
        funcionario_id = request.POST.get('funcionario_id')
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')
        foto_licencia = request.FILES.get('foto') # Nombre del campo en el HTML es 'foto'
        
        # 2. Validar
        if funcionario_id and foto_licencia:
            try:
                # Buscamos al funcionario afectado
                funcionario_afectado = Funcionarios.objects.get(pk=funcionario_id)
                
                # 3. Guardar la licencia en la base de datos (Documento Maestro)
                Licencias.objects.create(
                    id_funcionario=funcionario_afectado,
                    id_subdireccion_carga=request.user, # La subdirección logueada es quien sube
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                    ruta_foto_licencia=foto_licencia
                )
                # 4. Redirige al reporte para ver el registro
                return redirect('reporte_licencias')
            except Funcionarios.DoesNotExist:
                # Si el ID no corresponde a un funcionario, se sigue mostrando el formulario
                pass
            
    # Lógica de CARGA DE PÁGINA (GET)
    # Se obtienen todos los funcionarios para el selector del formulario
    funcionarios = Funcionarios.objects.all().order_by('username')
    return render(request, 'gestion_licencias.html', {'funcionarios': funcionarios})

@user_passes_test(es_subdireccion, login_url='login')
def reporte_licencias_view(request):
    """
    Vista para listar todas las licencias registradas (Lectura funcional).
    """
    # 1. Se obtienen todas las licencias de la base de datos
    licencias = Licencias.objects.all().order_by('-fecha_registro')
    
    context = {
        'licencias': licencias,
        # 2. Eliminamos la línea que causaba el FieldError. 
        #    La suma de días es un cálculo complejo que haremos después si sobra tiempo.
        'dias_totales': 0 
    }
    return render(request, 'reporte_licencias.html', context)

# intranet/views.py

@user_passes_test(es_subdireccion, login_url='login')
def reporte_solicitudes_view(request):
    """
    Vista para que la Subdirección revise las solicitudes de permiso (solo lectura).
    """
    # Obtenemos todas las solicitudes que están en estado 'Pendiente'
    solicitudes = SolicitudesPermiso.objects.filter(estado='Pendiente').order_by('-fecha_solicitud')
    
    context = {
        'solicitudes': solicitudes
    }
    return render(request, 'reporte_solicitudes.html', context)

@user_passes_test(es_subdireccion, login_url='login')
def aprobar_solicitud_view(request, solicitud_id):
    """
    Procesa la aprobación de una solicitud, registrando la licencia o descontando
    los días del balance, según el tipo de solicitud.
    """
    if request.method == 'POST':
        # 1. Obtener la solicitud
        solicitud = get_object_or_404(SolicitudesPermiso, pk=solicitud_id)
        
        if solicitud.estado == 'Pendiente':
            
            # --- 2. Lógica para Licencia Médica (Crea un registro, no descuenta días) ---
            if solicitud.tipo_permiso == 'licencia':
                
                # 2.1. Crear el registro en la tabla Licencias (historial)
                Licencias.objects.create(
                    id_funcionario=solicitud.id_funcionario_solicitante,
                    id_subdireccion_carga=request.user, # Subdirector que aprueba
                    fecha_inicio=solicitud.fecha_inicio,
                    fecha_fin=solicitud.fecha_fin,
                    # El archivo subido en el formulario de solicitud se traslada aquí
                    ruta_foto_licencia=solicitud.justificativo_archivo 
                )
                
            # --- 3. Lógica para Días/Vacaciones (Descuenta del balance) ---
            elif solicitud.tipo_permiso in ['vacaciones', 'administrativo']:
                
                # 3.1. Determinar qué campo del balance actualizar
                if solicitud.tipo_permiso == 'vacaciones':
                    campo_balance = 'vacaciones_restantes'
                else:
                    campo_balance = 'admin_restantes'
                    
                # 3.2. ACTUALIZACIÓN ATÓMICA del balance
                Dias_Administrativos.objects.filter(id_funcionario=solicitud.id_funcionario_solicitante).update(
                    **{campo_balance: F(campo_balance) - solicitud.dias_solicitados}
                )

            # 4. Marcar la solicitud como aprobada
            solicitud.estado = 'Aprobado'
            solicitud.save()

    return redirect('reporte_solicitudes')

# --- 4. Vistas de Admin (Protegidas) ---

@login_required(login_url='login') 
@user_passes_test(es_admin, login_url='login')
def admin_roles_view(request):
    roles_list = Roles.objects.all()
    context = {
        'roles': roles_list
    }
    return render(request, 'admin_roles.html', context)

@login_required(login_url='login') 
@user_passes_test(es_admin, login_url='login')
def admin_logs_view(request):
    logs_list = Logs_Auditoria.objects.all().order_by('-fecha_hora')
    context = {
        'logs': logs_list
    }
    return render(request, 'admin_logs.html', context)

# intranet/views.py

@login_required(login_url='login')
def historial_personal_view(request):
    """
    Vista para que el Funcionario vea su historial de solicitudes y licencias.
    """
    # 1. Solicitudes de permiso: propias del usuario logueado
    solicitudes = SolicitudesPermiso.objects.filter(id_funcionario_solicitante=request.user).order_by('-fecha_solicitud')
    
    # 2. Historial de licencias: licencias emitidas a este funcionario
    licencias_recibidas = Licencias.objects.filter(id_funcionario=request.user).order_by('-fecha_inicio')
    
    context = {
        'solicitudes': solicitudes,
        'licencias_recibidas': licencias_recibidas,
    }
    return render(request, 'historial_personal.html', context)

@login_required(login_url='login')
def eventos_json_view(request):
    """
    Vista que retorna los eventos del calendario en formato JSON para FullCalendar.
    """
    # 1. Obtener todos los eventos
    eventos = Eventos_Calendario.objects.all()
    
    # 2. Adaptar los datos al formato específico que FullCalendar espera
    data = []
    for evento in eventos:
        data.append({
            'title': f"{evento.tipo_evento}: {evento.titulo}",
            # Formato YYYY-MM-DD para FullCalendar
            'start': evento.fecha_inicio.strftime('%Y-%m-%d'), 
            # Si hay fecha fin, la usa, sino, usa la de inicio
            'end': evento.fecha_fin.strftime('%Y-%m-%d') if evento.fecha_fin else evento.fecha_inicio.strftime('%Y-%m-%d'),
            'color': '#f4a460' if evento.tipo_evento == 'Feriado' else '#1E4A7B',
            'allDay': True,
        })
        
    return JsonResponse(data, safe=False)