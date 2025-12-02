# ~/picar-x/iot/obstacle_avoidance_mqtt.py
from Adafruit_IO import MQTTClient
from picarx import Picarx
import time
import os
from dotenv import load_dotenv
from db_local import insert_sensor_reading


load_dotenv("/home/pi/picar-x/.env")

AIO_USERNAME = os.getenv("AIO_USERNAME")
AIO_KEY = os.getenv("AIO_KEY")

FEED = "obstacle-command"

px = Picarx()
running = False

def on_message(client, feed_id, payload):
    global running
    print("Received:", payload)

    if payload == "start":
        running = True
        print("Obstacle avoidance started")
    elif payload == "stop":
        running = False
        px.stop()
        print("Obstacle avoidance stopped")

def loop():
    while True:
        if running:
            dist = px.ultrasonic.read()
            insert_sensor_reading("ultrasonic_distance", dist)

            if dist < 25:
                px.backward(40)
                time.sleep(0.5)
                px.turn_right(40)
                time.sleep(0.5)
            else:
                px.forward(30)

        time.sleep(0.1)

client = MQTTClient(AIO_USERNAME, AIO_KEY)
client.on_message = on_message
client.connect()
client.subscribe(FEED)

print("Listening to obstacle-command feed...")
client.loop_background()

loop()
