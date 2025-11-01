# ~/picar-x/example/17.imu_mqtt.py
import sys, time, math, signal, json
sys.path.append("/home/pi/picar-x")

from iot.mqtt_helper import AIOPublisher
import board, adafruit_mpu6050

i2c = board.I2C()
mpu = adafruit_mpu6050.MPU6050(i2c)

running = True
def stop_handler(*_): 
    global running; running = False

def main():
    signal.signal(signal.SIGINT, stop_handler)
    pub = AIOPublisher()

    SEND_INTERVAL = 2.0
    ACC_DELTA = 0.20
    GYRO_DELTA = 2.0
    last_send = 0.0
    last_payload = None

    print("IMU publisher started (Ctrl+C to stop).")
    try:
        while running:
            acc = mpu.acceleration
            gyro_rad = mpu.gyro
            gyro = tuple(g * (180.0 / math.pi) for g in gyro_rad)

            print(f"Accel: {tuple(round(v,2) for v in acc)}  Gyro: {tuple(round(v,1) for v in gyro)}")

            now = time.time()
            if now - last_send >= SEND_INTERVAL:
                payload = {
                    "ax": round(acc[0],3), "ay": round(acc[1],3), "az": round(acc[2],3),
                    "gx": round(gyro[0],2), "gy": round(gyro[1],2), "gz": round(gyro[2],2)
                }

                changed = (
                    last_payload is None or
                    any(abs(payload[k] - last_payload[k]) >= ACC_DELTA for k in ("ax","ay","az")) or
                    any(abs(payload[k] - last_payload[k]) >= GYRO_DELTA for k in ("gx","gy","gz"))
                )
                if changed:
                    pub.send("imu", json.dumps(payload))
                    last_payload = payload
                    last_send = now

            time.sleep(0.05)
    finally:
        print("IMU publisher stopped.")

if __name__ == "__main__":
    main()
