# command_handler.py
# Author: Joan Cobeña
# Description: Módulo para manejar comandos relacionados con procesos.

from process_manager import crear_proceso, listar_procesos, eliminar_proceso, modificar_proceso
from system_metrics import system_monitor
import json

# Definición de los formatos de respuesta del protocolo
def formato_ok(mensaje):
    return f"OK|{mensaje}"

def formato_error(mensaje):
    return f"ERROR|{mensaje}"

def formato_datos(datos):
    return f"DATOS|{datos}"

"""
    Procesa un comando de gestión de procesos.
    cmd: Comando a procesar.
    Retorna un mensaje indicando el resultado de la operación.
    Los comandos válidos son:
    - CREAR|<nombre>|<prioridad>
    - LISTAR
    - ELIMINAR|<id>
    - MODIFICAR|<id>|<campo>|<valor>
"""
def procesar_comando(cmd):
    # 1. Usamos el delimitador |
    partes = cmd.strip().split('|')
    if not partes:
        return formato_error("Comando vacío.")

    accion = partes[0].lower()
    
    try:
        if accion == "crear":
            if len(partes) != 3:
                return formato_error("Argumentos inválidos para CREAR. Se necesita: CREAR|nombre|prioridad")
            _, nombre, prioridad = partes
            ok, msg = crear_proceso(nombre, prioridad)
            return formato_ok(msg) if ok else formato_error(msg)

        elif accion == "listar":
            datos_procesos = listar_procesos()
            return formato_datos(datos_procesos)

        elif accion == "eliminar":
            if len(partes) != 2:
                return formato_error("Argumentos inválidos para ELIMINAR. Se necesita: ELIMINAR|id")
            _, id_ = partes
            ok, msg = eliminar_proceso(id_)
            return formato_ok(msg) if ok else formato_error(msg)
            
        elif accion == "modificar":
            if len(partes) != 4:
                return formato_error("Argumentos inválidos para MODIFICAR. Se necesita: MODIFICAR|id|campo|valor")
            _, id_, campo, valor = partes
            ok, msg = modificar_proceso(id_, campo, valor)
            return formato_ok(msg) if ok else formato_error(msg)
        
        elif accion == "ayuda":
            ayuda = (
                "Comandos disponibles:\n"
                "CREAR|<nombre>|<prioridad> - Crea un nuevo proceso.\n"
                "LISTAR - Lista todos los procesos.\n"
                "ELIMINAR|<id> - Elimina un proceso por su ID.\n"
                "MODIFICAR|<id>|<campo>|<valor> - Modifica un campo de un proceso.\n"
                "METRICAS - Obtiene métricas actuales del sistema.\n"
                "HISTORIAL_CPU|<limite> - Obtiene historial de CPU.\n"
                "HISTORIAL_MEMORIA|<limite> - Obtiene historial de memoria.\n"
                "PROCESOS_REALES - Lista procesos reales del sistema.\n"
                "INFO_SISTEMA - Información general del sistema.\n"
                "SALIR - Desconecta del servidor."
            )
            return formato_datos(ayuda)
        
        elif accion == "metricas":
            metricas = system_monitor.get_current_metrics()
            return formato_datos(json.dumps(metricas))
        
        elif accion == "historial_cpu":
            limite = int(partes[1]) if len(partes) > 1 else 50
            historial = system_monitor.get_cpu_history(limite)
            return formato_datos(json.dumps(historial))
        
        elif accion == "historial_memoria":
            limite = int(partes[1]) if len(partes) > 1 else 50
            historial = system_monitor.get_memory_history(limite)
            return formato_datos(json.dumps(historial))
        
        elif accion == "historial_disco":
            limite = int(partes[1]) if len(partes) > 1 else 50
            historial = system_monitor.get_disk_history(limite)
            return formato_datos(json.dumps(historial))
        
        elif accion == "historial_red":
            limite = int(partes[1]) if len(partes) > 1 else 50
            historial = system_monitor.get_network_history(limite)
            return formato_datos(json.dumps(historial))
        
        elif accion == "procesos_reales":
            procesos_reales = system_monitor.get_real_processes()
            return formato_datos(json.dumps(procesos_reales))
        
        elif accion == "info_sistema":
            info = system_monitor.get_system_info()
            return formato_datos(json.dumps(info))
        
        elif accion == "todas_metricas":
            todas = system_monitor.get_all_metrics_json()
            return formato_datos(todas)

        elif accion == "salir":
            return "SALIR|Desconectando."

        else:
            return formato_error("Comando no reconocido.")
            
    except Exception as e:
        return formato_error(f"Error inesperado en el servidor: {str(e)}")