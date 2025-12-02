# ~/picar-x/iot/subscriber.py
"""
Unified MQTT subscriber for PiCar-X.

Subscribes to Adafruit IO feeds:
  - picarx-command: forward, backward, stop (motors only)
  - steering-command: left, right, center (direction servo only)
  - camera-command: pan_left, pan_right, pan_center, tilt_up, tilt_down, tilt_center
  - line-command: start, stop
  - obstacle-command: start, stop

Run on the Pi:
    cd ~/picar-x
    python3 iot/subscriber.py
"""

import os
import time
import threading
from pathlib import Path

from dotenv import load_dotenv
from Adafruit_IO import MQTTClient
from picarx import Picarx

# Import your existing database helpers
import sys
sys.path.append("/home/pi/picar-x")
from iot.mqtt_helper import AIOPublisher
from iot.logger import log
from robot_hat import TTS

# -------------------------------------------------
# Load credentials
# -------------------------------------------------
ENV_PATH = Path("/home/pi/picar-x/.env")
load_dotenv(ENV_PATH)

AIO_USERNAME = os.getenv("AIO_USERNAME")
AIO_KEY = os.getenv("AIO_KEY")

# Feeds
AIO_COMMAND_FEED = os.getenv("AIO_COMMAND_FEED", "picarx-command")
AIO_STEERING_FEED = os.getenv("AIO_STEERING_FEED", "steering-command")
AIO_CAMERA_FEED = os.getenv("AIO_CAMERA_FEED", "camera-command")
AIO_TTS_FEED = os.getenv("AIO_TTS_FEED", "tts")
AIO_LINE_FEED = os.getenv("AIO_LINE_FEED", "line-command")
AIO_OBS_FEED = os.getenv("AIO_OBS_FEED", "obstacle-command")

if not (AIO_USERNAME and AIO_KEY):
    raise RuntimeError("AIO_USERNAME or AIO_KEY is missing in .env")

# -------------------------------------------------
# PiCar-X setup
# -------------------------------------------------
px = Picarx()
pub = AIOPublisher()


# Control settings
MOTOR_POWER = 20
STEERING_ANGLE = 30

# Camera settings
current_pan_angle = 0
current_tilt_angle = 0
CAMERA_STEP = 15  # degrees per command

# Line tracking settings
LINE_POWER = 10
LINE_OFFSET = 20

# Obstacle avoidance settings
OBS_POWER = 50
SAFE_DISTANCE = 40
DANGER_DISTANCE = 20

# Publishing settings
SEND_INTERVAL = 2.0
CHANGE_DELTA = 50

# -------------------------------------------------
# State for background modes
# -------------------------------------------------
line_active = False
line_thread = None

obs_active = False
obs_thread = None

state_lock = threading.Lock()


# -------------------------------------------------
# Motor control (forward/backward/stop)
# -------------------------------------------------
def do_forward():
    print("[MOTOR] forward")
    px.forward(MOTOR_POWER)


def do_backward():
    print("[MOTOR] backward")
    px.backward(MOTOR_POWER)


def do_stop():
    print("[MOTOR] stop")
    px.stop()


MOTOR_COMMANDS = {
    "forward": do_forward,
    "backward": do_backward,
    "stop": do_stop,
}


# -------------------------------------------------
# Steering control (direction servo)
# -------------------------------------------------
def do_steer_left():
    print(f"[STEERING] left ({-STEERING_ANGLE}°)")
    px.set_dir_servo_angle(-STEERING_ANGLE)


def do_steer_right():
    print(f"[STEERING] right ({STEERING_ANGLE}°)")
    px.set_dir_servo_angle(STEERING_ANGLE)


def do_steer_center():
    print("[STEERING] center")
    px.set_dir_servo_angle(0)


STEERING_COMMANDS = {
    "left": do_steer_left,
    "right": do_steer_right,
    "center": do_steer_center,
}


