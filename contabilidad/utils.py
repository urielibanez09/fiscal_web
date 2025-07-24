# contabilidad/utils.py

import os
import xml.etree.ElementTree as ET
from datetime import datetime

def parsear_cfdi(xml_path):
    try:
        ns = {'cfdi': 'http://www.sat.gob.mx/cfd/4', 'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'}
        tree = ET.parse(xml_path)
        root = tree.getroot()
        datos = {
            "Fecha": root.get('Fecha'), "Subtotal": float(root.get('SubTotal', 0)),
            "Total": float(root.get('Total', 0)), "TipoDeComprobante": root.get('TipoDeComprobante')
        }
        emisor = root.find('cfdi:Emisor', ns); receptor = root.find('cfdi:Receptor', ns)
        datos["RFC Emisor"] = emisor.get('Rfc') if emisor is not None else 'N/A'
        datos["Nombre Emisor"] = emisor.get('Nombre') if emisor is not None else 'N/A'
        datos["RFC Receptor"] = receptor.get('Rfc') if receptor is not None else 'N/A'
        datos["Nombre Receptor"] = receptor.get('Nombre') if receptor is not None else 'N/A'
        tfd_node = root.find('cfdi:Complemento/tfd:TimbreFiscalDigital', ns)
        datos["UUID"] = tfd_node.get('UUID', 'N/A') if tfd_node is not None else 'N/A'
        return datos
    except Exception:
        return None

def procesar_seleccion(base_path, rfc_cliente, anio):
    mapa_ingresos, mapa_egresos = {}, {}
    for tipo_op in ['emitidos', 'recibidos']:
        path_anio = os.path.join(base_path, rfc_cliente, tipo_op, str(anio))
        if not os.path.isdir(path_anio): continue
        for mes_folder in os.listdir(path_anio):
            path_mes = os.path.join(path_anio, mes_folder)
            if not os.path.isdir(path_mes): continue
            for file in os.listdir(path_mes):
                if file.lower().endswith('.xml'):
                    xml_path = os.path.join(path_mes, file)
                    datos_cfdi = parsear_cfdi(xml_path)
                    if datos_cfdi and datos_cfdi["UUID"] != 'N/A':
                        datos_cfdi["Estado"] = "Cancelado" if "cancelados" in mes_folder.lower() else "Vigente"
                        try:
                            fecha_dt = datetime.fromisoformat(datos_cfdi["Fecha"].split('T')[0])
                            mes_num = f"{fecha_dt.month:02d}"
                            datos_cfdi["Mes de Emisión"] = mes_num
                        except:
                            datos_cfdi["Mes de Emisión"] = ""
                        if datos_cfdi["RFC Emisor"] == rfc_cliente: mapa_ingresos[datos_cfdi["UUID"]] = datos_cfdi
                        elif datos_cfdi["RFC Receptor"] == rfc_cliente: mapa_egresos[datos_cfdi["UUID"]] = datos_cfdi
    return mapa_ingresos, mapa_egresos