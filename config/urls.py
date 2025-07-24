from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Esta línea le dice a Django que busque todas las demás URLs
    # en el archivo urls.py de nuestra app 'contabilidad'
    path('', include('contabilidad.urls')),
]