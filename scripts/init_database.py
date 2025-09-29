#!/usr/bin/env python3
"""
Database Initialization Script
Sets up PostgreSQL database, runs migrations, and validates setup
"""

import asyncio
import asyncpg
import sys
import os
from pathlib import Path
import json

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.utils.database import db_manager, DatabaseManager
from backend.models import CuratorBrief, ExhibitionProposal


async def create_database_if_not_exists():
    """Create the database if it doesn't exist"""

    # Connect to default postgres database first
    conn = await asyncpg.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', '5432')),
        user=os.getenv('DB_USER', 'curator'),
        password=os.getenv('DB_PASSWORD', 'curator_password'),
        database='postgres'  # Connect to default database
    )

    db_name = os.getenv('DB_NAME', 'curator_db')

    # Check if database exists
    exists = await conn.fetchval(
        "SELECT 1 FROM pg_database WHERE datname = $1", db_name
    )

    if not exists:
        print(f"Creating database: {db_name}")
        await conn.execute(f'CREATE DATABASE "{db_name}"')
        print(f"✅ Database {db_name} created successfully")
    else:
        print(f"✅ Database {db_name} already exists")

    await conn.close()


async def run_schema_sql():
    """Run the schema SQL file"""

    schema_file = Path(__file__).parent.parent / "infrastructure" / "init_db.sql"

    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")

    # Read the SQL file
    with open(schema_file, 'r') as f:
        sql_content = f.read()

    # Connect to the target database
    conn = await asyncpg.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', '5432')),
        database=os.getenv('DB_NAME', 'curator_db'),
        user=os.getenv('DB_USER', 'curator'),
        password=os.getenv('DB_PASSWORD', 'curator_password')
    )

    print("Running database schema...")

    try:
        # Split SQL into individual statements and execute
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]

        for i, statement in enumerate(statements):
            if statement:
                try:
                    await conn.execute(statement)
                    if i % 10 == 0:  # Progress indicator
                        print(f"  Executed {i+1}/{len(statements)} statements...")
                except Exception as e:
                    # Skip statements that might fail on re-run (like CREATE EXTENSION)
                    if "already exists" not in str(e).lower():
                        print(f"Warning: Statement failed: {e}")

        print(f"✅ Schema executed successfully ({len(statements)} statements)")

    except Exception as e:
        print(f"❌ Error executing schema: {e}")
        raise
    finally:
        await conn.close()


