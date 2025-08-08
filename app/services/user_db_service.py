# Path: app/services/user_db_service.py

import sqlite3
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from app.core.config import DATABASE_URL
from app.core.security import get_password_hash


logger = logging.getLogger(__name__)

class UserDBService:
    def __init__(self, db_path: str = DATABASE_URL):
        self.db_path = db_path
        self._conn = None
        self._connect()
        self._create_table_if_not_exists()

    def _connect(self):
        """Establish a connection to the SQLite database."""
        try:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row # Allows accessing columns by name
            logger.info(f"--- UserDBService: Successfully connected to database at {self.db_path} ---")
        except sqlite3.Error as e:
            logger.critical(f"--- UserDBService: Database connection failed: {e} ---", exc_info=True)
            raise

    def _create_table_if_not_exists(self):
        """Creates the users table and a default admin if the table is empty."""
        try:
            cursor = self._conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    hashed_password TEXT NOT NULL,
                    is_admin INTEGER NOT NULL DEFAULT 0
                )
            """)
            
            # Check if any users exist
            cursor.execute("SELECT COUNT(id) FROM users")
            user_count = cursor.fetchone()[0]
            
            # If no users exist, create a default admin to prevent lockout
            if user_count == 0:
                logger.info("--- UserDBService: No users found. Creating default admin user. ---")
                default_admin_pass = "353ip455w0rd?"
                hashed_password = get_password_hash(default_admin_pass)
                cursor.execute(
                    "INSERT INTO users (username, hashed_password, is_admin) VALUES (?, ?, ?)",
                    ("admin", hashed_password, 1) # 1 for True
                )
                logger.info(f"--- Default admin created with username 'admin' and password '{default_admin_pass}'. Please change this password. ---")

            self._conn.commit()
        except sqlite3.Error as e:
            logger.error(f"--- UserDBService: Failed to create or verify users table: {e} ---", exc_info=True)
            self._conn.rollback()

    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Retrieves a user by username from the database."""
        try:
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            user_row = cursor.fetchone()
            return dict(user_row) if user_row else None
        except sqlite3.Error as e:
            logger.error(f"--- UserDBService: Failed to get user '{username}': {e} ---")
            return None

    def add_user(self, username: str, plain_password: str, is_admin: bool = False) -> bool:
        """Adds a new user to the database. Returns True on success, False on failure."""
        if self.get_user(username):
            logger.warning(f"--- UserDBService: Attempted to add existing user '{username}'. ---")
            return False # User already exists
            
        try:
            hashed_password = get_password_hash(plain_password)
            is_admin_int = 1 if is_admin else 0
            
            cursor = self._conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, hashed_password, is_admin) VALUES (?, ?, ?)",
                (username, hashed_password, is_admin_int)
            )
            self._conn.commit()
            logger.info(f"--- UserDBService: Successfully added new user '{username}'. ---")
            return True
        except sqlite3.Error as e:
            logger.error(f"--- UserDBService: Failed to add user '{username}': {e} ---", exc_info=True)
            self._conn.rollback()
            return False

# Create a singleton instance to be used across the application
user_db_service = UserDBService()