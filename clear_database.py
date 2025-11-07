#!/usr/bin/env python3
"""
Database clearing utility for the Discord bot.
This script will clear all data from the bot's database.

Usage: python clear_database.py
"""

import sqlite3
import os
import sys
from datetime import datetime

def clear_database(db_path="bot_database.db"):
    """Clear all data from the bot database"""
    
    if not os.path.exists(db_path):
        print(f"❌ Database file '{db_path}' not found.")
        return False
    
    print(f"🗃️ Found database: {db_path}")
    
    # Get database file size
    file_size = os.path.getsize(db_path)
    print(f"📊 Database size: {file_size:,} bytes")
    
    # Show warning
    print("\n⚠️  WARNING: This will permanently delete ALL data from the database!")
    print("This includes:")
    print("  • All chat rooms")
    print("  • All channel subscriptions") 
    print("  • All message logs")
    print("  • All settings")
    
    # Ask for confirmation
    response = input("\nAre you sure you want to continue? Type 'YES' to confirm: ")
    
    if response != "YES":
        print("❌ Database clear cancelled.")
        return False
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Get list of all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            if not tables:
                print("✅ Database is already empty.")
                return True
            
            print(f"\n🧹 Clearing {len(tables)} tables...")
            
            # Clear each table
            for table in tables:
                table_name = table[0]
                if table_name != 'sqlite_sequence':  # Skip system table
                    try:
                        # Get row count before clearing
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        row_count = cursor.fetchone()[0]
                        
                        # Clear the table
                        cursor.execute(f"DELETE FROM {table_name}")
                        print(f"  ✅ Cleared {table_name} ({row_count:,} rows)")
                    except sqlite3.Error as e:
                        print(f"  ❌ Error clearing {table_name}: {e}")
            
            # Reset auto-increment counters
            cursor.execute("DELETE FROM sqlite_sequence")
            
            conn.commit()
            
        print("\n🎉 Database cleared successfully!")
        print(f"📅 Cleared at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Show new file size
        new_file_size = os.path.getsize(db_path)
        print(f"📊 New database size: {new_file_size:,} bytes")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def show_database_info(db_path="bot_database.db"):
    """Show information about the database without clearing it"""
    
    if not os.path.exists(db_path):
        print(f"❌ Database file '{db_path}' not found.")
        return
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            print(f"📊 Database Information: {db_path}")
            print(f"📁 File size: {os.path.getsize(db_path):,} bytes")
            print()
            
            # Get list of all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            if not tables:
                print("📋 No tables found in database.")
                return
            
            print(f"📋 Found {len(tables)} tables:")
            print()
            
            total_rows = 0
            for table in tables:
                table_name = table[0]
                if table_name != 'sqlite_sequence':
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        row_count = cursor.fetchone()[0]
                        total_rows += row_count
                        print(f"  📊 {table_name}: {row_count:,} rows")
                    except sqlite3.Error as e:
                        print(f"  ❌ {table_name}: Error reading ({e})")
            
            print()
            print(f"📈 Total rows across all tables: {total_rows:,}")
            
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def main():
    """Main function"""
    print("🤖 Discord Bot Database Utility")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--info" or sys.argv[1] == "-i":
            show_database_info()
            return
        elif sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("Usage:")
            print("  python clear_database.py         # Clear the database")
            print("  python clear_database.py --info  # Show database info")
            print("  python clear_database.py --help  # Show this help")
            return
    
    # Default action: clear database
    success = clear_database()
    
    if success:
        print("\n💡 Tip: Restart the bot to reinitialize the database with default settings.")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()