# ~/picar-x/iot/logger.py
from pathlib import Path
from datetime import datetime

LOG_DIR = Path("/home/pi/picar-x/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

def log(sensor: str, data: dict):
    """Append one row to today's CSV: logs/YYYY-MM-DD_<sensor>.csv"""
    day = datetime.now().strftime("%Y-%m-%d")
    file = LOG_DIR / f"{day}_{sensor}.csv"
    new = not file.exists()

    with file.open("a", encoding="utf-8") as f:
        if new:
            f.write("timestamp," + ",".join(data.keys()) + "\n")
        row = datetime.now().isoformat(timespec="seconds") + "," + ",".join(str(v) for v in data.values()) + "\n"
        f.write(row)
