import os
import openpyxl
from collections import OrderedDict
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import (
    Cliente, Modulo, Cuestionario, Pregunta, Opcion, 
    PerfilUsuario, ResultadoCuestionario, RespuestaUsuario
)
from .utils import procesar_seleccion

# --- VISTAS PRINCIPALES Y DE AUTENTICACIÓN ---

@login_required(login_url='login')
def main_dashboard_view(request):
    """Muestra el panel principal de módulos."""
    try:
        perfil = PerfilUsuario.objects.get(usuario=request.user)
        modulos_permitidos = perfil.modulos_permitidos.all()
    except PerfilUsuario.DoesNotExist:
        if request.user.is_superuser:
            modulos_permitidos = Modulo.objects.all()
        else:
            modulos_permitidos = []
    
    contexto = {
        'lista_modulos': modulos_permitidos
    }
    return render(request, 'main_dashboard.html', contexto)

@login_required(login_url='login')
def cliente_list_view(request):
    """Muestra la lista de clientes asignados al usuario."""
    clientes_del_usuario = Cliente.objects.filter(usuarios_asignados=request.user)
    contexto = {
        'lista_clientes': clientes_del_usuario,
        'usuario': request.user,
    }
    return render(request, 'cliente_list.html', contexto)

def login_view(request):
    """Maneja el inicio de sesión del usuario."""
    error = None
    if request.method == 'POST':
        usuario_form = request.POST.get('username')
        password_form = request.POST.get('password')
        user = authenticate(request, username=usuario_form, password=password_form)
        if user is not None:
            login(request, user)
            return redirect('main_dashboard')
        else:
            error = "Usuario o contraseña inválidos. Por favor, intenta de nuevo."
    return render(request, 'login.html', {'error': error})

def logout_view(request):
    """Cierra la sesión del usuario."""
    logout(request)
    return redirect('login')

# --- VISTAS DE MÓDULOS POR CLIENTE ---

@login_required(login_url='login')
def dashboard_cliente_view(request, cliente_id):
    """Muestra el dashboard de un cliente específico."""
    cliente = get_object_or_404(Cliente, id=cliente_id, usuarios_asignados=request.user)
    contexto = {
        'cliente': cliente,
        'modulos': cliente.modulos_activos.all(),
        'active_tab': 'Dashboard'
    }
    return render(request, 'dashboard_cliente.html', contexto)

@login_required(login_url='login')
def expediente_view(request, cliente_id):
    """Muestra el expediente de un cliente específico."""
    cliente = get_object_or_404(Cliente, id=cliente_id, usuarios_asignados=request.user)
    contexto = {
        'cliente': cliente,
        'modulos': cliente.modulos_activos.all(),
        'active_tab': 'Expediente'
    }
    return render(request, 'expediente.html', contexto)

@login_required(login_url='login')
def xml_viewer_view(request, cliente_id, anio=None):
    """Muestra el visor de facturas XML para un cliente y año."""
    cliente = get_object_or_404(Cliente, id=cliente_id, usuarios_asignados=request.user)
    path_cliente_fs = os.path.join(settings.RUTA_PRINCIPAL_XMLS, cliente.rfc)
    anios_disponibles = set()
    for tipo_op in ['emitidos', 'recibidos']:
        path_tipo = os.path.join(path_cliente_fs, tipo_op)
        if os.path.isdir(path_tipo):
            for anio_folder in os.listdir(path_tipo):
                if anio_folder.isdigit() and os.path.isdir(os.path.join(path_tipo, anio_folder)):
                    anios_disponibles.add(anio_folder)
    
    if anio is None:
        anio = sorted(list(anios_disponibles), reverse=True)[0] if anios_disponibles else datetime.now().year

    mapa_ingresos, mapa_egresos = procesar_seleccion(settings.RUTA_PRINCIPAL_XMLS, cliente.rfc, str(anio))
    nombres_mes_dict = { "01": "Enero", "02": "Febrero", "03": "Marzo", "04": "Abril", "05": "Mayo", "06": "Junio", "07": "Julio", "08": "Agosto", "09": "Septiembre", "10": "Octubre", "11": "Noviembre", "12": "Diciembre"}
    
    contexto = {
        'cliente': cliente,
        'modulos': cliente.modulos_activos.all(),
        'active_tab': 'FACTURACION',
        'ingresos': agrupar_por_mes(mapa_ingresos, nombres_mes_dict),
        'egresos': agrupar_por_mes(mapa_egresos, nombres_mes_dict),
        'nombres_mes': nombres_mes_dict,
        'anios_disponibles': sorted(list(anios_disponibles), reverse=True),
        'anio_seleccionado': int(anio),
    }
    return render(request, 'xml_viewer.html', contexto)

