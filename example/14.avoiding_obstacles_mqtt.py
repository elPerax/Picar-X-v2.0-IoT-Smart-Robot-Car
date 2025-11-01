import sys, os, time, signal
sys.path.append("/home/pi/picar-x")

from picarx import Picarx
from iot.mqtt_helper import AIOPublisher
from iot.logger import log


POWER = 50
SafeDistance = 40    # > 40 safe
DangerDistance = 20  # 20..39 turn; <20 back

running = True

def _sigint_handler(signum, frame):
    # just flip the flag; cleanup happens in finally
    global running
    running = False

def hard_stop(px: Picarx):
    try:
        # stop both directions just in case
        px.forward(0)
        px.backward(0)
        # center steering
        px.set_dir_servo_angle(0)
        # some firm delay to ensure PWM updates reach the HAT
        time.sleep(0.05)
        # optional: if SDK has px.stop(), call it
        if hasattr(px, "stop"):
            px.stop()
    except Exception:
        pass

def main():
    global running
    signal.signal(signal.SIGINT, _sigint_handler)  # Ctrl+C
    px = Picarx()
    pub = AIOPublisher()

    try:
        while running:
            distance = round(px.ultrasonic.read(), 2)
            print("distance:", distance)
            pub.send("ultrasonic_distance", distance)
            log("ultrasonic", {"distance": distance})

            if distance >= SafeDistance:
                px.set_dir_servo_angle(0)
                px.forward(POWER)
            elif distance >= DangerDistance:
                px.set_dir_servo_angle(30)
                px.forward(POWER)
                time.sleep(0.1)
            else:
                px.set_dir_servo_angle(-30)
                px.backward(POWER)
                time.sleep(0.5)

            # small tick to keep loop responsive to Ctrl+C
            time.sleep(0.02)

    finally:
        hard_stop(px)
        print("Stopped and centered.")

if __name__ == "__main__":
    main()

