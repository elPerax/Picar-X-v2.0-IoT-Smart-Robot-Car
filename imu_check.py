from time import sleep

def get_sensor():
    # 1) Preferred full IMU path
    try:
        from robot_hat.imu import IMU
        s = IMU()
        return "robot_hat.imu.IMU", s, True  # has gyro
    except Exception:
        pass
    # 2) ADXL345 accel-only path
    from robot_hat.modules import ADXL345
    s = ADXL345()
    return "robot_hat.modules.ADXL345", s, False  # accel only

def read_accel(s):
    """Return (ax, ay, az) trying multiple API names."""
    # Common SunFounder shapes
    if hasattr(s, "get_acceleration") and callable(s.get_acceleration):
        return s.get_acceleration()                # tuple
    if hasattr(s, "read") and callable(s.read):
        v = s.read()                               # dict/tuple?
        if isinstance(v, dict):
            return (v.get("x"), v.get("y"), v.get("z"))
        if isinstance(v, (list, tuple)) and len(v) >= 3:
            return (v[0], v[1], v[2])
    # Per-axis getters
    if all(hasattr(s, m) for m in ("get_x", "get_y", "get_z")):
        return (s.get_x(), s.get_y(), s.get_z())
    # Per-axis properties
    if all(hasattr(s, a) for a in ("x", "y", "z")):
        return (getattr(s, "x"), getattr(s, "y"), getattr(s, "z"))
    # Single property with tuple
    if hasattr(s, "acceleration"):
        val = getattr(s, "acceleration")
        if isinstance(val, (list, tuple)) and len(val) >= 3:
            return (val[0], val[1], val[2])
    raise AttributeError("Could not find accel accessors on ADXL345; attrs: " + ", ".join(dir(s)))

def main():
    path, sensor, has_gyro = get_sensor()
    print(f"[OK] Using IMU via: {path}  (gyro: {'yes' if has_gyro else 'no'})")
    for _ in range(10):
        ax, ay, az = read_accel(sensor)
        if has_gyro:
            try:
                gx, gy, gz = sensor.gyro
            except Exception:
                gx, gy, gz = (0.0, 0.0, 0.0)
        else:
            gx, gy, gz = (0.0, 0.0, 0.0)
        print(f"accel: {(ax, ay, az)}  gyro: {(gx, gy, gz)}")
        sleep(0.5)

if __name__ == "__main__":
    main()
