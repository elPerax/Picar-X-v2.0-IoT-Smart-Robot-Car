# ~/picar-x/iot/logger.py
import time
from pathlib import Path
from datetime import datetime

# Import database functions
import sys
sys.path.append("/home/pi/picar-x")
from iot.db_local import insert_sensor_batch, init_db

LOG_DIR = Path("/home/pi/picar-x/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Initialize database on import
init_db()

def log(sensor: str, data: dict):
    """
    Log sensor data to BOTH:
    1. CSV file: logs/YYYY-MM-DD_<sensor>.csv
    2. SQLite database: logs/picarx_data.db
    
    Example:
        log("ultrasonic", {"distance": 45.2})
        log("grayscale", {"left": 120, "mid": 90, "right": 85})
    """
    # 1. Log to CSV (original behavior)
    day = datetime.now().strftime("%Y-%m-%d")
    file = LOG_DIR / f"{day}_{sensor}.csv"
    new = not file.exists()
    
    with file.open("a", encoding="utf-8") as f:
        if new:
            f.write("timestamp," + ",".join(data.keys()) + "\n")
        row = datetime.now().isoformat(timespec="seconds") + "," + ",".join(str(v) for v in data.values()) + "\n"
        f.write(row)
    
    # 2. Log to SQLite database (NEW!)
    try:
        # Build sensor_dict for database
        sensor_dict = {"timestamp": time.time()}
        
        # Convert data keys to match database format
        # e.g., {"distance": 45.2} -> {"ultrasonic_distance": 45.2}
        for key, value in data.items():
            # Create sensor name like "ultrasonic_distance" or "grayscale_left"
            db_key = f"{sensor}_{key}"
            sensor_dict[db_key] = value
        
        # Insert to database
        insert_sensor_batch(sensor_dict)
    except Exception as e:
        # Don't crash if database fails, just print error
        print(f"[LOGGER] Database error: {e}")
