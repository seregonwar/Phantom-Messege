import sqlite3
import os
import json
from datetime import datetime, timedelta
import logging
from src.core.dropbox_sync import DropboxSync

class LicenseDBManager:
    def __init__(self):
        self.db_path = os.path.join("database", "generated_licenses.db")
        self.dropbox = DropboxSync()
        self._initialize_database()
        self._sync_with_dropbox()
    
    def _initialize_database(self):
        """Initialize the database and create tables if they don't exist"""
        os.makedirs("database", exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Drop existing tables to recreate with new structure
            cursor.execute("DROP TABLE IF EXISTS active_devices")
            cursor.execute("DROP TABLE IF EXISTS device_history")
            cursor.execute("DROP TABLE IF EXISTS generated_licenses")
            cursor.execute("DROP TABLE IF EXISTS remote_commands")
            
            # Create tables with updated structure
            cursor.execute('''
                CREATE TABLE generated_licenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    license_key TEXT NOT NULL,
                    hardware_id TEXT,
                    type TEXT NOT NULL,
                    valid_days INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    expiration_date TEXT NOT NULL,
                    metadata TEXT,
                    file_path TEXT,
                    status TEXT DEFAULT 'active'
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE active_devices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hardware_id TEXT NOT NULL,
                    license_key TEXT NOT NULL,
                    activation_date TEXT NOT NULL,
                    last_check TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    system_info TEXT,
                    ip_address TEXT,
                    location TEXT,
                    hostname TEXT,
                    username TEXT,
                    last_ping TEXT,
                    UNIQUE(hardware_id, license_key)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE device_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hardware_id TEXT NOT NULL,
                    license_key TEXT NOT NULL,
                    action TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE remote_commands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hardware_id TEXT NOT NULL,
                    command_type TEXT NOT NULL,
                    command_data TEXT,
                    issued_at TEXT NOT NULL,
                    executed_at TEXT,
                    status TEXT DEFAULT 'pending'
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hardware_id TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    read_at TEXT
                )
            ''')
            
            # Tabelle per il supporto
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS support_tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject TEXT NOT NULL,
                    category TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    closed_at TEXT,
                    resolution TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ticket_responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id INTEGER NOT NULL,
                    sender TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (ticket_id) REFERENCES support_tickets(id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS support_agents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    status TEXT NOT NULL,
                    last_active TEXT,
                    specialties TEXT,
                    max_concurrent_chats INTEGER DEFAULT 3
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agent_chat_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id INTEGER NOT NULL,
                    client_id TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    status TEXT NOT NULL,
                    rating INTEGER,
                    feedback TEXT,
                    FOREIGN KEY (agent_id) REFERENCES support_agents(id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    sender TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    read_at TEXT,
                    FOREIGN KEY (session_id) REFERENCES agent_chat_sessions(id)
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_license_key ON generated_licenses(license_key)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_hardware_id ON active_devices(hardware_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_device_history ON device_history(hardware_id, license_key)')
            
            conn.commit()
    
    def _sync_with_dropbox(self):
        """Sincronizza il database locale con Dropbox"""
        try:
            # Ottieni tutte le licenze da Dropbox
            dropbox_licenses = self.dropbox.get_all_licenses()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for license in dropbox_licenses:
                    # Aggiorna o inserisci la licenza
                    cursor.execute('''
                        INSERT OR REPLACE INTO generated_licenses 
                        (license_key, hardware_id, type, valid_days, created_at, 
                         expiration_date, metadata, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        license['license_key'],
                        license['hardware_id'],
                        license['data'].get('type', 'UNKNOWN'),
                        license['data'].get('valid_days', 0),
                        license['created_at'],
                        (datetime.fromisoformat(license['created_at']) + 
                         timedelta(days=license['data'].get('valid_days', 0))).isoformat(),
                        json.dumps(license['data']),
                        license['status']
                    ))
                    
                    # Se ci sono informazioni sul dispositivo, aggiornale
                    if license.get('device_info'):
                        self.add_device(
                            license['hardware_id'],
                            license['license_key'],
                            license['device_info']
                        )
                
                conn.commit()
            logging.info(f"Synced {len(dropbox_licenses)} licenses from Dropbox")
            
        except Exception as e:
            logging.error(f"Error syncing with Dropbox: {e}")
    
    def save_license(self, key: str, metadata: dict, file_path: str) -> bool:
        """Save a generated license to the database and Dropbox"""
        try:
            # Salva nel database locale
            result = super().save_license(key, metadata, file_path)
            if not result:
                return False
                
            # Carica su Dropbox
            if not self.dropbox.upload_license(key, metadata.get('hardware_id'), metadata):
                logging.error("Failed to upload license to Dropbox")
                return False
                
            return True
            
        except Exception as e:
            logging.error(f"Error saving license: {e}")
            return False
    
    def get_all_devices(self) -> list:
        """Get all devices with latest Dropbox sync"""
        try:
            self._sync_with_dropbox()  # Sincronizza prima di ottenere i dispositivi
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 
                        d.*,
                        l.type as license_type,
                        l.expiration_date,
                        COUNT(h.id) as activation_count
                    FROM active_devices d
                    LEFT JOIN generated_licenses l ON d.license_key = l.license_key
                    LEFT JOIN device_history h ON d.hardware_id = h.hardware_id
                    GROUP BY d.hardware_id, d.license_key
                    ORDER BY d.last_check DESC
                ''')
                devices = [dict(row) for row in cursor.fetchall()]
                
                # Aggiungi informazioni aggiuntive per ogni dispositivo
                for device in devices:
                    # Ottieni statistiche di utilizzo
                    device['usage_stats'] = self.get_device_usage_stats(device['hardware_id'])
                    
                    # Ottieni storico attività
                    device['activity_history'] = self.get_device_history(device['hardware_id'])
                    
                    # Decodifica le informazioni JSON
                    try:
                        device['system_info'] = device['system_info'] or '{}'
                        device['location'] = device['location'] or '{}'
                    except:
                        device['system_info'] = '{}'
                        device['location'] = '{}'
                
                logging.info(f"Found {len(devices)} devices")
                return devices
                
        except Exception as e:
            logging.error(f"Error getting devices: {e}")
            return []
    
    def revoke_device(self, hardware_id: str, license_key: str) -> bool:
        """Revoke device access and sync with Dropbox"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Aggiorna lo stato del dispositivo
                cursor.execute('''
                    UPDATE active_devices 
                    SET status = 'revoked',
                        last_check = ?
                    WHERE hardware_id = ? AND license_key = ?
                ''', (
                    datetime.now().isoformat(),
                    hardware_id, 
                    license_key
                ))
                
                # Aggiungi al registro storico
                cursor.execute('''
                    INSERT INTO device_history
                    (hardware_id, license_key, action, timestamp)
                    VALUES (?, ?, 'revoked', ?)
                ''', (
                    hardware_id,
                    license_key,
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                
                # Revoca su Dropbox
                if self.dropbox:
                    if not self.dropbox.revoke_license(
                        license_key, 
                        f"Revoked for device {hardware_id}"
                    ):
                        logging.error("Failed to revoke on Dropbox")
                        return False
                        
                return True
                
        except Exception as e:
            logging.error(f"Error revoking device: {e}")
            return False
    
    def update_device_info(self, hardware_id: str, system_info: dict) -> bool:
        """Update device information and sync with Dropbox"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Aggiorna le informazioni del dispositivo
                cursor.execute('''
                    UPDATE active_devices
                    SET system_info = ?,
                        last_check = ?,
                        ip_address = ?,
                        location = ?,
                        hostname = ?,
                        username = ?
                    WHERE hardware_id = ?
                ''', (
                    json.dumps(system_info.get('system', {})),
                    datetime.now().isoformat(),
                    system_info.get('ip_address', ''),
                    json.dumps(system_info.get('location', {})),
                    system_info.get('hostname', ''),
                    system_info.get('username', ''),
                    hardware_id
                ))
                
                # Ottieni la licenza associata
                cursor.execute('''
                    SELECT license_key FROM active_devices
                    WHERE hardware_id = ?
                ''', (hardware_id,))
                
                result = cursor.fetchone()
                if result:
                    # Aggiorna le informazioni su Dropbox
                    license_key = result[0]
                    license_info = self.get_license_by_key(license_key)
                    if license_info:
                        self.dropbox.upload_license(
                            license_key,
                            hardware_id,
                            json.loads(license_info['metadata']),
                            system_info
                        )
                
                conn.commit()
                return True
                
        except Exception as e:
            logging.error(f"Error updating device info: {e}")
            return False
    
    def get_device_history(self, hardware_id: str) -> str:
        """Get activity history for a device"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT license_key, action, timestamp
                FROM device_history
                WHERE hardware_id = ?
                ORDER BY timestamp DESC
            ''', (hardware_id,))
            
            history = cursor.fetchall()
            if not history:
                return "Nessuna attività registrata"
                
            return "\n".join(
                f"- {row[0]}: {row[1]} ({row[2]})"
                for row in history
            )
    
    def get_all_licenses(self) -> list:
        """Get all generated licenses"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT l.*, 
                       COALESCE(d.hardware_id, 'Non attivata') as active_device,
                       COALESCE(d.activation_date, 'N/A') as device_activation,
                       COALESCE(d.status, 'inactive') as device_status
                FROM generated_licenses l
                LEFT JOIN active_devices d ON l.license_key = d.license_key
                ORDER BY l.created_at DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_license_by_key(self, key: str) -> dict:
        """Get license details by key"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT l.*, 
                       d.hardware_id as active_device,
                       d.activation_date as device_activation,
                       d.status as device_status
                FROM generated_licenses l
                LEFT JOIN active_devices d ON l.license_key = d.license_key
                WHERE l.license_key = ?
            ''', (key,))
            result = cursor.fetchone()
            return dict(result) if result else None
    
    def update_license_status(self, key: str, updates: dict) -> bool:
        """Update license status and metadata"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if isinstance(updates, str):
                    # Se updates è una stringa, è uno stato
                    cursor.execute('''
                        UPDATE generated_licenses 
                        SET status = ? 
                        WHERE license_key = ?
                    ''', (updates, key))
                else:
                    # Se updates è un dict, aggiorna i metadati
                    license_data = self.get_license_by_key(key)
                    if not license_data:
                        return False
                        
                    metadata = json.loads(license_data['metadata'])
                    metadata.update(updates)
                    
                    cursor.execute('''
                        UPDATE generated_licenses 
                        SET metadata = ?
                        WHERE license_key = ?
                    ''', (json.dumps(metadata), key))
                
                conn.commit()
                
                # Aggiorna anche su Dropbox
                if self.dropbox:
                    if isinstance(updates, str):
                        if updates == 'revoked':
                            self.dropbox.revoke_license(key, "Revoked from local database")
                    else:
                        self.dropbox.update_license(key, updates)
                
                return True
                
        except Exception as e:
            logging.error(f"Error updating license status: {e}")
            return False
    
    def add_device(self, hardware_id: str, license_key: str, system_info: dict) -> bool:
        """Add a new device activation with system information"""
        try:
            now = datetime.now().isoformat()
            
            # Estrai le informazioni dal dizionario system_info
            system_data = json.dumps(system_info.get('system', {}))
            ip_address = system_info.get('ip_address', '')
            location = json.dumps(system_info.get('location', {}))
            hostname = system_info.get('hostname', '')
            username = system_info.get('username', '')
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO active_devices 
                    (hardware_id, license_key, activation_date, last_check, status,
                     system_info, ip_address, location, hostname, username, last_ping)
                    VALUES (?, ?, ?, ?, 'active', ?, ?, ?, ?, ?, ?)
                ''', (
                    hardware_id, 
                    license_key, 
                    now, 
                    now,
                    system_data,  # JSON string
                    ip_address,   # string
                    location,     # JSON string
                    hostname,     # string
                    username,     # string
                    now
                ))
                
                cursor.execute('''
                    INSERT INTO device_history 
                    (hardware_id, license_key, action, timestamp)
                    VALUES (?, ?, 'activated', ?)
                ''', (hardware_id, license_key, now))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error adding device: {e}")
            return False
    
    def get_device_usage_stats(self, hardware_id: str) -> dict:
        """Get detailed usage statistics for a device"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Ottieni il numero totale di attivazioni
            cursor.execute('''
                SELECT COUNT(*) 
                FROM device_history 
                WHERE hardware_id = ? AND action = 'activated'
            ''', (hardware_id,))
            total_activations = cursor.fetchone()[0]
            
            # Calcola i giorni totali di utilizzo
            cursor.execute('''
                SELECT 
                    MIN(activation_date) as first_activation,
                    MAX(last_check) as last_check
                FROM active_devices
                WHERE hardware_id = ?
            ''', (hardware_id,))
            dates = cursor.fetchone()
            
            total_days_used = 0
            if dates[0] and dates[1]:
                first = datetime.fromisoformat(dates[0])
                last = datetime.fromisoformat(dates[1])
                total_days_used = (last - first).days + 1
            
            # Calcola la durata dell'ultima sessione
            cursor.execute('''
                SELECT 
                    activation_date,
                    last_check
                FROM active_devices
                WHERE hardware_id = ?
                ORDER BY last_check DESC
                LIMIT 1
            ''', (hardware_id,))
            last_session = cursor.fetchone()
            
            last_session_duration = 0
            if last_session:
                start = datetime.fromisoformat(last_session[0])
                end = datetime.fromisoformat(last_session[1])
                last_session_duration = round((end - start).total_seconds() / 60)  # in minuti
            
            # Calcola il tempo totale di utilizzo
            cursor.execute('''
                SELECT 
                    SUM(
                        ROUND(
                            (JULIANDAY(last_check) - JULIANDAY(activation_date)) * 24
                        )
                    ) as total_hours
                FROM active_devices
                WHERE hardware_id = ?
            ''', (hardware_id,))
            total_usage_time = cursor.fetchone()[0] or 0
            
            return {
                'total_activations': total_activations,
                'total_days_used': total_days_used,
                'last_session_duration': last_session_duration,
                'total_usage_time': round(total_usage_time, 1)
            }
    
    def add_remote_command(self, hardware_id: str, command_type: str, command_data: dict = None) -> bool:
        """Add a remote command for a device"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO remote_commands
                    (hardware_id, command_type, command_data, issued_at)
                    VALUES (?, ?, ?, ?)
                ''', (
                    hardware_id,
                    command_type,
                    json.dumps(command_data) if command_data else None,
                    datetime.now().isoformat()
                ))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error adding remote command: {e}")
            return False
    
    def get_pending_commands(self, hardware_id: str) -> list:
        """Get pending commands for a device"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM remote_commands
                WHERE hardware_id = ? AND status = 'pending'
                ORDER BY issued_at ASC
            ''', (hardware_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def update_command_status(self, command_id: int, status: str) -> bool:
        """Update the status of a remote command"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE remote_commands
                    SET status = ?, executed_at = ?
                    WHERE id = ?
                ''', (status, datetime.now().isoformat(), command_id))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error updating command status: {e}")
            return False
    
    def add_chat_message(self, hardware_id: str, sender: str, message: str) -> bool:
        """Add a chat message to the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO chat_messages
                    (hardware_id, sender, message, timestamp)
                    VALUES (?, ?, ?, ?)
                ''', (
                    hardware_id,
                    sender,
                    message,
                    datetime.now().isoformat()
                ))
                conn.commit()
            return True
        except Exception as e:
            logging.error(f"Error adding chat message: {e}")
            return False
            
    def get_chat_history(self, hardware_id: str) -> list:
        """Get chat history for a device"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM chat_messages 
                WHERE hardware_id = ?
                ORDER BY timestamp ASC
            ''', (hardware_id,))
            return [dict(row) for row in cursor.fetchall()]
            
    def get_device_info(self, hardware_id: str) -> dict:
        """Get detailed device information"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM active_devices
                WHERE hardware_id = ?
            ''', (hardware_id,))
            result = cursor.fetchone()
            return dict(result) if result else None
    
    def add_support_ticket(self, ticket_data: dict) -> bool:
        """Add a new support ticket"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO support_tickets
                    (subject, category, priority, description, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    ticket_data['subject'],
                    ticket_data['category'],
                    ticket_data['priority'],
                    ticket_data['description'],
                    ticket_data['status'],
                    ticket_data['created_at']
                ))
                conn.commit()
            return True
        except Exception as e:
            logging.error(f"Error adding support ticket: {e}")
            return False
            
    def get_user_tickets(self) -> list:
        """Get all tickets for the current user"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM support_tickets
                ORDER BY created_at DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]
            
    def get_ticket_responses(self, ticket_id: int) -> list:
        """Get all responses for a ticket"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM ticket_responses
                WHERE ticket_id = ?
                ORDER BY timestamp ASC
            ''', (ticket_id,))
            return [dict(row) for row in cursor.fetchall()]
            
    def get_available_agents(self) -> list:
        """Get list of available support agents"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT a.*, COUNT(s.id) as active_chats
                FROM support_agents a
                LEFT JOIN agent_chat_sessions s ON 
                    a.id = s.agent_id AND 
                    s.status = 'active'
                WHERE a.status = 'available'
                GROUP BY a.id
                HAVING active_chats < a.max_concurrent_chats
                ORDER BY active_chats ASC
            ''')
            return [dict(row) for row in cursor.fetchall()]
            
    def add_support_message(self, message_data: dict) -> bool:
        """Add a support chat message"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO support_messages
                    (sender, message, timestamp)
                    VALUES (?, ?, ?)
                ''', (
                    message_data['sender'],
                    message_data['message'],
                    message_data['timestamp']
                ))
                conn.commit()
            return True
        except Exception as e:
            logging.error(f"Error adding support message: {e}")
            return False

    def start_chat_session(self, client_id: str) -> dict:
        """Start a new chat session with an available agent"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get available agent
                cursor.execute('''
                    SELECT a.*, COUNT(s.id) as active_chats
                    FROM support_agents a
                    LEFT JOIN agent_chat_sessions s ON 
                        a.id = s.agent_id AND 
                        s.status = 'active'
                    WHERE a.status = 'available'
                    GROUP BY a.id
                    HAVING active_chats < a.max_concurrent_chats
                    ORDER BY active_chats ASC
                    LIMIT 1
                ''')
                
                agent = cursor.fetchone()
                if not agent:
                    return {'status': 'queued'}
                
                # Create chat session
                cursor.execute('''
                    INSERT INTO agent_chat_sessions
                    (agent_id, client_id, started_at, status)
                    VALUES (?, ?, ?, 'active')
                ''', (
                    agent['id'],
                    client_id,
                    datetime.now().isoformat()
                ))
                
                session_id = cursor.lastrowid
                
                # Add system message
                cursor.execute('''
                    INSERT INTO chat_messages
                    (session_id, sender, message, timestamp)
                    VALUES (?, 'system', ?, ?)
                ''', (
                    session_id,
                    f"Connected with agent {agent['name']}",
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                
                return {
                    'status': 'connected',
                    'session_id': session_id,
                    'agent': {
                        'name': agent['name'],
                        'specialties': agent['specialties']
                    }
                }
                
        except Exception as e:
            logging.error(f"Error starting chat session: {e}")
            return {'status': 'error'}

    def add_chat_message(self, session_id: int, sender: str, message: str) -> bool:
        """Add a message to a chat session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO chat_messages
                    (session_id, sender, message, timestamp)
                    VALUES (?, ?, ?, ?)
                ''', (
                    session_id,
                    sender,
                    message,
                    datetime.now().isoformat()
                ))
                conn.commit()
            return True
        except Exception as e:
            logging.error(f"Error adding chat message: {e}")
            return False

    def get_chat_history(self, session_id: int) -> list:
        """Get chat history for a session"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM chat_messages
                WHERE session_id = ?
                ORDER BY timestamp ASC
            ''', (session_id,))
            return [dict(row) for row in cursor.fetchall()]

    def end_chat_session(self, session_id: int, rating: int = None, feedback: str = None) -> bool:
        """End a chat session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE agent_chat_sessions
                    SET status = 'ended',
                        ended_at = ?,
                        rating = ?,
                        feedback = ?
                    WHERE id = ?
                ''', (
                    datetime.now().isoformat(),
                    rating,
                    feedback,
                    session_id
                ))
                conn.commit()
            return True
        except Exception as e:
            logging.error(f"Error ending chat session: {e}")
            return False

    def get_recent_tickets(self) -> list:
        """Get recent support tickets"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT t.*, 
                       COUNT(r.id) as response_count,
                       MAX(r.timestamp) as last_response,
                       l.license_key,
                       l.hardware_id
                FROM support_tickets t
                LEFT JOIN ticket_responses r ON t.id = r.ticket_id
                LEFT JOIN generated_licenses l ON t.license_key = l.license_key
                GROUP BY t.id
                ORDER BY 
                    CASE t.status 
                        WHEN 'open' THEN 1
                        WHEN 'in_progress' THEN 2
                        ELSE 3
                    END,
                    t.created_at DESC
                LIMIT 50
            ''')
            tickets = [dict(row) for row in cursor.fetchall()]
            logging.info(f"Found {len(tickets)} tickets")
            return tickets

    def get_support_statistics(self) -> dict:
        """Get support system statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Totale ticket
            cursor.execute("SELECT COUNT(*) FROM support_tickets")
            total_tickets = cursor.fetchone()[0] or 0
            
            # Ticket attivi
            cursor.execute(
                "SELECT COUNT(*) FROM support_tickets WHERE status IN ('open', 'in_progress')"
            )
            active_tickets = cursor.fetchone()[0] or 0
            
            # Ticket risolti
            cursor.execute(
                "SELECT COUNT(*) FROM support_tickets WHERE status = 'closed'"
            )
            resolved_tickets = cursor.fetchone()[0] or 0
            
            # Tempo medio di risposta
            cursor.execute('''
                SELECT AVG(
                    CAST(
                        (julianday(MIN(r.timestamp)) - julianday(t.created_at)) * 24 * 60 
                        AS INTEGER
                    )
                )
                FROM support_tickets t
                JOIN ticket_responses r ON t.id = r.ticket_id
                WHERE t.status = 'closed'
                GROUP BY t.id
            ''')
            result = cursor.fetchone()
            avg_response_time = result[0] if result and result[0] else 0
            
            stats = {
                'total_tickets': total_tickets,
                'active_tickets': active_tickets,
                'resolved_tickets': resolved_tickets,
                'avg_response_time': round(avg_response_time, 1)
            }
            
            logging.info(f"Support statistics: {stats}")
            return stats

    def get_active_chats(self) -> list:
        """Get list of active chat sessions"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.*, 
                       a.name as agent_name,
                       COUNT(m.id) as message_count,
                       MAX(m.timestamp) as last_message
                FROM agent_chat_sessions c
                JOIN support_agents a ON c.agent_id = a.id
                LEFT JOIN chat_messages m ON c.id = m.session_id
                WHERE c.status = 'active'
                GROUP BY c.id
                ORDER BY c.started_at DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]

    def create_ticket(self, ticket_data: dict) -> int:
        """Create a new support ticket"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO support_tickets
                    (subject, category, priority, description, status, created_at)
                    VALUES (?, ?, ?, ?, 'open', ?)
                ''', (
                    ticket_data['subject'],
                    ticket_data['category'],
                    ticket_data['priority'],
                    ticket_data['description'],
                    datetime.now().isoformat()
                ))
                return cursor.lastrowid
        except Exception as e:
            logging.error(f"Error creating ticket: {e}")
            return None

    def get_ticket_responses(self, ticket_id: int) -> list:
        """Get all responses for a ticket"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM ticket_responses
                WHERE ticket_id = ?
                ORDER BY timestamp ASC
            ''', (ticket_id,))
            return [dict(row) for row in cursor.fetchall()]

    def add_ticket_response(self, ticket_id: int, sender: str, message: str) -> bool:
        """Add a response to a ticket"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO ticket_responses
                    (ticket_id, sender, message, timestamp)
                    VALUES (?, ?, ?, ?)
                ''', (
                    ticket_id,
                    sender,
                    message,
                    datetime.now().isoformat()
                ))
                
                # Aggiorna lo stato del ticket
                cursor.execute('''
                    UPDATE support_tickets
                    SET status = 'in_progress'
                    WHERE id = ? AND status = 'open'
                ''', (ticket_id,))
                
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error adding ticket response: {e}")
            return False