#!/usr/bin/env python3
"""
Database migration script to add reply feature columns to existing database.
Run this script once to upgrade your database schema.
"""

import sqlite3
import os
from pathlib import Path

def migrate_database(db_path="bot_database.db"):
    """Add reply feature columns to existing global_chat_messages table"""
    print(f"🔄 Starting database migration for reply feature...")
    print(f"📁 Database path: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check if columns already exist
            cursor.execute("PRAGMA table_info(global_chat_messages)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Add missing columns one by one
            columns_to_add = [
                ('reply_to_message_id', 'TEXT'),
                ('reply_to_username', 'TEXT'), 
                ('reply_to_content', 'TEXT')
            ]
            
            added_columns = []
            for column_name, column_type in columns_to_add:
                if column_name not in columns:
                    print(f"➕ Adding column: {column_name}")
                    cursor.execute(f'''
                        ALTER TABLE global_chat_messages 
                        ADD COLUMN {column_name} {column_type}
                    ''')
                    added_columns.append(column_name)
                else:
                    print(f"✅ Column already exists: {column_name}")
            
            conn.commit()
            
            if added_columns:
                print(f"✅ Successfully added {len(added_columns)} columns: {', '.join(added_columns)}")
            else:
                print("✅ All reply feature columns already exist")
                
            print("🎉 Database migration completed successfully!")
            return True
            
    except sqlite3.Error as e:
        print(f"❌ Database migration failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during migration: {e}")
        return False

if __name__ == "__main__":
    # Try common database paths
    possible_paths = [
        "bot_database.db",
        "../bot_database.db", 
        "/root/mahadi/balu/bot_database.db"
    ]
    
    db_path = None
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if db_path:
        success = migrate_database(db_path)
        if success:
            print("\n🚀 Migration complete! You can now restart your bot.")
        else:
            print("\n❌ Migration failed! Please check the error messages above.")
    else:
        print("❌ Could not find bot_database.db file.")
        print("📝 Available files:")
        for file in os.listdir("."):
            if file.endswith(".db"):
                print(f"   - {file}")
        print("\n💡 Usage: python migrate_reply_feature.py")