from datetime import datetime
import sqlite3
import json
import logging
from typing import Dict, List, Optional

class TicketManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._initialize_database()
        
    def _initialize_database(self):
        """Initialize ticket database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hardware_id TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    category TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    closed_at TEXT,
                    assigned_to TEXT,
                    resolution TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ticket_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id INTEGER NOT NULL,
                    sender TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    attachments TEXT,
                    FOREIGN KEY (ticket_id) REFERENCES tickets(id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ticket_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT,
                    timestamp TEXT NOT NULL,
                    performed_by TEXT NOT NULL,
                    FOREIGN KEY (ticket_id) REFERENCES tickets(id)
                )
            ''')
            
    def create_ticket(self, ticket_data: Dict) -> Optional[int]:
        """Create a new support ticket"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                now = datetime.now().isoformat()
                cursor.execute('''
                    INSERT INTO tickets (
                        hardware_id, subject, description, status,
                        priority, category, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    ticket_data['hardware_id'],
                    ticket_data['subject'],
                    ticket_data['description'],
                    'open',
                    ticket_data['priority'],
                    ticket_data['category'],
                    now,
                    now
                ))
                
                ticket_id = cursor.lastrowid
                
                # Add initial history entry
                cursor.execute('''
                    INSERT INTO ticket_history (
                        ticket_id, action, details, timestamp, performed_by
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    ticket_id,
                    'created',
                    'Ticket created',
                    now,
                    ticket_data['hardware_id']
                ))
                
                return ticket_id
                
        except Exception as e:
            logging.error(f"Error creating ticket: {e}")
            return None
            
    def add_message(self, ticket_id: int, message_data: Dict) -> bool:
        """Add a message to a ticket"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO ticket_messages (
                        ticket_id, sender, message, timestamp, attachments
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    ticket_id,
                    message_data['sender'],
                    message_data['message'],
                    datetime.now().isoformat(),
                    json.dumps(message_data.get('attachments', []))
                ))
                
                # Update ticket last update time
                cursor.execute('''
                    UPDATE tickets 
                    SET updated_at = ? 
                    WHERE id = ?
                ''', (datetime.now().isoformat(), ticket_id))
                
                return True
                
        except Exception as e:
            logging.error(f"Error adding message: {e}")
            return False
            
    def get_ticket_history(self, ticket_id: int) -> List[Dict]:
        """Get complete ticket history including messages"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get ticket details
            cursor.execute('SELECT * FROM tickets WHERE id = ?', (ticket_id,))
            ticket = dict(cursor.fetchone())
            
            # Get messages
            cursor.execute(
                'SELECT * FROM ticket_messages WHERE ticket_id = ? ORDER BY timestamp ASC',
                (ticket_id,)
            )
            messages = [dict(row) for row in cursor.fetchall()]
            
            # Get history
            cursor.execute(
                'SELECT * FROM ticket_history WHERE ticket_id = ? ORDER BY timestamp ASC',
                (ticket_id,)
            )
            history = [dict(row) for row in cursor.fetchall()]
            
            return {
                'ticket': ticket,
                'messages': messages,
                'history': history
            } 