# -------------------------------------------------
# Camera control helpers
# -------------------------------------------------
def do_pan_left():
    global current_pan_angle
    current_pan_angle -= CAMERA_STEP
    if current_pan_angle < -30:
        current_pan_angle = -30
    print(f"[CAMERA] Pan left to {current_pan_angle}°")
    px.set_cam_pan_angle(current_pan_angle)


def do_pan_right():
    global current_pan_angle
    current_pan_angle += CAMERA_STEP
    if current_pan_angle > 30:
        current_pan_angle = 30
    print(f"[CAMERA] Pan right to {current_pan_angle}°")
    px.set_cam_pan_angle(current_pan_angle)


def do_pan_center():
    global current_pan_angle
    current_pan_angle = 0
    print("[CAMERA] Pan center")
    px.set_cam_pan_angle(0)


def do_tilt_up():
    global current_tilt_angle
    current_tilt_angle -= CAMERA_STEP
    if current_tilt_angle < -30:
        current_tilt_angle = -30
    print(f"[CAMERA] Tilt up to {current_tilt_angle}°")
    px.set_cam_tilt_angle(current_tilt_angle)


def do_tilt_down():
    global current_tilt_angle
    current_tilt_angle += CAMERA_STEP
    if current_tilt_angle > 30:
        current_tilt_angle = 30
    print(f"[CAMERA] Tilt down to {current_tilt_angle}°")
    px.set_cam_tilt_angle(current_tilt_angle)


def do_tilt_center():
    global current_tilt_angle
    current_tilt_angle = 0
    print("[CAMERA] Tilt center")
    px.set_cam_tilt_angle(0)


CAMERA_COMMANDS = {
    "pan_left": do_pan_left,
    "pan_right": do_pan_right,
    "pan_center": do_pan_center,
    "tilt_up": do_tilt_up,
    "tilt_down": do_tilt_down,
    "tilt_center": do_tilt_center,
}


# -------------------------------------------------
# TTS (Text-to-Speech) control
# -------------------------------------------------
def do_speak(text):
    """Speak the given text via TTS."""
    print(f"[TTS] Speaking: {text}")
    try:
        # create a fresh TTS object each time
        local_tts = TTS(lang="en-US")
        local_tts.say(text)

        # Log to database
        log("tts", {"text": text})
        print("[TTS] Done speaking")
    except Exception as e:
        print(f"[TTS] Error: {e}")


# -------------------------------------------------
# Line-tracking mode
# -------------------------------------------------
def get_line_status(val_list):
    _state = px.get_line_status(val_list)
    if _state == [0, 0, 0]:
        return 'stop'
    elif _state[1] == 1:
        return 'forward'
    elif _state[0] == 1:
        return 'right'
    elif _state[2] == 1:
        return 'left'
    return 'stop'


