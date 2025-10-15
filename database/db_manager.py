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
            
            # Create team_register table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS team_register (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_user_id TEXT NOT NULL,
                    guild_id TEXT NOT NULL,
                    guild_name TEXT,
                    server_link TEXT,
                    team_name TEXT,
                    created_by TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Add created_by column to existing tables (if it doesn't exist)
            try:
                cursor.execute('ALTER TABLE team_register ADD COLUMN created_by TEXT')
            except sqlite3.OperationalError:
                # Column already exists
                pass
            
            # Add category_id column to existing tables (if it doesn't exist)
            try:
                cursor.execute('ALTER TABLE team_register ADD COLUMN category_id INTEGER')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON team_register(category_id)')
            except sqlite3.OperationalError:
                # Column already exists
                pass
            
            # Create index for faster lookups
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_user_guild 
                ON team_register(discord_user_id, guild_id)
            ''')
            
            # Create notification_subscriptions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notification_subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id TEXT NOT NULL,
                    channel_id TEXT NOT NULL,
                    category_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(guild_id, channel_id, category_id)
                )
            ''')
            
            # Check if the current table has the wrong UNIQUE constraint and fix it
            try:
                # Try to get the table schema
                cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='notification_subscriptions'")
                schema = cursor.fetchone()
                if schema and 'UNIQUE(guild_id, channel_id, category_id)' not in schema[0]:
                    # The table has the wrong constraint, we need to recreate it
                    print("Updating notification_subscriptions table schema...")
                    
                    # Backup existing data
                    cursor.execute('SELECT * FROM notification_subscriptions')
                    existing_data = cursor.fetchall()
                    
                    # Drop the old table
                    cursor.execute('DROP TABLE notification_subscriptions')
                    
                    # Recreate with correct schema
                    cursor.execute('''
                        CREATE TABLE notification_subscriptions (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            guild_id TEXT NOT NULL,
                            channel_id TEXT NOT NULL,
                            category_id INTEGER,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(guild_id, channel_id, category_id)
                        )
                    ''')
                    
                    # Restore data (skip duplicates that would violate the new constraint)
                    for row in existing_data:
                        try:
                            cursor.execute('''
                                INSERT INTO notification_subscriptions (id, guild_id, channel_id, category_id, created_at)
                                VALUES (?, ?, ?, ?, ?)
                            ''', row)
                        except sqlite3.IntegrityError:
                            # Skip duplicate entries
                            pass
                    
                    print("Schema update completed!")
            except Exception as e:
                print(f"Schema update failed (continuing with existing schema): {e}")
            
            # Add category_id column to existing subscriptions table (if it doesn't exist)
            try:
                cursor.execute('ALTER TABLE notification_subscriptions ADD COLUMN category_id INTEGER')
            except sqlite3.OperationalError:
                # Column already exists
                pass
            
            # Create challenges_categories table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS challenges_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert fixed categories if they don't exist
            categories = [
                ('Clash Squad Limited', 'Limited clash squad matches with restricted loadouts'),
                ('Clash Squad Unlimited', 'Unlimited clash squad matches with full access to weapons'),
                ('Clash Squad Quantra', 'Quantra-based clash squad battles'),
                ('Full Map', 'Full battle royale map games'),
                ('Custom', 'Custom game modes and challenges')
            ]
            
            for category_name, description in categories:
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO challenges_categories (name, description)
                        VALUES (?, ?)
                    ''', (category_name, description))
                except sqlite3.IntegrityError:
                    # Category already exists
                    pass
            
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
    
    def register_team(self, discord_user_id, guild_id, guild_name=None, server_link=None, team_name=None, created_by=None, category_id=None):
        """Register or update a team entry - allows multiple entries per user with different team names"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get current time in Dhaka timezone
            dhaka_time = datetime.now(self.timezone).strftime('%Y-%m-%d %H:%M:%S')
            
            # Check if entry already exists with same user, guild, and team name
            cursor.execute('''
                SELECT id FROM team_register 
                WHERE discord_user_id = ? AND guild_id = ? AND LOWER(team_name) = LOWER(?)
            ''', (discord_user_id, guild_id, team_name))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing entry with same team name
                cursor.execute('''
                    UPDATE team_register 
                    SET guild_name = ?, server_link = ?, updated_at = ?,
                        created_by = COALESCE(created_by, ?), category_id = ?
                    WHERE discord_user_id = ? AND guild_id = ? AND LOWER(team_name) = LOWER(?)
                ''', (guild_name, server_link, dhaka_time, created_by or discord_user_id, category_id, discord_user_id, guild_id, team_name))
                return "updated"
            else:
                # Insert new entry (different team name or new user)
                cursor.execute('''
                    INSERT INTO team_register (discord_user_id, guild_id, guild_name, server_link, team_name, created_by, category_id, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (discord_user_id, guild_id, guild_name, server_link, team_name, created_by or discord_user_id, category_id, dhaka_time, dhaka_time))
                return "created"
    
    def get_team_registration(self, discord_user_id, guild_id):
        """Get team registration for a specific user in a guild"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT guild_name, server_link, team_name, created_by, created_at, updated_at
                FROM team_register 
                WHERE discord_user_id = ? AND guild_id = ?
            ''', (discord_user_id, guild_id))
            
            result = cursor.fetchone()
            if result:
                return {
                    'guild_name': result[0],
                    'server_link': result[1],
                    'team_name': result[2],
                    'created_by': result[3],
                    'created_at': result[4],
                    'updated_at': result[5]
                }
            return None
    
    def get_all_team_registrations(self, guild_id=None):
        """Get all team registrations, optionally filtered by guild"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if guild_id:
                cursor.execute('''
                    SELECT discord_user_id, guild_name, server_link, team_name, created_at
                    FROM team_register 
                    WHERE guild_id = ?
                    ORDER BY created_at DESC
                ''', (guild_id,))
            else:
                cursor.execute('''
                    SELECT discord_user_id, guild_id, guild_name, server_link, team_name, created_at
                    FROM team_register 
                    ORDER BY created_at DESC
                ''')
            
            results = cursor.fetchall()
            teams = []
            
            for result in results:
                if guild_id:
                    teams.append({
                        'discord_user_id': result[0],
                        'guild_name': result[1],
                        'server_link': result[2],
                        'team_name': result[3],
                        'created_at': result[4]
                    })
                else:
                    teams.append({
                        'discord_user_id': result[0],
                        'guild_id': result[1],
                        'guild_name': result[2],
                        'server_link': result[3],
                        'team_name': result[4],
                        'created_at': result[5]
                    })
            
            return teams
    
    def delete_team_registration(self, discord_user_id, guild_id):
        """Delete a team registration"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM team_register 
                WHERE discord_user_id = ? AND guild_id = ?
            ''', (discord_user_id, guild_id))
            
            return cursor.rowcount > 0
    
    def check_team_name_exists(self, guild_id, team_name, exclude_user_id=None):
        """Check if a team name already exists in a guild (excluding a specific user)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if exclude_user_id:
                cursor.execute('''
                    SELECT discord_user_id, team_name FROM team_register 
                    WHERE guild_id = ? AND LOWER(team_name) = LOWER(?) AND discord_user_id != ?
                ''', (guild_id, team_name, exclude_user_id))
            else:
                cursor.execute('''
                    SELECT discord_user_id, team_name FROM team_register 
                    WHERE guild_id = ? AND LOWER(team_name) = LOWER(?)
                ''', (guild_id, team_name))
            
            return cursor.fetchone()
    
    def get_recent_teams(self, guild_id, limit=5):
        """Get the most recently updated teams in a guild"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT discord_user_id, team_name, server_link, guild_name, created_by, updated_at
                FROM team_register 
                WHERE guild_id = ? AND team_name IS NOT NULL
                ORDER BY updated_at DESC
                LIMIT ?
            ''', (guild_id, limit))
            
            results = cursor.fetchall()
            teams = []
            
            for result in results:
                teams.append({
                    'discord_user_id': result[0],
                    'team_name': result[1],
                    'server_link': result[2],
                    'guild_name': result[3],
                    'created_by': result[4],
                    'updated_at': result[5]
                })
            
            return teams
    
    def get_global_recent_teams(self, limit=10):
        """Get the most recently updated teams across all guilds"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT discord_user_id, team_name, server_link, guild_name, guild_id, created_by, updated_at
                FROM team_register 
                WHERE team_name IS NOT NULL
                ORDER BY updated_at DESC
                LIMIT ?
            ''', (limit,))
            
            results = cursor.fetchall()
            teams = []
            
            for result in results:
                teams.append({
                    'discord_user_id': result[0],
                    'team_name': result[1],
                    'server_link': result[2],
                    'guild_name': result[3],
                    'guild_id': result[4],
                    'created_by': result[5],
                    'updated_at': result[6]
                })
            
            return teams
    
    def subscribe_to_notifications(self, guild_id, channel_id, category_id=None):
        """Subscribe a channel to team registration notifications for a specific category or all categories"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get current time in Dhaka timezone
            dhaka_time = datetime.now(self.timezone).strftime('%Y-%m-%d %H:%M:%S')
            
            # If subscribing to all categories (category_id=None), remove all specific category subscriptions
            if category_id is None:
                # Check if already subscribed to all categories
                cursor.execute('''
                    SELECT id FROM notification_subscriptions 
                    WHERE guild_id = ? AND channel_id = ? AND category_id IS NULL
                ''', (guild_id, channel_id))
                if cursor.fetchone():
                    # Already subscribed to all categories, just refresh
                    cursor.execute('''
                        UPDATE notification_subscriptions 
                        SET created_at = ?
                        WHERE guild_id = ? AND channel_id = ? AND category_id IS NULL
                    ''', (dhaka_time, guild_id, channel_id))
                    return "refreshed"
                
                # Remove all specific category subscriptions
                cursor.execute('''
                    DELETE FROM notification_subscriptions 
                    WHERE guild_id = ? AND channel_id = ? AND category_id IS NOT NULL
                ''', (guild_id, channel_id))
            # If subscribing to a specific category, check if already subscribed to all categories
            else:
                cursor.execute('''
                    SELECT id FROM notification_subscriptions 
                    WHERE guild_id = ? AND channel_id = ? AND category_id IS NULL
                ''', (guild_id, channel_id))
                if cursor.fetchone():
                    # Already subscribed to all categories, no need to add specific category
                    return False
                
                # Check if already subscribed to this specific category
                cursor.execute('''
                    SELECT id FROM notification_subscriptions 
                    WHERE guild_id = ? AND channel_id = ? AND category_id = ?
                ''', (guild_id, channel_id, category_id))
                existing = cursor.fetchone()
                if existing:
                    # Update the existing subscription (refresh timestamp)
                    cursor.execute('''
                        UPDATE notification_subscriptions 
                        SET created_at = ?
                        WHERE guild_id = ? AND channel_id = ? AND category_id = ?
                    ''', (dhaka_time, guild_id, channel_id, category_id))
                    return "refreshed"
            
            # Insert new subscription
            try:
                cursor.execute('''
                    INSERT INTO notification_subscriptions (guild_id, channel_id, category_id, created_at)
                    VALUES (?, ?, ?, ?)
                ''', (guild_id, channel_id, category_id, dhaka_time))
                return True
            except sqlite3.IntegrityError:
                # This can happen if the database constraint is different than expected
                # Try to update instead
                cursor.execute('''
                    UPDATE notification_subscriptions 
                    SET category_id = ?, created_at = ?
                    WHERE guild_id = ? AND channel_id = ?
                ''', (category_id, dhaka_time, guild_id, channel_id))
                return "refreshed"
    
    def unsubscribe_from_notifications(self, guild_id, channel_id, category_id=None):
        """Unsubscribe a channel from team registration notifications for a specific category or all categories"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if category_id is not None:
                # Unsubscribe from specific category
                cursor.execute('''
                    DELETE FROM notification_subscriptions 
                    WHERE guild_id = ? AND channel_id = ? AND category_id = ?
                ''', (guild_id, channel_id, category_id))
            else:
                # Unsubscribe from all categories
                cursor.execute('''
                    DELETE FROM notification_subscriptions 
                    WHERE guild_id = ? AND channel_id = ?
                ''', (guild_id, channel_id))
            return cursor.rowcount > 0
    
    def get_notification_subscribers(self, category_id=None):
        """Get all channels subscribed to notifications for a specific category or all categories"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if category_id is not None:
                # Get subscribers for specific category + those subscribed to all categories (NULL)
                cursor.execute('''
                    SELECT guild_id, channel_id, category_id FROM notification_subscriptions
                    WHERE category_id = ? OR category_id IS NULL
                ''', (category_id,))
            else:
                # Get all subscribers
                cursor.execute('''
                    SELECT guild_id, channel_id, category_id FROM notification_subscriptions
                ''')
            
            results = cursor.fetchall()
            return results
    
    def is_subscribed(self, guild_id, channel_id, category_id=None):
        """Check if a channel is subscribed to notifications for a specific category or any category"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if category_id is not None:
                # Check if subscribed to specific category or all categories
                cursor.execute('''
                    SELECT id FROM notification_subscriptions 
                    WHERE guild_id = ? AND channel_id = ? AND (category_id = ? OR category_id IS NULL)
                ''', (guild_id, channel_id, category_id))
            else:
                # Check if subscribed to any category
                cursor.execute('''
                    SELECT id FROM notification_subscriptions 
                    WHERE guild_id = ? AND channel_id = ?
                ''', (guild_id, channel_id))
            return cursor.fetchone() is not None
    
    def get_channel_subscriptions(self, guild_id, channel_id):
        """Get all subscription categories for a specific channel"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT category_id FROM notification_subscriptions 
                WHERE guild_id = ? AND channel_id = ?
                ORDER BY category_id
            ''', (guild_id, channel_id))
            results = cursor.fetchall()
            return [row[0] for row in results]
    
    def get_challenge_categories(self, active_only=True):
        """Get all challenge categories"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if active_only:
                cursor.execute('''
                    SELECT id, name, description FROM challenges_categories 
                    WHERE is_active = TRUE 
                    ORDER BY id
                ''')
            else:
                cursor.execute('''
                    SELECT id, name, description FROM challenges_categories 
                    ORDER BY id
                ''')
            
            results = cursor.fetchall()
            categories = []
            
            for result in results:
                categories.append({
                    'id': result[0],
                    'name': result[1],
                    'description': result[2]
                })
            
            return categories
    
    def get_category_by_id(self, category_id):
        """Get a specific category by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, description FROM challenges_categories 
                WHERE id = ? AND is_active = TRUE
            ''', (category_id,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'id': result[0],
                    'name': result[1],
                    'description': result[2]
                }
            return None
    
    def get_category_by_name(self, category_name):
        """Get a specific category by name"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, description FROM challenges_categories 
                WHERE LOWER(name) = LOWER(?) AND is_active = TRUE
            ''', (category_name,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'id': result[0],
                    'name': result[1],
                    'description': result[2]
                }
            return None
    
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
    
    def get_global_chat_channels(self, active_only=True):
        """Get all registered global chat channels"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if active_only:
                cursor.execute('''
                    SELECT guild_id, channel_id, guild_name, channel_name FROM global_chat_channels
                    WHERE is_active = TRUE
                    ORDER BY created_at
                ''')
            else:
                cursor.execute('''
                    SELECT guild_id, channel_id, guild_name, channel_name, is_active FROM global_chat_channels
                    ORDER BY created_at
                ''')
            
            results = cursor.fetchall()
            channels = []
            
            for result in results:
                if active_only:
                    channels.append({
                        'guild_id': result[0],
                        'channel_id': result[1],
                        'guild_name': result[2],
                        'channel_name': result[3]
                    })
                else:
                    channels.append({
                        'guild_id': result[0],
                        'channel_id': result[1],
                        'guild_name': result[2],
                        'channel_name': result[3],
                        'is_active': result[4]
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
    
    def close(self):
        """Close database connection (SQLite handles this automatically)"""
        pass