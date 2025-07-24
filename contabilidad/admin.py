from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import (
    Cliente, Modulo, Cuestionario, Pregunta, Opcion, 
    ResultadoCuestionario, PerfilUsuario, RespuestaUsuario
)
from django.urls import path
from django.shortcuts import redirect

class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    verbose_name_plural = 'Perfiles'
    filter_horizontal = ('modulos_permitidos', 'cuestionarios_asignados')

class UserAdmin(BaseUserAdmin):
    inlines = (PerfilUsuarioInline,)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

class ClienteAdmin(admin.ModelAdmin):
    filter_horizontal = ('modulos_activos', 'usuarios_asignados')
    list_display = ('nombre', 'rfc', 'mostrar_usuarios_asignados')
    search_fields = ('nombre', 'rfc')
    fieldsets = (
        ('Información Principal', {'fields': ('usuarios_asignados', 'nombre', 'rfc', 'estatus', 'tipo')}),
        ('Expediente del Cliente', {'fields': ('regimen_fiscal', 'domicilio', 'telefono', 'correo', 'fecha_inicio_operaciones')}),
        ('Información Operativa y Comercial', {'fields': ('no_recurrente', 'tipo_de_servicio', 'giro_comercial', 'areas', 'socio')}),
        ('Información de Pago', {'fields': ('forma_de_pago', 'honorarios')}),
        ('Permisos de Módulos', {'fields': ('modulos_activos',)}),
    )
    
    def mostrar_usuarios_asignados(self, obj):
        return ", ".join([user.username for user in obj.usuarios_asignados.all()])
    mostrar_usuarios_asignados.short_description = 'Usuarios Asignados'

class OpcionInline(admin.TabularInline):
    model = Opcion
    extra = 1

class PreguntaAdmin(admin.ModelAdmin):
    inlines = [OpcionInline]

class CuestionarioAdmin(admin.ModelAdmin):
    change_list_template = "admin/cuestionario_changelist.html"

class ModuloAdmin(admin.ModelAdmin):
    filter_horizontal = ('cuestionarios',)

class RespuestaUsuarioInline(admin.TabularInline):
    model = RespuestaUsuario
    extra = 0 
    readonly_fields = ('pregunta', 'opcion_seleccionada')
    can_delete = False

class ResultadoCuestionarioAdmin(admin.ModelAdmin):
    # --- CÓDIGO CORREGIDO ---
    list_display = ('usuario', 'cuestionario', 'puntaje', 'fecha_inicio', 'completado')
    # --- FIN DE LA CORRECCIÓN ---
    list_filter = ('cuestionario', 'usuario', 'completado')
    inlines = [RespuestaUsuarioInline] 
    def has_module_permission(self, request):
        return request.user.is_superuser

admin.site.register(Cliente, ClienteAdmin)
admin.site.register(Modulo, ModuloAdmin)
admin.site.register(Cuestionario, CuestionarioAdmin)
admin.site.register(Pregunta, PreguntaAdmin)
admin.site.register(ResultadoCuestionario, ResultadoCuestionarioAdmin)