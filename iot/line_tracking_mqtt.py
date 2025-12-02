# ~/picar-x/iot/line_tracking_mqtt.py
from Adafruit_IO import MQTTClient
from picarx import Picarx
import time
import os
from dotenv import load_dotenv
from db_local import insert_sensor_reading


load_dotenv("/home/pi/picar-x/.env")

AIO_USERNAME = os.getenv("AIO_USERNAME")
AIO_KEY = os.getenv("AIO_KEY")

FEED = "line-command"

px = Picarx()
running = False

def on_message(client, feed_id, payload):
    global running
    print("Received:", payload)

    if payload == "start":
        running = True
        print("Line tracking started")
    elif payload == "stop":
        running = False
        px.stop()
        print("Line tracking stopped")

def loop():
    while True:
        if running:
            left, mid, right = px.get_grayscale()

            insert_sensor_reading("grayscale_left", left)
            insert_sensor_reading("grayscale_mid", mid)
            insert_sensor_reading("grayscale_right", right)

            if mid < 500:
                px.forward(30)
            elif left < 500:
                px.turn_left(30)
            elif right < 500:
                px.turn_right(30)

        time.sleep(0.1)


client = MQTTClient(AIO_USERNAME, AIO_KEY)
client.on_message = on_message

client.connect()
client.subscribe(FEED)

print("Listening to line-command feed...")
client.loop_background()

loop()
