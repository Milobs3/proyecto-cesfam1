from django.urls import path
from . import views

urlpatterns = [
    # --- Vistas de Autenticación y Comunes ---
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('documentos/', views.documentos_view, name='documentos'),
    path('calendario/', views.calendario_view, name='calendario'),
    path('manual/', views.manual_view, name='manual'),
    path('gestion/solicitudes/', views.gestion_solicitudes_view, name='gestion_solicitudes'),

    # --- Vistas de Dashboard Unificado ---
    path('dashboard/', views.dashboard_view, name='dashboard'), # <-- VISTA UNIFICADA
    
    # Redireccionamos los nombres viejos a la vista unificada (esto es clave para el login)
    path('dashboard/funcionario/', views.dashboard_view, name='dashboard_funcionario'), # <-- APUNTA A VISTA UNIFICADA
    path('dashboard/subdireccion/', views.dashboard_view, name='dashboard_subdireccion'), # <-- APUNTA A VISTA UNIFICADA

    # --- Vistas de Admin ---
    path('roles/gestion/', views.admin_roles_view, name='roles_gestion'), 
    path('logs/auditoria/', views.admin_logs_view, name='logs_auditoria'),

    # --- Vistas de Subdirección (Gestión) ---
    path('gestion/calendario/', views.gestion_calendario_view, name='gestion_calendario'),
    path('gestion/dias/', views.gestion_dias_view, name='gestion_dias'),
    path('gestion/documentos/', views.gestion_documentos_view, name='gestion_documentos'),
    path('gestion/licencias/', views.gestion_licencias_view, name='gestion_licencias'),
    path('reporte/licencias/', views.reporte_licencias_view, name='reporte_licencias'),
    path('reportes/solicitudes/', views.reporte_solicitudes_view, name='reporte_solicitudes'),
    path('gestion/solicitudes/aprobar/<int:solicitud_id>/', views.aprobar_solicitud_view, name='aprobar_solicitud'),
    
    # RUTA DE HISTORIAL PERSONAL
    path('mi-historial/', views.historial_personal_view, name='historial_personal'),

    # Opcional: una página de inicio
    path('', views.login_view, name='index'), 

   # RUTA API PARA EL CALENDARIO (AÑADIR ESTO)
    path('api/eventos/', views.eventos_json_view, name='eventos_json'),
]