from django.db import models
from django.contrib.auth.models import User

# --- Modelos de Cuestionarios y Evaluación (Sin cambios en su definición) ---
class Cuestionario(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    tiempo_limite_minutos = models.PositiveIntegerField(default=10, help_text="Tiempo límite en minutos para completar el cuestionario.")
    def __str__(self):
        return self.titulo

class Pregunta(models.Model):
    cuestionario = models.ForeignKey(Cuestionario, related_name='preguntas', on_delete=models.CASCADE)
    texto = models.CharField(max_length=500)
    valor = models.PositiveIntegerField(default=1, help_text="Puntos que vale esta pregunta.")
    def __str__(self):
        return self.texto

class Opcion(models.Model):
    pregunta = models.ForeignKey(Pregunta, related_name='opciones', on_delete=models.CASCADE)
    texto = models.CharField(max_length=200)
    es_correcta = models.BooleanField(default=False)
    def __str__(self):
        return self.texto

# --- Modelos Principales (Cliente, Módulo, Perfil) ---
class Modulo(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    cuestionarios = models.ManyToManyField(Cuestionario, blank=True)
    def __str__(self):
        return self.nombre

class Cliente(models.Model):
    usuarios_asignados = models.ManyToManyField(User, blank=True)
    nombre = models.CharField(max_length=200)
    rfc = models.CharField(max_length=13, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    modulos_activos = models.ManyToManyField(Modulo, blank=True)
    regimen_fiscal = models.CharField("Régimen Fiscal", max_length=200, blank=True)
    domicilio = models.TextField(blank=True)
    telefono = models.CharField("Teléfono", max_length=20, blank=True)
    correo = models.EmailField("Correo", max_length=254, blank=True)
    fecha_inicio_operaciones = models.DateField("Fecha de inicio de operaciones", blank=True, null=True)
    no_recurrente = models.CharField("No. Recurrente", max_length=50, blank=True)
    tipo = models.CharField(max_length=100, blank=True)
    estatus = models.CharField(max_length=100, blank=True)
    tipo_de_servicio = models.CharField("Tipo de servicio", max_length=200, blank=True)
    giro_comercial = models.CharField("Giro Comercial", max_length=200, blank=True)
    forma_de_pago = models.CharField("Forma de Pago", max_length=100, blank=True)
    honorarios = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    socio = models.CharField("Socio", max_length=255, blank=True)
    areas = models.CharField("Áreas", max_length=255, blank=True)
    def __str__(self):
        return f"{self.nombre} ({self.rfc})"

class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    modulos_permitidos = models.ManyToManyField(Modulo, blank=True, related_name="usuarios_con_acceso")
    cuestionarios_asignados = models.ManyToManyField(Cuestionario, blank=True)
    def __str__(self):
        return f"Perfil de {self.usuario.username}"

# --- Modelos para guardar los Resultados y Respuestas ---
class ResultadoCuestionario(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    cuestionario = models.ForeignKey(Cuestionario, on_delete=models.CASCADE)
    puntaje = models.FloatField(null=True, blank=True) # Puede estar vacío al iniciar
    # --- CAMBIOS ---
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    completado = models.BooleanField(default=False) # Para saber si el intento fue finalizado

    def __str__(self):
        estado = "Completado" if self.completado else "Iniciado"
        return f"{self.usuario.username} - {self.cuestionario.titulo} ({estado})"

class RespuestaUsuario(models.Model):
    resultado = models.ForeignKey(ResultadoCuestionario, related_name='respuestas', on_delete=models.CASCADE)
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE)
    opcion_seleccionada = models.ForeignKey(Opcion, on_delete=models.CASCADE)

    def __str__(self):
        return f"Respuesta a '{self.pregunta.texto[:30]}...'"