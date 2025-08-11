# system_metrics.py
# Author: Módulo de métricas del sistema
# Description: Obtiene métricas reales de CPU, memoria y procesos del sistema

import psutil
import threading
import time
import json
from datetime import datetime
from collections import deque

class SystemMetrics:
    """Clase para recopilar y gestionar métricas del sistema"""
    
    def __init__(self, history_size=100):
        self.history_size = history_size
        self.cpu_history = deque(maxlen=history_size)
        self.memory_history = deque(maxlen=history_size)
        self.disk_history = deque(maxlen=history_size)
        self.network_history = deque(maxlen=history_size)
        self.process_count_history = deque(maxlen=history_size)
        
        self.lock = threading.Lock()
        self.monitoring = False
        self.monitor_thread = None
        
        # Métricas actuales
        self.current_metrics = {
            'cpu_percent': 0.0,
            'memory': {'percent': 0.0, 'used': 0, 'total': 0, 'available': 0},
            'disk': {'percent': 0.0, 'used': 0, 'total': 0, 'free': 0},
            'network': {'bytes_sent': 0, 'bytes_recv': 0},
            'processes': {'total': 0, 'running': 0, 'sleeping': 0},
            'timestamp': datetime.now().isoformat()
        }
    
    def start_monitoring(self, interval=1.0):
        """Inicia el monitoreo continuo del sistema"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,), daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Detiene el monitoreo del sistema"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
    
    def _monitor_loop(self, interval):
        """Loop principal de monitoreo"""
        last_network = psutil.net_io_counters()
        
        while self.monitoring:
            try:
                # CPU
                cpu_percent = psutil.cpu_percent(interval=0.1)
                
                # Memoria
                memory = psutil.virtual_memory()
                
                # Disco (partición principal)
                disk = psutil.disk_usage('/')
                
                # Red
                current_network = psutil.net_io_counters()
                network_diff = {
                    'bytes_sent': current_network.bytes_sent - last_network.bytes_sent,
                    'bytes_recv': current_network.bytes_recv - last_network.bytes_recv
                }
                last_network = current_network
                
                # Procesos
                processes = list(psutil.process_iter(['status']))
                process_stats = {
                    'total': len(processes),
                    'running': len([p for p in processes if p.info['status'] == psutil.STATUS_RUNNING]),
                    'sleeping': len([p for p in processes if p.info['status'] == psutil.STATUS_SLEEPING])
                }
                
                timestamp = datetime.now().isoformat()
                
                # Actualizar métricas actuales
                with self.lock:
                    self.current_metrics = {
                        'cpu_percent': round(cpu_percent, 2),
                        'memory': {
                            'percent': round(memory.percent, 2),
                            'used': memory.used,
                            'total': memory.total,
                            'available': memory.available
                        },
                        'disk': {
                            'percent': round(disk.percent, 2),
                            'used': disk.used,
                            'total': disk.total,
                            'free': disk.free
                        },
                        'network': network_diff,
                        'processes': process_stats,
                        'timestamp': timestamp
                    }
                    
                    # Agregar a historial
                    self.cpu_history.append({'value': cpu_percent, 'timestamp': timestamp})
                    self.memory_history.append({'value': memory.percent, 'timestamp': timestamp})
                    self.disk_history.append({'value': disk.percent, 'timestamp': timestamp})
                    self.network_history.append({
                        'sent': network_diff['bytes_sent'],
                        'recv': network_diff['bytes_recv'],
                        'timestamp': timestamp
                    })
                    self.process_count_history.append({'value': process_stats['total'], 'timestamp': timestamp})
                
                time.sleep(interval)
                
            except Exception as e:
                print(f"Error en monitoreo del sistema: {e}")
                time.sleep(interval)
    
    def get_current_metrics(self):
        """Obtiene las métricas actuales del sistema"""
        with self.lock:
            return self.current_metrics.copy()
    
    def get_cpu_history(self, limit=None):
        """Obtiene el historial de uso de CPU"""
        with self.lock:
            history = list(self.cpu_history)
            return history[-limit:] if limit else history
    
    def get_memory_history(self, limit=None):
        """Obtiene el historial de uso de memoria"""
        with self.lock:
            history = list(self.memory_history)
            return history[-limit:] if limit else history
    
    def get_disk_history(self, limit=None):
        """Obtiene el historial de uso de disco"""
        with self.lock:
            history = list(self.disk_history)
            return history[-limit:] if limit else history
    
    def get_network_history(self, limit=None):
        """Obtiene el historial de red"""
        with self.lock:
            history = list(self.network_history)
            return history[-limit:] if limit else history
    
    def get_process_history(self, limit=None):
        """Obtiene el historial de conteo de procesos"""
        with self.lock:
            history = list(self.process_count_history)
            return history[-limit:] if limit else history
    
    def get_all_metrics_json(self):
        """Obtiene todas las métricas en formato JSON"""
        with self.lock:
            data = {
                'current': self.current_metrics,
                'history': {
                    'cpu': list(self.cpu_history)[-50:],  # Últimos 50 puntos
                    'memory': list(self.memory_history)[-50:],
                    'disk': list(self.disk_history)[-50:],
                    'network': list(self.network_history)[-50:],
                    'processes': list(self.process_count_history)[-50:]
                }
            }
            return json.dumps(data, indent=2)
    
    def get_real_processes(self):
        """Obtiene información de procesos reales del sistema"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_percent']):
                try:
                    proc_info = proc.info
                    processes.append({
                        'pid': proc_info['pid'],
                        'name': proc_info['name'] or 'N/A',
                        'status': proc_info['status'],
                        'cpu_percent': round(proc_info['cpu_percent'] or 0, 2),
                        'memory_percent': round(proc_info['memory_percent'] or 0, 2)
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Ordenar por uso de CPU descendente
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            return processes[:20]  # Top 20 procesos
            
        except Exception as e:
            return [{'error': f"Error obteniendo procesos: {str(e)}"}]
    
    def get_system_info(self):
        """Obtiene información general del sistema"""
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            cpu_count = psutil.cpu_count()
            cpu_count_logical = psutil.cpu_count(logical=True)
            
            return {
                'platform': psutil.PLATFORM,
                'boot_time': boot_time.isoformat(),
                'cpu_count_physical': cpu_count,
                'cpu_count_logical': cpu_count_logical,
                'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
                'disk_total_gb': round(psutil.disk_usage('/').total / (1024**3), 2)
            }
        except Exception as e:
            return {'error': f"Error obteniendo info del sistema: {str(e)}"}

# Instancia global del monitor
system_monitor = SystemMetrics()
