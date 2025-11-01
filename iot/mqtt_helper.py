# ~/picar-x/iot/mqtt_helper.py
import os, time
from dotenv import load_dotenv
from Adafruit_IO import MQTTClient
from pathlib import Path


load_dotenv(Path("/home/pi/picar-x/.env"))

AIO_USERNAME = os.getenv("AIO_USERNAME")
AIO_KEY = os.getenv("AIO_KEY")

class AIOPublisher:
    def __init__(self):
        if not (AIO_USERNAME and AIO_KEY):
            raise RuntimeError("Missing AIO_USERNAME/AIO_KEY in .env")
        self.client = MQTTClient(AIO_USERNAME, AIO_KEY)
        self.client.connect()
        # give broker a moment
        time.sleep(0.5)

    def send(self, feed_key: str, value):
        try:
            self.client.publish(feed_key, str(value))
        except Exception:
            # try quick reconnect once
            try:
                self.client.disconnect()
            except Exception:
                pass
            self.client = MQTTClient(AIO_USERNAME, AIO_KEY)
            self.client.connect()
            time.sleep(0.25)
            self.client.publish(feed_key, str(value))
