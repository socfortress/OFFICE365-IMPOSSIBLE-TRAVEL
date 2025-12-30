import os
from pathlib import Path
from typing import List
from typing import Optional

import aiosqlite
from loguru import logger


class DatabaseService:
    """Service for managing login history in SQLite database"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        # Ensure the directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    async def initialize(self):
        """Initialize the database and create tables if they don't exist"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS login_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user TEXT NOT NULL,
                    ip TEXT NOT NULL,
                    country TEXT NOT NULL,
                    city TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """,
            )
            # Create index on user for faster lookups
            await db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_user_timestamp
                ON login_history(user, timestamp DESC)
                """,
            )
            await db.commit()
            logger.info(f"Database initialized at {self.db_path}")

    async def add_login(
        self,
        user: str,
        ip: str,
        country: str,
        city: str,
        latitude: float,
        longitude: float,
        timestamp: str,
        max_records: int = 10,
    ):
        """Add a login record and maintain max records per user"""
        async with aiosqlite.connect(self.db_path) as db:
            # Insert the new record
            await db.execute(
                """
                INSERT INTO login_history
                (user, ip, country, city, latitude, longitude, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (user, ip, country, city, latitude, longitude, timestamp),
            )

            # Get count of records for this user
            cursor = await db.execute(
                "SELECT COUNT(*) FROM login_history WHERE user = ?",
                (user,),
            )
            count = (await cursor.fetchone())[0]

            # If exceeding max records, delete oldest ones
            if count > max_records:
                records_to_delete = count - max_records
                await db.execute(
                    """
                    DELETE FROM login_history
                    WHERE id IN (
                        SELECT id FROM login_history
                        WHERE user = ?
                        ORDER BY timestamp ASC
                        LIMIT ?
                    )
                    """,
                    (user, records_to_delete),
                )
                logger.info(f"Deleted {records_to_delete} old records for user {user}")

            await db.commit()
            logger.info(f"Added login record for user {user} from IP {ip}")

    async def get_recent_logins(self, user: str, limit: int = 10) -> List[dict]:
        """Get recent login records for a user"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT user, ip, country, city, latitude, longitude, timestamp
                FROM login_history
                WHERE user = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (user, limit),
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_last_login(self, user: str) -> Optional[dict]:
        """Get the most recent login for a user"""
        logins = await self.get_recent_logins(user, limit=1)
        return logins[0] if logins else None

    async def purge_database(self) -> int:
        """Delete all records from the database"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM login_history")
            count = (await cursor.fetchone())[0]

            await db.execute("DELETE FROM login_history")
            await db.commit()

            logger.warning(f"Purged {count} records from database")
            return count

    async def get_stats(self) -> dict:
        """Get database statistics"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT COUNT(*) as total_records FROM login_history",
            )
            total = (await cursor.fetchone())[0]

            cursor = await db.execute(
                "SELECT COUNT(DISTINCT user) as unique_users FROM login_history",
            )
            unique_users = (await cursor.fetchone())[0]

            return {
                "total_records": total,
                "unique_users": unique_users,
            }


# Singleton instance
_db_service: Optional[DatabaseService] = None


async def get_database_service() -> DatabaseService:
    """Get or create the database service singleton"""
    global _db_service
    if _db_service is None:
        db_path = os.getenv("DATABASE_PATH", "./data/impossible_travel.db")
        _db_service = DatabaseService(db_path)
        await _db_service.initialize()
    return _db_service
