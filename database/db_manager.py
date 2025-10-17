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
            
            # Create chat_categories table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_name TEXT NOT NULL UNIQUE,
                    created_by TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    max_servers INTEGER DEFAULT 50
                )
            ''')
            
            # Create category_subscriptions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS category_subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_name TEXT NOT NULL,
                    guild_id TEXT NOT NULL,
                    channel_id TEXT NOT NULL,
                    guild_name TEXT,
                    channel_name TEXT,
                    subscribed_by TEXT NOT NULL,
                    subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    UNIQUE(category_name, guild_id, channel_id),
                    FOREIGN KEY (category_name) REFERENCES chat_categories (category_name)
                )
            ''')
            
            # Create category_messages table for logging
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS category_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT NOT NULL,
                    category_name TEXT NOT NULL,
                    guild_id TEXT NOT NULL,
                    channel_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    guild_name TEXT,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    
    # Category Management Methods
    def create_chat_category(self, category_name, created_by, max_servers=50):
        """Create a new chat category"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # First check if a category with the same name already exists (case-insensitive)
            cursor.execute('''
                SELECT category_name FROM chat_categories 
                WHERE LOWER(category_name) = LOWER(?) AND is_active = TRUE
            ''', (category_name,))
            
            existing = cursor.fetchone()
            if existing:
                return False  # Category already exists
            
            dhaka_time = datetime.now(self.timezone).strftime('%Y-%m-%d %H:%M:%S')
            
            try:
                cursor.execute('''
                    INSERT INTO chat_categories (category_name, created_by, created_at, max_servers)
                    VALUES (?, ?, ?, ?)
                ''', (category_name, created_by, dhaka_time, max_servers))
                return True
            except sqlite3.IntegrityError:
                return False
    
    def get_chat_categories(self, active_only=True):
        """Get all chat categories"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = '''
                SELECT category_name, created_by, created_at, max_servers,
                       (SELECT COUNT(*) FROM category_subscriptions 
                        WHERE category_name = chat_categories.category_name AND is_active = TRUE) as subscriber_count
                FROM chat_categories 
            '''
            
            if active_only:
                query += ' WHERE is_active = TRUE'
            
            query += ' ORDER BY category_name'
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            categories = []
            for result in results:
                categories.append({
                    'category_name': result[0],
                    'created_by': result[1],
                    'created_at': result[2],
                    'max_servers': result[3],
                    'subscriber_count': result[4]
                })
            
            return categories
    
    def delete_chat_category(self, category_name, deleted_by):
        """Delete a chat category and all its subscriptions"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if category exists and if user is the creator
            cursor.execute('''
                SELECT created_by FROM chat_categories 
                WHERE LOWER(category_name) = LOWER(?) AND is_active = TRUE
            ''', (category_name,))
            
            result = cursor.fetchone()
            if not result:
                return "not_found"
            
            if result[0] != deleted_by:
                return "no_permission"
            
            # Deactivate category
            cursor.execute('''
                UPDATE chat_categories 
                SET is_active = FALSE 
                WHERE LOWER(category_name) = LOWER(?)
            ''', (category_name,))
            
            # Deactivate all subscriptions
            cursor.execute('''
                UPDATE category_subscriptions 
                SET is_active = FALSE 
                WHERE LOWER(category_name) = LOWER(?)
            ''', (category_name,))
            
            return "success"
    
    def subscribe_to_category(self, category_name, guild_id, channel_id, guild_name, channel_name, subscribed_by):
        """Subscribe a channel to a chat category"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if category exists and is active
            cursor.execute('''
                SELECT max_servers, category_name FROM chat_categories 
                WHERE LOWER(category_name) = LOWER(?) AND is_active = TRUE
            ''', (category_name,))
            
            category_result = cursor.fetchone()
            if not category_result:
                return "category_not_found"
            
            max_servers = category_result[0]
            actual_category_name = category_result[1]  # Get the actual category name with proper case
            
            # Check current subscriber count
            cursor.execute('''
                SELECT COUNT(*) FROM category_subscriptions 
                WHERE LOWER(category_name) = LOWER(?) AND is_active = TRUE
            ''', (category_name,))
            
            current_count = cursor.fetchone()[0]
            if current_count >= max_servers:
                return "category_full"
            
            dhaka_time = datetime.now(self.timezone).strftime('%Y-%m-%d %H:%M:%S')
            
            try:
                cursor.execute('''
                    INSERT INTO category_subscriptions 
                    (category_name, guild_id, channel_id, guild_name, channel_name, subscribed_by, subscribed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (actual_category_name, guild_id, channel_id, guild_name, channel_name, subscribed_by, dhaka_time))
                return "success"
            except sqlite3.IntegrityError:
                # Update existing subscription
                cursor.execute('''
                    UPDATE category_subscriptions 
                    SET guild_name = ?, channel_name = ?, is_active = TRUE, subscribed_at = ?, category_name = ?
                    WHERE LOWER(category_name) = LOWER(?) AND guild_id = ? AND channel_id = ?
                ''', (guild_name, channel_name, dhaka_time, actual_category_name, category_name, guild_id, channel_id))
                return "updated"
    
    def unsubscribe_from_category(self, category_name, guild_id, channel_id):
        """Unsubscribe a channel from a chat category"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE category_subscriptions 
                SET is_active = FALSE 
                WHERE LOWER(category_name) = LOWER(?) AND guild_id = ? AND channel_id = ?
            ''', (category_name, guild_id, channel_id))
            return cursor.rowcount > 0
    
    def get_category_subscribers(self, category_name):
        """Get all subscribers of a category"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT guild_id, channel_id, guild_name, channel_name 
                FROM category_subscriptions 
                WHERE LOWER(category_name) = LOWER(?) AND is_active = TRUE
                ORDER BY guild_name
            ''', (category_name,))
            
            results = cursor.fetchall()
            subscribers = []
            
            for result in results:
                subscribers.append({
                    'guild_id': result[0],
                    'channel_id': result[1],
                    'guild_name': result[2],
                    'channel_name': result[3]
                })
            
            return subscribers
    
    def get_channel_subscriptions(self, guild_id, channel_id):
        """Get all categories a channel is subscribed to"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT cs.category_name
                FROM category_subscriptions cs
                JOIN chat_categories cc ON cs.category_name = cc.category_name
                WHERE cs.guild_id = ? AND cs.channel_id = ? AND cs.is_active = TRUE AND cc.is_active = TRUE
                ORDER BY cs.category_name
            ''', (guild_id, channel_id))
            
            results = cursor.fetchall()
            subscriptions = []
            
            for result in results:
                subscriptions.append({
                    'category_name': result[0]
                })
            
            return subscriptions
    
    def log_category_message(self, message_id, category_name, guild_id, channel_id, user_id, username, guild_name, content):
        """Log a category chat message"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            dhaka_time = datetime.now(self.timezone).strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                INSERT INTO category_messages 
                (message_id, category_name, guild_id, channel_id, user_id, username, guild_name, content, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (message_id, category_name, guild_id, channel_id, user_id, username, guild_name, content, dhaka_time))