def line_tracking_loop():
    global line_active
    print("[LINE] loop started")
    
    last_state = "stop"
    last_sent_state = None
    last_send_ts = 0.0
    last_vals = (None, None, None)
    
    try:
        while True:
            with state_lock:
                if not line_active:
                    break

            try:
                gm = px.get_grayscale_data()
                state = get_line_status(gm)
                print(f"[LINE] gm: {gm}, state: {state}")
            except Exception as e:
                print("[LINE] error reading grayscale:", e)
                time.sleep(0.1)
                continue

            if state != "stop":
                last_state = state

            if state == 'forward':
                px.set_dir_servo_angle(0)
                px.forward(LINE_POWER)
            elif state == 'left':
                px.set_dir_servo_angle(LINE_OFFSET)
                px.forward(LINE_POWER)
            elif state == 'right':
                px.set_dir_servo_angle(-LINE_OFFSET)
                px.forward(LINE_POWER)
            else:
                print(f"[LINE] outHandle - last_state: {last_state}")
                if last_state == 'left':
                    px.set_dir_servo_angle(-30)
                    px.backward(10)
                elif last_state == 'right':
                    px.set_dir_servo_angle(30)
                    px.backward(10)

                recovery_attempts = 0
                while line_active and recovery_attempts < 100:
                    gm2 = px.get_grayscale_data()
                    st2 = get_line_status(gm2)
                    if st2 != last_state:
                        print("[LINE] Line found!")
                        break
                    time.sleep(0.001)
                    recovery_attempts += 1
                
                if recovery_attempts >= 100:
                    print("[LINE] Could not recover line")
                    break

            # Publish to Adafruit IO
            now = time.time()
            if now - last_send_ts >= SEND_INTERVAL:
                changed = (
                    last_vals[0] is None or
                    abs(gm[0]-last_vals[0]) >= CHANGE_DELTA or
                    abs(gm[1]-last_vals[1]) >= CHANGE_DELTA or
                    abs(gm[2]-last_vals[2]) >= CHANGE_DELTA
                )
                if changed:
                    try:
                        pub.send("grayscale-left",  int(gm[0]))
                        pub.send("grayscale-mid",   int(gm[1]))
                        pub.send("grayscale-right", int(gm[2]))
                        log("grayscale", {"left": int(gm[0]), "mid": int(gm[1]), "right": int(gm[2])})
                        last_vals = (gm[0], gm[1], gm[2])
                    except Exception as e:
                        print("[LINE] Publish error:", e)

                if state != last_sent_state:
                    try:
                        pub.send("line-state", state)
                        log("grayscale_state", {"state": state})
                        last_sent_state = state
                    except Exception as e:
                        print("[LINE] Publish state error:", e)

                last_send_ts = now

            time.sleep(0.02)

    finally:
        print("[LINE] loop stopping")
        px.stop()
        px.set_dir_servo_angle(0)


def start_line_tracking():
    global line_active, line_thread
    with state_lock:
        if line_active:
            print("[LINE] already active")
            return
        print("[LINE] starting")
        line_active = True
        _stop_obstacle_no_lock()
        line_thread = threading.Thread(target=line_tracking_loop, daemon=True)
        line_thread.start()


def _stop_line_no_lock():
    global line_active
    if line_active:
        print("[LINE] stopping")
        line_active = False


def stop_line_tracking():
    with state_lock:
        _stop_line_no_lock()


# -------------------------------------------------
# Obstacle-avoidance mode
# -------------------------------------------------
def obstacle_loop():
    global obs_active
    print("[OBS] loop started")
    
    last_send_ts = 0.0
    
    try:
        while True:
            with state_lock:
                if not obs_active:
                    break

            try:
                distance = round(px.ultrasonic.read(), 2)
                print(f"[OBS] distance: {distance} cm")
            except Exception as e:
                print("[OBS] error reading distance:", e)
                time.sleep(0.1)
                continue

            if distance >= SAFE_DISTANCE:
                px.set_dir_servo_angle(0)
                px.forward(OBS_POWER)
            elif distance >= DANGER_DISTANCE:
                px.set_dir_servo_angle(30)
                px.forward(OBS_POWER)
                time.sleep(0.1)
            else:
                print(f"[OBS] Too close ({distance} cm)")
                px.set_dir_servo_angle(-30)
                px.backward(OBS_POWER)
                time.sleep(0.5)

            # Publish to Adafruit IO
            now = time.time()
            if now - last_send_ts >= SEND_INTERVAL:
                try:
                    pub.send("ultrasonic-distance", distance)
                    log("ultrasonic", {"distance": distance})
                except Exception as e:
                    print("[OBS] Publish error:", e)
                last_send_ts = now

            time.sleep(0.02)

    finally:
        print("[OBS] loop stopping")
        px.stop()
        px.set_dir_servo_angle(0)


