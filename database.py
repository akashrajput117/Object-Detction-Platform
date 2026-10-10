import mysql.connector
from mysql.connector import Error
import sqlite3
import config
import logging
import os
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DatabaseManager:
    def __init__(self, use_sqlite_fallback=False, sqlite_path="detection_logs.db"):
        self.host = config.DB_HOST
        self.port = config.DB_PORT
        self.database = config.DB_NAME
        self.user = config.DB_USER
        self.password = config.DB_PASSWORD
        self.use_sqlite_fallback = use_sqlite_fallback
        self.sqlite_path = sqlite_path
        self.backend = None  # 'mysql', 'sqlite', or None
        self.connection = None

    def connect(self, enable_fallback=None):
        """
        Establish a connection to the database.
        Tries MySQL first. If MySQL fails and fallback is enabled, connects to SQLite.
        """
        if enable_fallback is not None:
            self.use_sqlite_fallback = enable_fallback

        if self.is_connected():
            return True

        # Try MySQL connection
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                connection_timeout=3
            )
            if self.connection.is_connected():
                self.backend = "mysql"
                logging.info("Connected to MySQL database successfully.")
                return True
        except (Error, Exception) as e:
            logging.error(f"Error connecting to MySQL: {e}")
            self.connection = None
            self.backend = None

        # If MySQL connection failed, check if SQLite fallback is enabled
        if self.use_sqlite_fallback:
            try:
                self.connection = sqlite3.connect(self.sqlite_path, check_same_thread=False)
                self.backend = "sqlite"
                self._init_sqlite_schema()
                logging.info(f"Connected to local SQLite database fallback: {self.sqlite_path}")
                return True
            except Exception as e:
                logging.error(f"Error initializing SQLite fallback: {e}")
                self.connection = None
                self.backend = None

        return False

    def _init_sqlite_schema(self):
        """Initialize the detection_logs table in SQLite if it doesn't exist."""
        if self.backend == "sqlite" and self.connection is not None:
            cursor = self.connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS detection_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    object_class TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    bbox_x INTEGER NOT NULL,
                    bbox_y INTEGER NOT NULL,
                    bbox_w INTEGER NOT NULL,
                    bbox_h INTEGER NOT NULL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON detection_logs(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_object_class ON detection_logs(object_class)")
            self.connection.commit()
            cursor.close()

    def get_backend(self):
        """Return the active database backend ('mysql', 'sqlite', or None)."""
        return self.backend if self.is_connected() else None

    def is_connected(self):
        """Check if the database connection is active."""
        if self.connection is None:
            return False
            
        if self.backend == "mysql":
            try:
                return self.connection.is_connected()
            except Exception:
                return False
        elif self.backend == "sqlite":
            return True
            
        return False

    def close(self):
        """Close the database connection safely."""
        if self.connection is not None:
            try:
                self.connection.close()
            except Exception as e:
                logging.warning(f"Error closing connection: {e}")
            finally:
                self.connection = None
                self.backend = None
                logging.info("Database connection closed.")

    def log_detection(self, object_class, confidence, bbox_x, bbox_y, bbox_w, bbox_h):
        """Insert a detection event into the database."""
        if not self.is_connected():
            return False
            
        cursor = None
        try:
            if self.backend == "mysql":
                cursor = self.connection.cursor()
                query = """
                    INSERT INTO detection_logs 
                    (object_class, confidence, bbox_x, bbox_y, bbox_w, bbox_h) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                values = (object_class, float(confidence), int(bbox_x), int(bbox_y), int(bbox_w), int(bbox_h))
                cursor.execute(query, values)
                self.connection.commit()
                return True
            elif self.backend == "sqlite":
                cursor = self.connection.cursor()
                query = """
                    INSERT INTO detection_logs 
                    (object_class, confidence, bbox_x, bbox_y, bbox_w, bbox_h) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """
                values = (object_class, float(confidence), int(bbox_x), int(bbox_y), int(bbox_w), int(bbox_h))
                cursor.execute(query, values)
                self.connection.commit()
                return True
        except Exception as e:
            logging.error(f"Failed to insert record into table: {e}")
            return False
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    pass

    def get_recent_logs(self, limit=50):
        """Retrieve recent detection logs."""
        if not self.is_connected():
            return []
            
        cursor = None
        try:
            if self.backend == "mysql":
                cursor = self.connection.cursor(dictionary=True)
                query = f"""
                    SELECT log_id, timestamp, object_class, confidence, bbox_x, bbox_y, bbox_w, bbox_h 
                    FROM detection_logs 
                    ORDER BY timestamp DESC 
                    LIMIT {limit}
                """
                cursor.execute(query)
                return cursor.fetchall()
            elif self.backend == "sqlite":
                self.connection.row_factory = sqlite3.Row
                cursor = self.connection.cursor()
                query = f"""
                    SELECT log_id, timestamp, object_class, confidence, bbox_x, bbox_y, bbox_w, bbox_h 
                    FROM detection_logs 
                    ORDER BY timestamp DESC 
                    LIMIT {limit}
                """
                cursor.execute(query)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logging.error(f"Failed to retrieve records: {e}")
            return []
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    pass

    def get_class_counts(self):
        """Retrieve count of detections per object class."""
        if not self.is_connected():
            return []
            
        cursor = None
        try:
            if self.backend == "mysql":
                cursor = self.connection.cursor(dictionary=True)
                query = """
                    SELECT object_class, COUNT(*) as count 
                    FROM detection_logs 
                    GROUP BY object_class
                    ORDER BY count DESC
                """
                cursor.execute(query)
                return cursor.fetchall()
            elif self.backend == "sqlite":
                self.connection.row_factory = sqlite3.Row
                cursor = self.connection.cursor()
                query = """
                    SELECT object_class, COUNT(*) as count 
                    FROM detection_logs 
                    GROUP BY object_class
                    ORDER BY count DESC
                """
                cursor.execute(query)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logging.error(f"Failed to retrieve class counts: {e}")
            return []
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    pass

    def get_detections_over_time(self):
        """Retrieve detection counts over time (per minute intervals)."""
        if not self.is_connected():
            return []
            
        cursor = None
        try:
            if self.backend == "mysql":
                cursor = self.connection.cursor(dictionary=True)
                query = """
                    SELECT DATE_FORMAT(timestamp, '%Y-%m-%d %H:%i:00') as time_interval, COUNT(*) as count
                    FROM detection_logs
                    GROUP BY time_interval
                    ORDER BY time_interval ASC
                    LIMIT 100
                """
                cursor.execute(query)
                return cursor.fetchall()
            elif self.backend == "sqlite":
                self.connection.row_factory = sqlite3.Row
                cursor = self.connection.cursor()
                query = """
                    SELECT strftime('%Y-%m-%d %H:%M:00', timestamp) as time_interval, COUNT(*) as count
                    FROM detection_logs
                    GROUP BY time_interval
                    ORDER BY time_interval ASC
                    LIMIT 100
                """
                cursor.execute(query)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logging.error(f"Failed to retrieve detections over time: {e}")
            return []
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    pass
