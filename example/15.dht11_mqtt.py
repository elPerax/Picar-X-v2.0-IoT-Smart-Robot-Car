# ~/picar-x/example/15.dht11_mqtt.py
import sys, time, signal
sys.path.append("/home/pi/picar-x")

from iot.mqtt_helper import AIOPublisher
import board
import adafruit_dht
from iot.logger import log


# DHT11 wired to Robot HAT "Digital 0"  ->  BCM 4  ->  board.D4
DHT_PIN = board.D4
dht = adafruit_dht.DHT11(DHT_PIN, use_pulseio=False)

running = True
def handle_stop(signum=None, frame=None):
    """Allow Ctrl+C to stop the loop cleanly."""
    global running
    running = False

def main():
    signal.signal(signal.SIGINT, handle_stop)
    pub = AIOPublisher()

    print("Starting DHT11 MQTT Publisher (Ctrl+C to stop)")
    interval = 5.0           # send at most once every 5s (safe for Adafruit IO free plan)
    last_send = 0.0
    last_temp = None
    last_hum = None

    try:
        while running:
            # respect rate limit
            now = time.time()
            if now - last_send < interval:
                time.sleep(0.1)
                continue

            try:
                temp_c = dht.temperature     # may raise RuntimeError sometimes
                hum = dht.humidity

                if temp_c is None or hum is None:
                    print("No valid DHT11 reading yet...")
                else:
                    print(f"DHT11 -> Temp: {temp_c:.1f} C | Hum: {hum:.0f}%")

                    # publish only if values changed meaningfully
                    if last_temp is None or abs(temp_c - last_temp) >= 0.5:
                        pub.send("dht11_temp", round(temp_c, 1))
                        last_temp = temp_c
                    if last_hum is None or abs(hum - last_hum) >= 1:
                        pub.send("dht11_humidity", int(round(hum)))
                        last_hum = hum
                        
                    log("dht11", {"temp": round(temp_c, 1), "humidity": int(round(hum))})

                    last_send = now

            except RuntimeError as e:
                # DHT sensors often throw transient errors; just retry
                print("DHT error:", e)
                time.sleep(1.5)

    finally:
        print("Stopped cleanly.")

if __name__ == "__main__":
    main()
