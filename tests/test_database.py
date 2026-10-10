import pytest
import os
from database import DatabaseManager

@pytest.fixture
def db():
    return DatabaseManager()

def test_db_initialization(db):
    assert db.host is not None
    assert db.database == "vision_platform"
    
def test_db_connection_fail_gracefully(db):
    # Intentionally bad port to test failure handling without fallback
    db.port = 99999 
    status = db.connect()
    
    assert status == False
    assert db.is_connected() == False
    
def test_log_detection_no_connection(db):
    # Ensure logging doesn't crash when not connected
    db.connection = None
    result = db.log_detection("person", 0.95, 10, 10, 100, 100)
    assert result == False

def test_sqlite_fallback_operations(tmp_path):
    test_db_path = str(tmp_path / "test_detection.db")
    db = DatabaseManager(use_sqlite_fallback=True, sqlite_path=test_db_path)
    db.port = 99999  # Force MySQL failure
    status = db.connect()
    
    assert status == True
    assert db.is_connected() == True
    assert db.get_backend() == "sqlite"
    
    # Test logging
    logged = db.log_detection("car", 0.92, 10, 20, 100, 50)
    assert logged == True
    
    # Test recent logs
    logs = db.get_recent_logs(limit=10)
    assert len(logs) == 1
    assert logs[0]["object_class"] == "car"
    
    # Test class counts
    counts = db.get_class_counts()
    assert len(counts) == 1
    assert counts[0]["object_class"] == "car"
    assert counts[0]["count"] == 1
    
    # Test detections over time
    timeline = db.get_detections_over_time()
    assert len(timeline) >= 1
    
    db.close()
    assert db.is_connected() == False