@login_required(login_url='login')
def iva_view(request, cliente_id):
    """Muestra el resumen de cálculo de IVA para un cliente."""
    cliente = get_object_or_404(Cliente, id=cliente_id, usuarios_asignados=request.user)
    anio_a_procesar = "2025" # Placeholder
    mapa_ingresos, mapa_egresos = procesar_seleccion(settings.RUTA_PRINCIPAL_XMLS, cliente.rfc, anio_a_procesar)
    resumen = {f"{i:02d}": {"iva_trasladado": 0, "iva_acreditable": 0} for i in range(1, 13)}
    for item in mapa_ingresos.values():
        if item.get("Estado") == "Vigente":
            mes = item.get("Mes de Emisión")
            if mes in resumen:
                resumen[mes]["iva_trasladado"] += item.get("IVA", 0)
    for item in mapa_egresos.values():
        if item.get("Estado") == "Vigente":
            mes = item.get("Mes de Emisión")
            if mes in resumen:
                resumen[mes]["iva_acreditable"] += item.get("IVA", 0)
    nombres_mes_dict = { "01": "Enero", "02": "Febrero", "03": "Marzo", "04": "Abril", "05": "Mayo", "06": "Junio", "07": "Julio", "08": "Agosto", "09": "Septiembre", "10": "Octubre", "11": "Noviembre", "12": "Diciembre"}
    tabla_resumen, total_anual = [], {"iva_trasladado": 0, "iva_acreditable": 0, "a_pagar": 0, "a_favor": 0}
    for mes_num, mes_nombre in nombres_mes_dict.items():
        data_mes = resumen[mes_num]
        a_pagar = max(0, data_mes['iva_trasladado'] - data_mes['iva_acreditable'])
        a_favor = max(0, data_mes['iva_acreditable'] - data_mes['iva_trasladado'])
        tabla_resumen.append({"mes": mes_nombre, "trasladado": data_mes['iva_trasladado'], "acreditable": data_mes['iva_acreditable'], "pagar": a_pagar, "favor": a_favor})
        total_anual["iva_trasladado"] += data_mes['iva_trasladado']; total_anual["iva_acreditable"] += data_mes['iva_acreditable']; total_anual["a_pagar"] += a_pagar; total_anual["a_favor"] += a_favor
    contexto = {
        'cliente': cliente,
        'modulos': cliente.modulos_activos.all(),
        'active_tab': 'Cálculo IVA',
        'tabla_resumen': tabla_resumen,
        'totales': total_anual
    }
    return render(request, 'iva.html', contexto)

# --- VISTAS PARA EL MÓDULO DE EVALUACIÓN ---

@login_required(login_url='login')
def importar_cuestionario_view(request):
    """Maneja la subida de un cuestionario desde un archivo Excel."""
    if request.method == 'POST':
        try:
            excel_file = request.FILES['excel_file']
            cuestionario_titulo = request.POST.get('titulo')
            tiempo_limite = request.POST.get('tiempo_limite')
            if not all([excel_file, cuestionario_titulo, tiempo_limite]):
                raise ValueError("Todos los campos son obligatorios.")
            cuestionario = Cuestionario.objects.create(titulo=cuestionario_titulo, tiempo_limite_minutos=int(tiempo_limite))
            workbook = openpyxl.load_workbook(excel_file)
            sheet = workbook.active
            for row in sheet.iter_rows(min_row=2, max_col=7, values_only=True):
                pregunta_texto, opA, opB, opC, opD, resp_correcta_texto, valor = (str(c or '').strip() for c in row)
                if not pregunta_texto: continue
                try: valor_pregunta = int(float(valor))
                except (ValueError, TypeError): valor_pregunta = 1
                pregunta = Pregunta.objects.create(cuestionario=cuestionario, texto=pregunta_texto, valor=valor_pregunta)
                opciones = [opA, opB, opC, opD]
                texto_correcto_limpio = resp_correcta_texto.split(')', 1)[-1].strip() if ')' in resp_correcta_texto else resp_correcta_texto
                for opcion_texto in opciones:
                    if opcion_texto:
                        Opcion.objects.create(pregunta=pregunta, texto=opcion_texto, es_correcta=(opcion_texto == texto_correcto_limpio))
            return redirect('/admin/contabilidad/cuestionario/')
        except Exception as e:
            return render(request, 'importar_cuestionario.html', {'error': f'Ocurrió un error: {e}'})
    return render(request, 'importar_cuestionario.html')

