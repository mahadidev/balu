#!/usr/bin/env python3
"""
Database migration script for Global Chat System.
Handles database initialization and schema migrations.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.database.models import Base
from shared.database.manager import db_manager
from sqlalchemy import text


async def create_database_if_not_exists():
    """Create the database if it doesn't exist."""
    print("🔍 Checking if database exists...")
    
    try:
        # Try to connect to the database
        await db_manager.initialize()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


async def create_tables():
    """Create all database tables."""
    print("🏗️  Creating database tables...")
    
    try:
        # Create all tables
        async with db_manager.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Database tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False


async def create_initial_data():
    """Create initial data and default settings."""
    print("📝 Creating initial data...")
    
    try:
        async with db_manager.session() as session:
            # Check if we already have data
            from shared.database.models import ChatRoom
            from sqlalchemy import select
            
            result = await session.execute(select(ChatRoom))
            existing_rooms = result.scalars().all()
            
            if existing_rooms:
                print("📊 Database already has data, skipping initial data creation")
                return True
            
            # Create default room
            print("🏠 Creating default room...")
            room_id = await db_manager.create_room(
                name="general",
                created_by="system",
                max_servers=50
            )
            
            if room_id:
                print(f"✅ Created default room 'general' with ID: {room_id}")
                
                # Get and display the default permissions
                permissions = await db_manager.get_room_permissions(room_id)
                print("📋 Default room permissions:")
                for key, value in permissions.items():
                    print(f"  - {key}: {value}")
            else:
                print("❌ Failed to create default room")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Error creating initial data: {e}")
        return False


async def run_custom_migrations():
    """Run any custom migration scripts."""
    print("🔄 Running custom migrations...")
    
    try:
        async with db_manager.session() as session:
            # Example: Add any custom data transformations here
            
            # Check for reply feature migration (if coming from old SQLite)
            from sqlalchemy import text
            
            # Check if we need to migrate from old database structure
            try:
                result = await session.execute(text("""
                    SELECT COUNT(*) FROM chat_messages 
                    WHERE reply_to_message_id IS NOT NULL
                """))
                reply_count = result.scalar()
                print(f"📊 Found {reply_count} messages with reply data")
            except Exception:
                # Table might not exist or might have different schema
                print("📊 No existing reply data found")
            
        print("✅ Custom migrations completed")
        return True
    except Exception as e:
        print(f"❌ Error running custom migrations: {e}")
        return False


async def verify_migration():
    """Verify that migration completed successfully."""
    print("🔍 Verifying migration...")
    
    try:
        # Test basic database operations
        all_rooms = await db_manager.get_all_rooms()
        print(f"📊 Found {len(all_rooms)} rooms in database")
        
        # Test live stats
        stats = await db_manager.get_live_stats()
        print(f"📈 Live stats: {stats}")
        
        # Test caching
        from shared.cache.redis_client import redis_client
        await redis_client.set("migration_test", "success", 30)
        result = await redis_client.get("migration_test")
        
        if result and result.decode() == "success":
            print("✅ Redis cache is working")
        else:
            print("❌ Redis cache test failed")
            return False
        
        print("✅ Migration verification successful")
        return True
    except Exception as e:
        print(f"❌ Migration verification failed: {e}")
        return False


async def main():
    """Main migration function."""
    print("🚀 Starting database migration for Global Chat System")
    print("=" * 50)
    
    try:
        # Step 1: Initialize database connection
        if not await create_database_if_not_exists():
            print("❌ Migration failed: Could not connect to database")
            return False
        
        # Step 2: Create tables
        if not await create_tables():
            print("❌ Migration failed: Could not create tables")
            return False
        
        # Step 3: Create initial data
        if not await create_initial_data():
            print("❌ Migration failed: Could not create initial data")
            return False
        
        # Step 4: Run custom migrations
        if not await run_custom_migrations():
            print("❌ Migration failed: Custom migrations failed")
            return False
        
        # Step 5: Initialize Redis
        print("🔄 Initializing Redis cache...")
        from shared.cache.redis_client import redis_client
        await redis_client.initialize()
        print("✅ Redis cache initialized")
        
        # Step 6: Verify migration
        if not await verify_migration():
            print("❌ Migration failed: Verification failed")
            return False
        
        print("=" * 50)
        print("🎉 Database migration completed successfully!")
        print("\n📋 Next steps:")
        print("  1. Start the Discord bot with your bot token")
        print("  2. Access the admin panel at http://localhost:8000")
        print("  3. Create rooms and register Discord channels")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up connections
        try:
            await db_manager.close()
            from shared.cache.redis_client import redis_client
            await redis_client.close()
        except:
            pass


if __name__ == "__main__":
    # Run migration
    success = asyncio.run(main())
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)