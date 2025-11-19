from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# --- MODELOS BASADOS EN TU INFORME (Cesfam PRINTEGRADO (1).docx) ---

# Tabla: Roles
class Roles(models.Model):
    nombre_rol = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.nombre_rol

# 2.Tabla: Funcionarios
class Funcionarios(AbstractUser):
    # 'email', 'username', 'password' ya vienen en AbstractUser.
    nombre = models.CharField(max_length=100, blank=True)
    id_rol = models.ForeignKey(Roles, on_delete=models.SET_NULL, null=True, blank=True)

# 3. Tabla: Dias_Administrativos
class Dias_Administrativos(models.Model):
    # OneToOneField asegura que solo haya UN registro por funcionario
    id_funcionario = models.OneToOneField(Funcionarios, on_delete=models.CASCADE, primary_key=True)
    vacaciones_restantes = models.IntegerField(default=20)
    admin_restantes = models.IntegerField(default=5)

# 4. Tabla: Documentos
class Documentos(models.Model):
    titulo = models.CharField(max_length=255)
    categoria = models.CharField(max_length=100, blank=True, null=True)
    # FileField es clave: Django manejará la subida de archivos (PDF, Word)
    ruta_archivo = models.FileField(upload_to='documentos/') 
    fecha_carga = models.DateTimeField(auto_now_add=True)
    # [cite_start]Registra QUIÉN subió el documento [cite: 232]
    id_autor_carga = models.ForeignKey(Funcionarios, on_delete=models.SET_NULL, null=True, blank=True)

# 5. Tabla: Comunicados 
class Comunicados(models.Model):
    titulo = models.CharField(max_length=255)
    cuerpo = models.TextField()
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    # [cite_start]Registra QUIÉN publicó el comunicado [cite: 224]
    id_autor = models.ForeignKey(Funcionarios, on_delete=models.SET_NULL, null=True)

# [cite_start]6. Tabla: Eventos_Calendario (Soporta RF7, RF8) [cite: 216, 226, 227]
# Para reuniones, capacitaciones, feriados
class Eventos_Calendario(models.Model):
    # Ya que el formulario HTML solo pide la fecha, usamos DateField para evitar errores de hora
    titulo = models.CharField(max_length=200)
    fecha_inicio = models.DateField() 
    fecha_fin = models.DateField(null=True, blank=True)
    tipo_evento = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.titulo} ({self.fecha_inicio})"

    class Meta:
        # Esto es necesario porque tu tabla ya existe con guiones bajos en el nombre
        db_table = 'intranet_eventos_calendario' 
        verbose_name_plural = "Eventos del Calendario"

# [cite_start]7. Tabla: Logs_Auditoria (Soporta RF18) [cite: 237]
# Almacena los cambios de roles y accesos
class Logs_Auditoria(models.Model):
    fecha_hora = models.DateTimeField(auto_now_add=True)
    id_usuario_actor = models.ForeignKey(Funcionarios, on_delete=models.SET_NULL, null=True, blank=True)
    accion = models.CharField(max_length=255)
    detalle = models.TextField(blank=True, null=True)

# --- MODELO BASADO EN EL "DOCUMENTO MAESTRO" (Requisito Extra) ---

# [cite_start]8. Tabla: Licencias (Requisito "Documento Maestro") [cite: 53-54]
# Flujo de Subdirección para ingresar licencias
class Licencias(models.Model):
    # El funcionario al que pertenece la licencia
    id_funcionario = models.ForeignKey(Funcionarios, on_delete=models.CASCADE, related_name='licencias_recibidas')
    # El funcionario (Subdirección) que cargó la licencia
    id_subdireccion_carga = models.ForeignKey(Funcionarios, on_delete=models.SET_NULL, null=True, related_name='licencias_cargadas')
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    ruta_foto_licencia = models.FileField(upload_to='licencias/')
    fecha_registro = models.DateTimeField(auto_now_add=True)

class SolicitudesPermiso(models.Model):
    # Este modelo registra la solicitud que el funcionario envía (HU4)
    id_funcionario_solicitante = models.ForeignKey(Funcionarios, on_delete=models.CASCADE, related_name='solicitudes_enviadas')
    tipo_permiso = models.CharField(max_length=50) # 'vacaciones', 'administrativo', 'otro'
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    dias_solicitados = models.IntegerField(default=0)
    justificativo_archivo = models.FileField(upload_to='solicitudes/', null=True, blank=True)
    fecha_solicitud = models.DateTimeField(default=timezone.now)
    estado = models.CharField(max_length=50, default='Pendiente') # 'Pendiente', 'Aprobado', 'Rechazado'
    
    def __str__(self):
        return f"Solicitud de {self.id_funcionario_solicitante.username} ({self.estado})"

    class Meta:
        verbose_name_plural = "Solicitudes de Permiso"