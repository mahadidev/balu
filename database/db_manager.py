import sqlite3
import os
from datetime import datetime
import pytz
import difflib

class DatabaseManager:
    def __init__(self, db_path="bot_database.db"):
        self.db_path = db_path
        self.timezone = pytz.timezone('Asia/Dhaka')
        self.init_database()
    
    def init_database(self):
        """Initialize the database and create tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create global_chat_rooms table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS global_chat_rooms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    room_name TEXT NOT NULL UNIQUE,
                    created_by TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    max_servers INTEGER DEFAULT 50
                )
            ''')
            
            # Create global_chat_channels table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS global_chat_channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id TEXT NOT NULL,
                    channel_id TEXT NOT NULL,
                    guild_name TEXT,
                    channel_name TEXT,
                    room_name TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    registered_by TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(guild_id, channel_id),
                    FOREIGN KEY (room_name) REFERENCES global_chat_rooms (room_name)
                )
            ''')
            
            # Create global_chat_messages table for logging
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS global_chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT NOT NULL,
                    room_name TEXT NOT NULL,
                    guild_id TEXT NOT NULL,
                    channel_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    guild_name TEXT,
                    content TEXT NOT NULL,
                    reply_to_message_id TEXT,
                    reply_to_username TEXT,
                    reply_to_content TEXT,
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
            
            # Create room_permissions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS room_permissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    room_name TEXT NOT NULL,
                    allow_urls BOOLEAN DEFAULT FALSE,
                    allow_files BOOLEAN DEFAULT FALSE,
                    enable_bad_word_filter BOOLEAN DEFAULT TRUE,
                    max_message_length INTEGER DEFAULT 2000,
                    rate_limit_seconds INTEGER DEFAULT 3,
                    allow_mentions BOOLEAN DEFAULT TRUE,
                    allow_emojis BOOLEAN DEFAULT TRUE,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_by TEXT,
                    UNIQUE(room_name),
                    FOREIGN KEY (room_name) REFERENCES global_chat_rooms (room_name)
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
            
            # Run migration for reply feature columns if needed
            self._migrate_reply_feature_columns(cursor, conn)
    
    def _migrate_reply_feature_columns(self, cursor, conn):
        """Add reply feature columns to existing global_chat_messages table if they don't exist"""
        try:
            # Check if reply columns exist
            cursor.execute("PRAGMA table_info(global_chat_messages)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Add missing columns
            columns_to_add = [
                ('reply_to_message_id', 'TEXT'),
                ('reply_to_username', 'TEXT'),
                ('reply_to_content', 'TEXT')
            ]
            
            for column_name, column_type in columns_to_add:
                if column_name not in columns:
                    print(f"🔄 Adding reply feature column: {column_name}")
                    cursor.execute(f'''
                        ALTER TABLE global_chat_messages 
                        ADD COLUMN {column_name} {column_type}
                    ''')
            
            conn.commit()
        except sqlite3.Error as e:
            print(f"⚠️ Reply feature migration error (non-critical): {e}")
    
    def create_chat_room(self, room_name, created_by, max_servers=50):
        """Create a new chat room and return room ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Normalize room name: strip extra spaces but preserve intentional spaces
            normalized_name = ' '.join(room_name.strip().split())
            
            # Check if normalized room name already exists
            cursor.execute('''
                SELECT room_name FROM global_chat_rooms 
                WHERE LOWER(TRIM(room_name)) = LOWER(?)
            ''', (normalized_name,))
            
            if cursor.fetchone():
                return False  # Room already exists
            
            dhaka_time = datetime.now(self.timezone).strftime('%Y-%m-%d %H:%M:%S')
            
            try:
                cursor.execute('''
                    INSERT INTO global_chat_rooms (room_name, created_by, created_at, max_servers)
                    VALUES (?, ?, ?, ?)
                ''', (normalized_name, created_by, dhaka_time, max_servers))
                
                # Get the room ID that was just created
                room_id = cursor.lastrowid
                
                # Create default permissions for the new room using room_id
                cursor.execute('''
                    INSERT INTO room_permissions (room_name, updated_by, updated_at)
                    VALUES (?, ?, ?)
                ''', (normalized_name, created_by, dhaka_time))
                
                return room_id
            except sqlite3.IntegrityError:
                return False
    
    def get_chat_rooms(self):
        """Get all active chat rooms"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT room_name, created_by, created_at, max_servers,
                       (SELECT COUNT(*) FROM global_chat_channels 
                        WHERE room_name = global_chat_rooms.room_name AND is_active = TRUE) as subscriber_count
                FROM global_chat_rooms 
                WHERE is_active = TRUE
                ORDER BY room_name
            ''')
            
            results = cursor.fetchall()
            rooms = []
            
            for result in results:
                rooms.append({
                    'room_name': result[0],
                    'created_by': result[1],
                    'created_at': result[2],
                    'max_servers': result[3],
                    'subscriber_count': result[4]
                })
            
            return rooms
    
    def find_closest_room(self, input_room_name):
        """Find the closest matching room name using enhanced fuzzy matching"""
        rooms = self.get_chat_rooms()
        if not rooms:
            return None
        
        room_names = [room['room_name'] for room in rooms]
        # Normalize input: strip extra spaces and convert to lowercase
        input_lower = ' '.join(input_room_name.lower().strip().split())
        
        # First try exact match (case insensitive, normalized spaces)
        for room_name in room_names:
            room_normalized = ' '.join(room_name.lower().strip().split())
            if room_normalized == input_lower:
                return room_name
        
        # Try partial word matching (e.g., "pubg comm" matches "pubg community")
        best_match = None
        best_score = 0
        
        for room_name in room_names:
            # Normalize room name: handle spaces, dashes, underscores
            room_normalized = ' '.join(room_name.lower().strip().split())
            
            # Check if input words are contained in room name
            input_words = input_lower.split()
            room_words = room_normalized.replace('-', ' ').replace('_', ' ').split()
            
            # Calculate word-based similarity
            word_matches = 0
            total_input_chars = len(input_lower.replace(' ', ''))
            matched_chars = 0
            
            for input_word in input_words:
                best_match_score = 0
                for room_word in room_words:
                    # Check for exact word match
                    if input_word == room_word:
                        best_match_score = 1.0
                        break  # Perfect match, no need to check others
                    # Check if input word is start of room word (abbreviation)
                    elif room_word.startswith(input_word) and len(input_word) >= 2:
                        best_match_score = max(best_match_score, 0.8)
                    # Check if room word contains input word
                    elif input_word in room_word and len(input_word) >= 3:
                        best_match_score = max(best_match_score, 0.6)
                    # Check for fuzzy word similarity (for typos like "community" vs "comminity")
                    elif len(input_word) >= 4 and len(room_word) >= 4:
                        word_similarity = difflib.SequenceMatcher(None, input_word, room_word).ratio()
                        if word_similarity >= 0.8:  # 80% similarity for individual words
                            best_match_score = max(best_match_score, word_similarity * 0.9)
                
                # Add the best score for this input word
                word_matches += best_match_score
                if best_match_score > 0:
                    matched_chars += len(input_word)
            
            # Calculate combined score
            word_score = word_matches / len(input_words) if input_words else 0
            char_score = matched_chars / total_input_chars if total_input_chars > 0 else 0
            combined_score = (word_score * 0.7) + (char_score * 0.3)
            
            if combined_score > best_score and combined_score >= 0.5:  # 50% threshold for partial matching
                best_score = combined_score
                best_match = room_name
        
        if best_match:
            return best_match
        
        # Fallback to traditional fuzzy matching
        closest_matches = difflib.get_close_matches(
            input_lower, 
            [name.lower() for name in room_names], 
            n=1, 
            cutoff=0.6
        )
        
        if closest_matches:
            for room_name in room_names:
                if room_name.lower() == closest_matches[0]:
                    return room_name
        
        return None
    
    def register_global_chat_channel(self, guild_id, channel_id, room_name, guild_name=None, channel_name=None, registered_by=None):
        """Register a channel for global chat room"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if room exists
            cursor.execute('''
                SELECT room_name FROM global_chat_rooms 
                WHERE room_name = ? AND is_active = TRUE
            ''', (room_name,))
            
            if not cursor.fetchone():
                return "room_not_found"
            
            dhaka_time = datetime.now(self.timezone).strftime('%Y-%m-%d %H:%M:%S')
            
            try:
                cursor.execute('''
                    INSERT INTO global_chat_channels (guild_id, channel_id, room_name, guild_name, channel_name, registered_by, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (guild_id, channel_id, room_name, guild_name, channel_name, registered_by, dhaka_time))
                return True
            except sqlite3.IntegrityError:
                cursor.execute('''
                    UPDATE global_chat_channels 
                    SET room_name = ?, guild_name = ?, channel_name = ?, is_active = TRUE, created_at = ?
                    WHERE guild_id = ? AND channel_id = ?
                ''', (room_name, guild_name, channel_name, dhaka_time, guild_id, channel_id))
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
    
    def get_global_chat_channels(self, room_name=None):
        """Get all registered global chat channels, optionally filtered by room"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if room_name:
                cursor.execute('''
                    SELECT guild_id, channel_id, guild_name, channel_name, room_name, registered_by
                    FROM global_chat_channels 
                    WHERE room_name = ? AND is_active = TRUE
                    ORDER BY guild_name
                ''', (room_name,))
            else:
                cursor.execute('''
                    SELECT guild_id, channel_id, guild_name, channel_name, room_name, registered_by
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
                    'channel_name': result[3],
                    'room_name': result[4],
                    'registered_by': result[5]
                })
            
            return channels
    
    def is_global_chat_channel(self, guild_id, channel_id):
        """Check if a channel is registered for global chat and return room name"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT room_name FROM global_chat_channels 
                WHERE guild_id = ? AND channel_id = ? AND is_active = TRUE
            ''', (guild_id, channel_id))
            result = cursor.fetchone()
            return result[0] if result else None
    
    def log_global_chat_message(self, message_id, room_name, guild_id, channel_id, user_id, username, guild_name, content, reply_to_message_id=None, reply_to_username=None, reply_to_content=None):
        """Log a global chat message with optional reply data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            dhaka_time = datetime.now(self.timezone).strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                INSERT INTO global_chat_messages 
                (message_id, room_name, guild_id, channel_id, user_id, username, guild_name, content, reply_to_message_id, reply_to_username, reply_to_content, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (message_id, room_name, guild_id, channel_id, user_id, username, guild_name, content, reply_to_message_id, reply_to_username, reply_to_content, dhaka_time))
    
    def get_message_for_reply(self, message_id, room_name):
        """Get message data for reply functionality"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT username, content, user_id FROM global_chat_messages 
                WHERE message_id = ? AND room_name = ?
                ORDER BY timestamp DESC LIMIT 1
            ''', (message_id, room_name))
            result = cursor.fetchone()
            if result:
                return {
                    'username': result[0],
                    'content': result[1],
                    'user_id': result[2]
                }
            return None
    
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
    
    def get_room_permissions(self, room_name):
        """Get permissions for a specific room"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT allow_urls, allow_files, enable_bad_word_filter, 
                       max_message_length, rate_limit_seconds, allow_mentions, allow_emojis
                FROM room_permissions 
                WHERE room_name = ?
            ''', (room_name,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'allow_urls': bool(result[0]),
                    'allow_files': bool(result[1]),
                    'enable_bad_word_filter': bool(result[2]),
                    'max_message_length': result[3],
                    'rate_limit_seconds': result[4],
                    'allow_mentions': bool(result[5]),
                    'allow_emojis': bool(result[6])
                }
            else:
                # Return default permissions
                return {
                    'allow_urls': False,
                    'allow_files': False,
                    'enable_bad_word_filter': True,
                    'max_message_length': 2000,
                    'rate_limit_seconds': 3,
                    'allow_mentions': True,
                    'allow_emojis': True
                }
    
    def update_room_permission(self, room_name, permission_name, value, updated_by):
        """Update a specific permission for a room"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            dhaka_time = datetime.now(self.timezone).strftime('%Y-%m-%d %H:%M:%S')
            
            # First ensure the room has permissions entry
            cursor.execute('''
                INSERT OR IGNORE INTO room_permissions (room_name, updated_by, updated_at)
                VALUES (?, ?, ?)
            ''', (room_name, updated_by, dhaka_time))
            
            # Update the specific permission
            query = f'''
                UPDATE room_permissions 
                SET {permission_name} = ?, updated_by = ?, updated_at = ?
                WHERE room_name = ?
            '''
            cursor.execute(query, (value, updated_by, dhaka_time, room_name))
            return cursor.rowcount > 0
    
    def is_room_owner(self, room_name, user_id):
        """Check if user is the owner of the room"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT created_by FROM global_chat_rooms 
                WHERE room_name = ? AND created_by = ?
            ''', (room_name, user_id))
            return cursor.fetchone() is not None
    
    def get_room_owner(self, room_name):
        """Get the owner of a room"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT created_by FROM global_chat_rooms 
                WHERE room_name = ?
            ''', (room_name,))
            result = cursor.fetchone()
            return result[0] if result else None
    
    def get_room_by_id(self, room_id):
        """Get room details by room ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, room_name, created_by, created_at, max_servers 
                FROM global_chat_rooms 
                WHERE id = ? AND is_active = TRUE
            ''', (room_id,))
            result = cursor.fetchone()
            if result:
                return {
                    'id': result[0],
                    'room_name': result[1],
                    'created_by': result[2],
                    'created_at': result[3],
                    'max_servers': result[4]
                }
            return None
    
    def get_room_id_by_name(self, room_name):
        """Get room ID by room name"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id FROM global_chat_rooms 
                WHERE room_name = ? AND is_active = TRUE
            ''', (room_name,))
            result = cursor.fetchone()
            return result[0] if result else None
    
    def is_room_owner_by_id(self, room_id, user_id):
        """Check if user is the owner of the room by room ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT created_by FROM global_chat_rooms 
                WHERE id = ? AND created_by = ? AND is_active = TRUE
            ''', (room_id, user_id))
            return cursor.fetchone() is not None
    
    def get_room_permissions_by_id(self, room_id):
        """Get permissions for a room by room ID"""
        room = self.get_room_by_id(room_id)
        if not room:
            return None
        return self.get_room_permissions(room['room_name'])
    
    def update_room_permission_by_id(self, room_id, permission_name, value, updated_by):
        """Update a specific permission for a room by room ID"""
        room = self.get_room_by_id(room_id)
        if not room:
            return False
        return self.update_room_permission(room['room_name'], permission_name, value, updated_by)
    
