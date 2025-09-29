"""
Database utilities and connection management
Handles PostgreSQL, Redis, and potential Neo4j connections
"""
import asyncio
import asyncpg
import redis.asyncio as redis
from typing import Optional, Dict, Any, List
import json
import logging
from datetime import datetime, timedelta
import os
from contextlib import asynccontextmanager

from backend.config import data_config

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages all database connections for the AI Curator Assistant
    """

    def __init__(self):
        self.pg_pool: Optional[asyncpg.Pool] = None
        self.redis_client: Optional[redis.Redis] = None
        self._config = {
            'postgresql': {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': int(os.getenv('DB_PORT', '5432')),
                'database': os.getenv('DB_NAME', 'curator_db'),
                'user': os.getenv('DB_USER', 'curator'),
                'password': os.getenv('DB_PASSWORD', 'curator_password'),
                'min_size': 5,
                'max_size': 20
            },
            'redis': {
                'host': os.getenv('REDIS_HOST', 'localhost'),
                'port': int(os.getenv('REDIS_PORT', '6379')),
                'password': os.getenv('REDIS_PASSWORD', 'curator_redis_password'),
                'db': int(os.getenv('REDIS_DB', '0'))
            }
        }

    async def initialize(self):
        """Initialize all database connections"""
        await self._init_postgresql()
        await self._init_redis()
        logger.info("Database connections initialized")

    async def _init_postgresql(self):
        """Initialize PostgreSQL connection pool"""
        try:
            self.pg_pool = await asyncpg.create_pool(
                host=self._config['postgresql']['host'],
                port=self._config['postgresql']['port'],
                database=self._config['postgresql']['database'],
                user=self._config['postgresql']['user'],
                password=self._config['postgresql']['password'],
                min_size=self._config['postgresql']['min_size'],
                max_size=self._config['postgresql']['max_size'],
                command_timeout=30
            )
            logger.info("PostgreSQL connection pool created")
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL pool: {e}")
            raise

    async def _init_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.Redis(
                host=self._config['redis']['host'],
                port=self._config['redis']['port'],
                password=self._config['redis']['password'],
                db=self._config['redis']['db'],
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )

            # Test connection
            await self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def close(self):
        """Close all database connections"""
        if self.pg_pool:
            await self.pg_pool.close()
            logger.info("PostgreSQL pool closed")

        if self.redis_client:
            await self.redis_client.aclose()
            logger.info("Redis connection closed")

    @asynccontextmanager
    async def get_pg_connection(self):
        """Get PostgreSQL connection from pool"""
        if not self.pg_pool:
            raise RuntimeError("PostgreSQL pool not initialized")

        async with self.pg_pool.acquire() as conn:
            yield conn

    async def health_check(self) -> Dict[str, bool]:
        """Check health of all database connections"""
        health = {
            'postgresql': False,
            'redis': False
        }

        # Test PostgreSQL
        try:
            async with self.get_pg_connection() as conn:
                await conn.fetchval("SELECT 1")
                health['postgresql'] = True
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")

        # Test Redis
        try:
            if self.redis_client:
                await self.redis_client.ping()
                health['redis'] = True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")

        return health


# Global database manager instance
db_manager = DatabaseManager()


class SessionManager:
    """
    Manages curator sessions using Redis and PostgreSQL
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.session_prefix = "session:"
        self.default_timeout = 3600  # 1 hour

    async def create_session(self, session_id: str, curator_brief: Dict[str, Any]) -> str:
        """Create a new curator session"""

        # Store session in PostgreSQL
        async with self.db.get_pg_connection() as conn:
            await conn.execute("""
                INSERT INTO curator_sessions (id, curator_brief, status, created_at)
                VALUES ($1, $2, 'pending', $3)
            """, session_id, json.dumps(curator_brief), datetime.utcnow())

        # Store session state in Redis for quick access
        session_key = f"{self.session_prefix}{session_id}"
        session_data = {
            'id': session_id,
            'status': 'pending',
            'current_stage': 1,
            'progress': 0,
            'created_at': datetime.utcnow().isoformat(),
            'curator_brief': curator_brief
        }

        await self.db.redis_client.hset(session_key, mapping={
            k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
            for k, v in session_data.items()
        })

        # Set expiration
        await self.db.redis_client.expire(session_key, self.default_timeout)

        logger.info(f"Created session {session_id}")
        return session_id

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        session_key = f"{self.session_prefix}{session_id}"

        # Try Redis first (faster)
        session_data = await self.db.redis_client.hgetall(session_key)

        if session_data:
            # Parse JSON fields
            for key in ['curator_brief', 'enriched_query', 'discovered_artists', 'discovered_artworks']:
                if key in session_data and session_data[key]:
                    try:
                        session_data[key] = json.loads(session_data[key])
                    except (json.JSONDecodeError, TypeError):
                        pass

            return session_data

        # Fallback to PostgreSQL
        async with self.db.get_pg_connection() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM curator_sessions WHERE id = $1
            """, session_id)

            if row:
                return dict(row)

        return None

    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session data"""
        session_key = f"{self.session_prefix}{session_id}"

        # Update Redis
        redis_updates = {
            k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
            for k, v in updates.items()
        }
        redis_updates['updated_at'] = datetime.utcnow().isoformat()

        await self.db.redis_client.hset(session_key, mapping=redis_updates)

        # Update PostgreSQL
        set_clauses = []
        values = []
        param_count = 1

        for key, value in updates.items():
            if key in ['curator_brief', 'enriched_query', 'discovered_artists', 'discovered_artworks', 'final_proposals']:
                set_clauses.append(f"{key} = ${param_count}")
                values.append(json.dumps(value) if isinstance(value, (dict, list)) else value)
            else:
                set_clauses.append(f"{key} = ${param_count}")
                values.append(value)
            param_count += 1

        if set_clauses:
            query = f"""
                UPDATE curator_sessions
                SET {', '.join(set_clauses)}, updated_at = ${ param_count}
                WHERE id = ${ param_count + 1}
            """
            values.extend([datetime.utcnow(), session_id])

            async with self.db.get_pg_connection() as conn:
                await conn.execute(query, *values)

        logger.info(f"Updated session {session_id}")
        return True

    async def list_active_sessions(self) -> List[Dict[str, Any]]:
        """List all active sessions"""
        async with self.db.get_pg_connection() as conn:
            rows = await conn.fetch("""
                SELECT id, curator_name, status, current_stage, progress, created_at, updated_at
                FROM curator_sessions
                WHERE status NOT IN ('complete', 'cancelled', 'error')
                ORDER BY created_at DESC
            """)

            return [dict(row) for row in rows]

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)

        async with self.db.get_pg_connection() as conn:
            # Mark old sessions as expired
            result = await conn.execute("""
                UPDATE curator_sessions
                SET status = 'expired'
                WHERE status IN ('pending', 'stage1_processing', 'stage2_processing', 'stage3_processing')
                AND updated_at < $1
            """, cutoff_time)

        return int(result.split()[-1])  # Extract affected row count