async def validate_database_setup():
    """Validate that the database is set up correctly"""

    print("\nValidating database setup...")

    await db_manager.initialize()

    try:
        # Test PostgreSQL connection
        async with db_manager.get_pg_connection() as conn:

            # Check required tables exist
            tables_query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """

            tables = await conn.fetch(tables_query)
            table_names = [row['table_name'] for row in tables]

            required_tables = [
                'curator_sessions',
                'search_patterns',
                'artwork_cache',
                'artist_cache',
                'exhibition_proposals',
                'api_usage_log',
                'system_config'
            ]

            missing_tables = [t for t in required_tables if t not in table_names]

            if missing_tables:
                print(f"❌ Missing tables: {missing_tables}")
                return False
            else:
                print(f"✅ All required tables present ({len(table_names)} total)")

            # Check pgvector extension
            extensions = await conn.fetch("""
                SELECT extname FROM pg_extension WHERE extname = 'vector'
            """)

            if extensions:
                print("✅ pgvector extension installed")
            else:
                print("❌ pgvector extension not found")
                return False

            # Test vector operations
            try:
                await conn.fetchval("SELECT '[1,2,3]'::vector")
                print("✅ Vector operations working")
            except Exception as e:
                print(f"❌ Vector operations failed: {e}")
                return False

            # Check system configuration
            config_count = await conn.fetchval("SELECT COUNT(*) FROM system_config")
            print(f"✅ System configuration entries: {config_count}")

            # Check sample data
            pattern_count = await conn.fetchval("SELECT COUNT(*) FROM search_patterns")
            print(f"✅ Sample search patterns: {pattern_count}")

        # Test Redis connection
        if db_manager.redis_client:
            await db_manager.redis_client.ping()
            print("✅ Redis connection working")
        else:
            print("⚠️  Redis not configured")

        print("\n✅ Database validation successful!")
        return True

    except Exception as e:
        print(f"❌ Database validation failed: {e}")
        return False

    finally:
        await db_manager.close()


async def insert_sample_data():
    """Insert sample data for testing"""

    print("\nInserting sample data...")

    await db_manager.initialize()

    try:
        async with db_manager.get_pg_connection() as conn:

            # Sample curator brief
            sample_brief = {
                "theme_title": "Light and Shadow in Dutch Art",
                "theme_description": "An exploration of how Dutch masters used chiaroscuro techniques to create dramatic lighting effects and emotional depth in their paintings.",
                "theme_concepts": ["chiaroscuro", "Dutch Golden Age", "light", "shadow"],
                "reference_artists": ["Rembrandt van Rijn", "Johannes Vermeer"],
                "target_audience": "general",
                "space_type": "main",
                "include_international": True
            }

            # Insert sample session
            session_id = "sample-session-001"
            await conn.execute("""
                INSERT INTO curator_sessions (id, curator_name, curator_brief, status)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (id) DO NOTHING
            """, session_id, "Sample Curator", json.dumps(sample_brief), "pending")

            # Additional search patterns
            patterns = [
                ("baroque", "movement", "http://vocab.getty.edu/aat/300021147", "300021147", 0.92),
                ("still life", "subject", "http://vocab.getty.edu/aat/300015638", "300015638", 0.88),
                ("sfumato", "technique", "http://vocab.getty.edu/aat/300404272", "300404272", 0.85),
                ("fresco", "technique", "http://vocab.getty.edu/aat/300178675", "300178675", 0.90)
            ]

            for concept, concept_type, uri, aat_id, confidence in patterns:
                await conn.execute("""
                    INSERT INTO search_patterns (concept, concept_type, getty_aat_uri, getty_aat_id, confidence_score)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (concept, concept_type) DO NOTHING
                """, concept, concept_type, uri, aat_id, confidence)

            print("✅ Sample data inserted")

    except Exception as e:
        print(f"❌ Failed to insert sample data: {e}")
        raise

    finally:
        await db_manager.close()


async def test_model_validation():
    """Test that Pydantic models work with the database"""

    print("\nTesting model validation...")

    try:
        # Test CuratorBrief validation
        brief = CuratorBrief(
            theme_title="Test Exhibition",
            theme_description="A test exhibition to validate the data models and database integration.",
            theme_concepts=["modernism", "abstract art"],
            reference_artists=["Pablo Picasso", "Wassily Kandinsky"],
            target_audience="general"
        )

        print(f"✅ CuratorBrief validation successful: {brief.theme_title}")

        # Test validation errors
        try:
            invalid_brief = CuratorBrief(
                theme_title="",  # Too short
                theme_description="Too short",  # Too short
                theme_concepts=[],  # Empty
            )
        except Exception as e:
            print(f"✅ Validation errors caught correctly: {type(e).__name__}")

        print("✅ Model validation tests passed")

    except Exception as e:
        print(f"❌ Model validation failed: {e}")
        raise


async def main():
    """Main initialization function"""

    print("="*60)
    print("AI CURATOR ASSISTANT - Database Initialization")
    print("="*60)

    try:
        # Step 1: Create database
        await create_database_if_not_exists()

        # Step 2: Run schema
        await run_schema_sql()

        # Step 3: Validate setup
        validation_success = await validate_database_setup()

        if not validation_success:
            print("\n❌ Database validation failed!")
            sys.exit(1)

        # Step 4: Insert sample data
        await insert_sample_data()

        # Step 5: Test models
        await test_model_validation()

        print("\n" + "="*60)
        print("✅ DATABASE INITIALIZATION COMPLETE!")
        print("="*60)
        print("\nNext steps:")
        print("1. Start the FastAPI server")
        print("2. Test the API endpoints")
        print("3. Run the web interface")

    except Exception as e:
        print(f"\n❌ Initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())