def start_obstacle():
    global obs_active, obs_thread
    with state_lock:
        if obs_active:
            print("[OBS] already active")
            return
        print("[OBS] starting")
        obs_active = True
        _stop_line_no_lock()
        obs_thread = threading.Thread(target=obstacle_loop, daemon=True)
        obs_thread.start()


def _stop_obstacle_no_lock():
    global obs_active
    if obs_active:
        print("[OBS] stopping")
        obs_active = False


def stop_obstacle():
    with state_lock:
        _stop_obstacle_no_lock()


# -------------------------------------------------
# MQTT callbacks
# -------------------------------------------------
def connected(client):
    print(f"[MQTT] Connected as {AIO_USERNAME}")
    print(f"[MQTT] Subscribing to:")
    print(f"  - {AIO_COMMAND_FEED}")
    print(f"  - {AIO_STEERING_FEED}")
    print(f"  - {AIO_CAMERA_FEED}")
    print(f"  - {AIO_TTS_FEED}")
    print(f"  - {AIO_LINE_FEED}")
    print(f"  - {AIO_OBS_FEED}")
    client.subscribe(AIO_COMMAND_FEED)
    client.subscribe(AIO_STEERING_FEED)
    client.subscribe(AIO_CAMERA_FEED)
    client.subscribe(AIO_TTS_FEED)
    client.subscribe(AIO_LINE_FEED)
    client.subscribe(AIO_OBS_FEED)


def disconnected(client):
    print("[MQTT] Disconnected!")
    raise SystemExit(1)


def message(client, feed_id, payload):
    cmd = str(payload).strip().lower()
    print(f"[MQTT] '{feed_id}': {cmd}")

    # Motor control (forward/backward/stop)
    if feed_id == AIO_COMMAND_FEED:
        stop_line_tracking()
        stop_obstacle()
        handler = MOTOR_COMMANDS.get(cmd)
        if handler:
            handler()
        else:
            print(f"[WARN] unknown motor command: {cmd}")

    # Steering control (left/right/center)
    elif feed_id == AIO_STEERING_FEED:
        handler = STEERING_COMMANDS.get(cmd)
        if handler:
            handler()
        else:
            print(f"[WARN] unknown steering command: {cmd}")

    # Camera control
    elif feed_id == AIO_CAMERA_FEED:
        handler = CAMERA_COMMANDS.get(cmd)
        if handler:
            handler()
        else:
            print(f"[WARN] unknown camera command: {cmd}")

    # TTS control (receives text to speak)
    elif feed_id == AIO_TTS_FEED:
        # The payload is the text to speak
        text = str(payload).strip()
        if text:
            do_speak(text)
        else:
            print("[WARN] empty TTS text")

    # Line tracking
    elif feed_id == AIO_LINE_FEED:
        if cmd == "start":
            start_line_tracking()
        elif cmd == "stop":
            stop_line_tracking()

    # Obstacle avoidance
    elif feed_id == AIO_OBS_FEED:
        if cmd == "start":
            start_obstacle()
        elif cmd == "stop":
            stop_obstacle()


# -------------------------------------------------
# Main
# -------------------------------------------------
def main():
    # Center everything on startup
    px.set_dir_servo_angle(0)
    px.set_cam_pan_angle(0)
    px.set_cam_tilt_angle(0)
    
    client = MQTTClient(AIO_USERNAME, AIO_KEY)
    client.on_connect = connected
    client.on_disconnect = disconnected
    client.on_message = message

    print("[MQTT] Connecting to Adafruit IO...")
    client.connect()

    try:
        client.loop_blocking()
    except KeyboardInterrupt:
        print("\n[MAIN] Ctrl+C detected")
    finally:
        print("[MAIN] Cleaning up")
        stop_line_tracking()
        stop_obstacle()
        px.stop()
        px.set_dir_servo_angle(0)
        px.set_cam_pan_angle(0)
        px.set_cam_tilt_angle(0)
        time.sleep(0.1)


if __name__ == "__main__":
    main()
