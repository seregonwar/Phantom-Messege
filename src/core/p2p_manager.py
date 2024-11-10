import socket
import threading
import json
import logging
from datetime import datetime
import uuid
from typing import Dict, Optional
from PyQt6.QtCore import QObject, pyqtSignal
import time

class P2PManager(QObject):
    # Signals
    device_connected = pyqtSignal(dict)  # Emesso quando un dispositivo si connette
    device_disconnected = pyqtSignal(str)  # Emesso quando un dispositivo si disconnette
    device_updated = pyqtSignal(dict)  # Emesso quando si ricevono aggiornamenti
    message_received = pyqtSignal(str, str)  # hardware_id, message
    
    def __init__(self, port: int = 5555):
        super().__init__()
        self.port = port
        self.devices: Dict[str, dict] = {}  # hardware_id -> device_info
        self.connections: Dict[str, socket.socket] = {}  # hardware_id -> socket
        self.running = False
        self.server_socket = None
        self._session_id = str(uuid.uuid4())
        self.reconnect_interval = 30  # secondi
        self.max_reconnect_attempts = 5
        self._reconnect_attempts = {}
        
        # Avvia thread di riconnessione
        self._start_reconnect_thread()
        
    def _start_reconnect_thread(self):
        """Avvia thread per gestire le riconnessioni"""
        def reconnect_loop():
            while self.running:
                try:
                    # Controlla dispositivi disconnessi
                    for hardware_id, device in list(self.devices.items()):
                        if hardware_id not in self.connections:
                            if self._should_attempt_reconnect(hardware_id):
                                self._attempt_reconnect(hardware_id, device)
                except Exception as e:
                    logging.error(f"Error in reconnect loop: {e}")
                finally:
                    time.sleep(self.reconnect_interval)
                    
        threading.Thread(target=reconnect_loop, daemon=True).start()
        
    def _should_attempt_reconnect(self, hardware_id: str) -> bool:
        """Verifica se tentare la riconnessione"""
        attempts = self._reconnect_attempts.get(hardware_id, 0)
        if attempts >= self.max_reconnect_attempts:
            return False
            
        last_attempt = self.devices[hardware_id].get('last_reconnect_attempt')
        if last_attempt:
            time_since_attempt = (datetime.now() - datetime.fromisoformat(last_attempt)).total_seconds()
            return time_since_attempt > self.reconnect_interval
            
        return True
        
    def _attempt_reconnect(self, hardware_id: str, device: dict):
        """Tenta la riconnessione a un dispositivo"""
        try:
            self.devices[hardware_id]['last_reconnect_attempt'] = datetime.now().isoformat()
            self._reconnect_attempts[hardware_id] = self._reconnect_attempts.get(hardware_id, 0) + 1
            
            if self.connect_to_device(device['ip_address'], hardware_id):
                logging.info(f"Successfully reconnected to {hardware_id}")
                self._reconnect_attempts[hardware_id] = 0
            else:
                logging.warning(f"Failed to reconnect to {hardware_id}")
                
        except Exception as e:
            logging.error(f"Error attempting reconnect: {e}")
        
    def start(self):
        """Avvia il server P2P"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(5)
            self.running = True
            
            # Thread per accettare connessioni
            threading.Thread(target=self._accept_connections, daemon=True).start()
            
            # Thread per il monitoraggio delle connessioni
            threading.Thread(target=self._monitor_connections, daemon=True).start()
            
            logging.info(f"P2P server started on port {self.port}")
            return True
            
        except Exception as e:
            logging.error(f"Error starting P2P server: {e}")
            return False
            
    def stop(self):
        """Ferma il server P2P"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
            
        # Chiudi tutte le connessioni
        for conn in self.connections.values():
            try:
                conn.close()
            except:
                pass
                
        self.connections.clear()
        self.devices.clear()
        
    def connect_to_device(self, ip: str, hardware_id: str) -> bool:
        """Connette a un dispositivo specifico"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip, self.port))
            
            # Invia info di connessione
            self._send_data(sock, {
                'type': 'connect',
                'hardware_id': hardware_id,
                'session_id': self._session_id
            })
            
            # Avvia thread per gestire i messaggi
            threading.Thread(
                target=self._handle_connection,
                args=(sock, hardware_id),
                daemon=True
            ).start()
            
            self.connections[hardware_id] = sock
            return True
            
        except Exception as e:
            logging.error(f"Error connecting to device {hardware_id}: {e}")
            return False
            
    def send_message(self, hardware_id: str, message: str) -> bool:
        """Invia un messaggio a un dispositivo"""
        if hardware_id not in self.connections:
            return False
            
        try:
            self._send_data(self.connections[hardware_id], {
                'type': 'message',
                'content': message,
                'timestamp': datetime.now().isoformat()
            })
            return True
        except:
            return False
            
    def get_device_info(self, hardware_id: str) -> Optional[dict]:
        """Ottiene informazioni su un dispositivo"""
        return self.devices.get(hardware_id)
        
    def get_connected_devices(self) -> list:
        """Ottiene la lista dei dispositivi connessi"""
        return list(self.devices.values())
        
    def _accept_connections(self):
        """Loop per accettare nuove connessioni"""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                # Gestisci la nuova connessione in un thread separato
                threading.Thread(
                    target=self._handle_new_connection,
                    args=(client_socket, address),
                    daemon=True
                ).start()
            except:
                if self.running:
                    logging.error("Error accepting connection")
                    
    def _handle_new_connection(self, client_socket: socket.socket, address: tuple):
        """Gestisce una nuova connessione"""
        try:
            # Ricevi info di connessione
            data = self._receive_data(client_socket)
            if not data or data.get('type') != 'connect':
                client_socket.close()
                return
                
            hardware_id = data['hardware_id']
            
            # Aggiungi alla lista connessioni
            self.connections[hardware_id] = client_socket
            
            # Richiedi info dispositivo
            self._send_data(client_socket, {
                'type': 'get_info',
                'session_id': self._session_id
            })
            
            # Gestisci i messaggi
            self._handle_connection(client_socket, hardware_id)
            
        except Exception as e:
            logging.error(f"Error handling new connection: {e}")
            client_socket.close()
            
    def _handle_connection(self, sock: socket.socket, hardware_id: str):
        """Gestisce i messaggi da una connessione"""
        while self.running:
            try:
                data = self._receive_data(sock)
                if not data:
                    break
                    
                if data['type'] == 'info':
                    # Aggiorna info dispositivo
                    self.devices[hardware_id] = data['info']
                    self.device_updated.emit(data['info'])
                    
                elif data['type'] == 'message':
                    # Gestisci messaggio
                    self.message_received.emit(hardware_id, data['content'])
                    
            except:
                break
                
        # Connessione persa
        self._handle_disconnect(hardware_id)
        
    def _handle_disconnect(self, hardware_id: str):
        """Gestisce la disconnessione di un dispositivo"""
        if hardware_id in self.connections:
            self.connections[hardware_id].close()
            del self.connections[hardware_id]
            
        if hardware_id in self.devices:
            del self.devices[hardware_id]
            
        self.device_disconnected.emit(hardware_id)
        
    def _monitor_connections(self):
        """Monitora lo stato delle connessioni"""
        while self.running:
            for hardware_id, sock in list(self.connections.items()):
                try:
                    # Invia ping
                    self._send_data(sock, {'type': 'ping'})
                except:
                    # Connessione persa
                    self._handle_disconnect(hardware_id)
                    
            threading.Event().wait(30)  # Check ogni 30 secondi
            
    def _send_data(self, sock: socket.socket, data: dict):
        """Invia dati su un socket"""
        message = json.dumps(data).encode()
        sock.sendall(len(message).to_bytes(4, 'big'))
        sock.sendall(message)
        
    def _receive_data(self, sock: socket.socket) -> Optional[dict]:
        """Ricevi dati da un socket"""
        try:
            length = int.from_bytes(sock.recv(4), 'big')
            message = sock.recv(length).decode()
            return json.loads(message)
        except:
            return None 