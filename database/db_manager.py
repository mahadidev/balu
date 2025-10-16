import sqlite3
import os
from datetime import datetime
import pytz

class DatabaseManager:
    def __init__(self, db_path="bot_database.db"):
        self.db_path = db_path
        self.timezone = pytz.timezone('Asia/Dhaka')
        self.init_database()
    
    def init_database(self):
        """Initialize the database and create tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create global_chat_channels table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS global_chat_channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id TEXT NOT NULL,
                    channel_id TEXT NOT NULL,
                    guild_name TEXT,
                    channel_name TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    registered_by TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(guild_id, channel_id)
                )
            ''')
            
            # Create global_chat_messages table for logging
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS global_chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT NOT NULL,
                    guild_id TEXT NOT NULL,
                    channel_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    guild_name TEXT,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create global_chat_settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS global_chat_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_name TEXT NOT NULL UNIQUE,
                    setting_value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert default settings
            default_settings = [
                ('rate_limit_seconds', '3'),
                ('max_message_length', '2000'),
                ('enable_filtering', 'true'),
                ('webhook_name', 'Global Chat')
            ]
            
            for setting_name, setting_value in default_settings:
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO global_chat_settings (setting_name, setting_value)
                        VALUES (?, ?)
                    ''', (setting_name, setting_value))
                except sqlite3.IntegrityError:
                    pass
            
            conn.commit()
    
    def register_global_chat_channel(self, guild_id, channel_id, guild_name=None, channel_name=None, registered_by=None):
        """Register a channel for global chat"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            dhaka_time = datetime.now(self.timezone).strftime('%Y-%m-%d %H:%M:%S')
            
            try:
                cursor.execute('''
                    INSERT INTO global_chat_channels (guild_id, channel_id, guild_name, channel_name, registered_by, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (guild_id, channel_id, guild_name, channel_name, registered_by, dhaka_time))
                return True
            except sqlite3.IntegrityError:
                cursor.execute('''
                    UPDATE global_chat_channels 
                    SET guild_name = ?, channel_name = ?, is_active = TRUE, created_at = ?
                    WHERE guild_id = ? AND channel_id = ?
                ''', (guild_name, channel_name, dhaka_time, guild_id, channel_id))
                return "updated"
    
    def unregister_global_chat_channel(self, guild_id, channel_id):
        """Unregister a channel from global chat"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM global_chat_channels 
                WHERE guild_id = ? AND channel_id = ?
            ''', (guild_id, channel_id))
            return cursor.rowcount > 0
    
    def get_global_chat_channels(self):
        """Get all registered global chat channels"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT guild_id, channel_id, guild_name, channel_name 
                FROM global_chat_channels 
                WHERE is_active = TRUE
                ORDER BY guild_name
            ''')
            
            results = cursor.fetchall()
            channels = []
            
            for result in results:
                channels.append({
                    'guild_id': result[0],
                    'channel_id': result[1],
                    'guild_name': result[2],
                    'channel_name': result[3]
                })
            
            return channels
    
    def is_global_chat_channel(self, guild_id, channel_id):
        """Check if a channel is registered for global chat"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id FROM global_chat_channels 
                WHERE guild_id = ? AND channel_id = ? AND is_active = TRUE
            ''', (guild_id, channel_id))
            return cursor.fetchone() is not None
    
    def log_global_chat_message(self, message_id, guild_id, channel_id, user_id, username, guild_name, content):
        """Log a global chat message"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            dhaka_time = datetime.now(self.timezone).strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                INSERT INTO global_chat_messages 
                (message_id, guild_id, channel_id, user_id, username, guild_name, content, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (message_id, guild_id, channel_id, user_id, username, guild_name, content, dhaka_time))
    
    def get_global_chat_setting(self, setting_name):
        """Get a global chat setting value"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT setting_value FROM global_chat_settings 
                WHERE setting_name = ?
            ''', (setting_name,))
            
            result = cursor.fetchone()
            return result[0] if result else None
    
    def update_global_chat_setting(self, setting_name, setting_value):
        """Update a global chat setting"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            dhaka_time = datetime.now(self.timezone).strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                INSERT OR REPLACE INTO global_chat_settings 
                (setting_name, setting_value, updated_at)
                VALUES (?, ?, ?)
            ''', (setting_name, setting_value, dhaka_time))