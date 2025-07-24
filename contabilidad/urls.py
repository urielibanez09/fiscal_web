from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('', views.main_dashboard_view, name='main_dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('clientes/', views.cliente_list_view, name='cliente_list'),

    # Rutas para los módulos de cada cliente
    path('cliente/<int:cliente_id>/', views.dashboard_cliente_view, name='cliente_dashboard'),
    path('cliente/<int:cliente_id>/expediente/', views.expediente_view, name='expediente'),
    path('cliente/<int:cliente_id>/xmls/', views.xml_viewer_view, name='xml_viewer_default'),
    path('cliente/<int:cliente_id>/xmls/<int:anio>/', views.xml_viewer_view, name='xml_viewer'),
    path('cliente/<int:cliente_id>/iva/', views.iva_view, name='iva'),

    # Rutas para el Módulo de Evaluación
    path('importar-cuestionario/', views.importar_cuestionario_view, name='importar_cuestionario'),
    path('evaluaciones/', views.evaluacion_list_view, name='evaluacion_list'),
    path('evaluacion/tomar/<int:cuestionario_id>/', views.tomar_evaluacion_view, name='tomar_evaluacion'),

    # --- INICIO DE LA CORRECCIÓN ---
    # Añadimos la URL para la vista de resultados que faltaba
    path('evaluacion/resultado/<int:resultado_id>/', views.resultado_evaluacion_view, name='resultado_evaluacion'),
    # --- FIN DE LA CORRECCIÓN ---
]