class CacheManager:
    """
    Manages caching for artwork, artist, and search pattern data
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.cache_prefixes = {
            'artwork': 'artwork:',
            'artist': 'artist:',
            'search_pattern': 'pattern:',
            'api_response': 'api:'
        }

    async def cache_artwork(self, artwork_uri: str, artwork_data: Dict[str, Any], ttl: int = 86400):
        """Cache artwork data"""
        key = f"{self.cache_prefixes['artwork']}{artwork_uri}"
        await self.db.redis_client.setex(
            key,
            ttl,
            json.dumps(artwork_data, default=str)
        )

    async def get_cached_artwork(self, artwork_uri: str) -> Optional[Dict[str, Any]]:
        """Get cached artwork data"""
        key = f"{self.cache_prefixes['artwork']}{artwork_uri}"
        data = await self.db.redis_client.get(key)

        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse cached artwork data for {artwork_uri}")

        return None

    async def cache_api_response(self, endpoint: str, query_hash: str, response_data: Any, ttl: int = 3600):
        """Cache API response"""
        key = f"{self.cache_prefixes['api_response']}{endpoint}:{query_hash}"
        await self.db.redis_client.setex(
            key,
            ttl,
            json.dumps(response_data, default=str)
        )

    async def get_cached_api_response(self, endpoint: str, query_hash: str) -> Optional[Any]:
        """Get cached API response"""
        key = f"{self.cache_prefixes['api_response']}{endpoint}:{query_hash}"
        data = await self.db.redis_client.get(key)

        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse cached API response for {endpoint}:{query_hash}")

        return None

    async def invalidate_cache(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern"""
        keys = []
        async for key in self.db.redis_client.scan_iter(match=pattern):
            keys.append(key)

        if keys:
            return await self.db.redis_client.delete(*keys)
        return 0


# Convenience functions for common database operations
async def init_database():
    """Initialize database connections"""
    await db_manager.initialize()


async def close_database():
    """Close database connections"""
    await db_manager.close()


async def get_session_manager() -> SessionManager:
    """Get session manager instance"""
    return SessionManager(db_manager)


async def get_cache_manager() -> CacheManager:
    """Get cache manager instance"""
    return CacheManager(db_manager)


__all__ = [
    'DatabaseManager',
    'SessionManager',
    'CacheManager',
    'db_manager',
    'init_database',
    'close_database',
    'get_session_manager',
    'get_cache_manager'
]