@login_required(login_url='login')
def evaluacion_list_view(request):
    """Muestra la lista de cuestionarios asignados al usuario."""
    cuestionarios = set()
    try:
        perfil = PerfilUsuario.objects.get(usuario=request.user)
        for c in perfil.cuestionarios_asignados.all():
            cuestionarios.add(c)
        for modulo in perfil.modulos_permitidos.all():
            for c in modulo.cuestionarios.all():
                cuestionarios.add(c)
    except PerfilUsuario.DoesNotExist:
        pass
    contexto = { 'lista_cuestionarios': sorted(list(cuestionarios), key=lambda x: x.titulo) }
    return render(request, 'evaluacion_list.html', contexto)

@login_required(login_url='login')
def tomar_evaluacion_view(request, cuestionario_id):
    """Presenta el cuestionario y procesa las respuestas."""
    cuestionario = get_object_or_404(Cuestionario.objects.prefetch_related('preguntas__opciones'), id=cuestionario_id)
    hoy = timezone.now().date()
    intentos_hoy = ResultadoCuestionario.objects.filter(usuario=request.user, cuestionario=cuestionario, fecha_inicio__date=hoy).exists()
    if intentos_hoy:
        return render(request, 'evaluacion_bloqueada.html')

    if request.method == 'POST':
        puntos_obtenidos = 0
        puntos_totales = 0
        resultado = ResultadoCuestionario.objects.create(usuario=request.user, cuestionario=cuestionario, completado=False)
        for pregunta in cuestionario.preguntas.all():
            puntos_totales += pregunta.valor
            opcion_seleccionada_id = request.POST.get(f'pregunta_{pregunta.id}')
            if opcion_seleccionada_id:
                try:
                    opcion_seleccionada = Opcion.objects.get(id=opcion_seleccionada_id)
                    RespuestaUsuario.objects.create(resultado=resultado, pregunta=pregunta, opcion_seleccionada=opcion_seleccionada)
                    if opcion_seleccionada.es_correcta:
                        puntos_obtenidos += pregunta.valor
                except Opcion.DoesNotExist:
                    pass # Ignorar si la opción no es válida
        puntaje_final = (puntos_obtenidos / puntos_totales) * 100 if puntos_totales > 0 else 0
        resultado.puntaje = puntaje_final
        resultado.completado = True
        resultado.save()
        return redirect('resultado_evaluacion', resultado_id=resultado.id)

    contexto = { 'cuestionario': cuestionario }
    return render(request, 'tomar_evaluacion.html', contexto)

@login_required(login_url='login')
def resultado_evaluacion_view(request, resultado_id):
    """Muestra un mensaje de finalización (oculta el resultado)."""
    resultado = get_object_or_404(ResultadoCuestionario, id=resultado_id, usuario=request.user)
    contexto = {'cuestionario': resultado.cuestionario}
    return render(request, 'resultado_evaluacion.html', contexto)

# --- FUNCIÓN DE AYUDA ---
def agrupar_por_mes(mapa_datos, nombres_mes):
    """Agrupa un diccionario de facturas por mes de emisión."""
    datos_agrupados = OrderedDict()
    for mes_nombre in nombres_mes.values():
        datos_agrupados[mes_nombre] = []
    for uuid, item in mapa_datos.items():
        mes_emision = item.get("Mes de Emisión")
        if mes_emision in nombres_mes:
            nombre_del_mes = nombres_mes[mes_emision]
            datos_agrupados[nombre_del_mes].append(item)
    return {mes: sorted(facturas, key=lambda x: x['Fecha']) for mes, facturas in datos_agrupados.items() if facturas}