# ~/picar-x/example/16.line_follow_mqtt.py
import sys, time, signal
sys.path.append("/home/pi/picar-x")

from picarx import Picarx
from iot.mqtt_helper import AIOPublisher
from iot.logger import log


px = Picarx()
# If you ever move the sensor, you can force pins like:
# px = Picarx(grayscale_pins=['A0', 'A1', 'A2'])

# Optional: if you didn't calibrate with the tool, you can set refs here.
# px.set_line_reference([1400, 1400, 1400])

px_power = 10
offset = 20
running = True

def handle_stop(*_):
    global running
    running = False

def get_status(val_list):
    # returns one of: 'stop', 'forward', 'left', 'right'
    _state = px.get_line_status(val_list)   # [0/1, 0/1, 0/1], 0=line, 1=background
    if _state == [0, 0, 0]:
        return 'stop'
    elif _state[1] == 1:
        return 'forward'
    elif _state[0] == 1:
        return 'right'
    elif _state[2] == 1:
        return 'left'
    return 'stop'

def main():
    signal.signal(signal.SIGINT, handle_stop)
    pub = AIOPublisher()

    last_state = "stop"
    last_sent_state = None
    last_send_ts = 0.0
    last_vals = (None, None, None)

    SEND_INTERVAL = 2.0      # seconds between publishes (safe for free plan)
    CHANGE_DELTA  = 50       # only push grayscale if it changed a fair amount

    try:
        while running:
            gm = px.get_grayscale_data()           # [left, middle, right] raw values
            state = get_status(gm)
            print(f"gm_val_list: {gm}, {state}")

            # ---- driving logic (same behavior as your original) ----
            if state != "stop":
                last_state = state

            if state == 'forward':
                px.set_dir_servo_angle(0)
                px.forward(px_power)
            elif state == 'left':
                px.set_dir_servo_angle(offset)
                px.forward(px_power)
            elif state == 'right':
                px.set_dir_servo_angle(-offset)
                px.forward(px_power)
            else:
                # outHandle behavior
                if last_state == 'left':
                    px.set_dir_servo_angle(-30); px.backward(10)
                elif last_state == 'right':
                    px.set_dir_servo_angle(30); px.backward(10)

                # wait until state changes
                while running:
                    gm2 = px.get_grayscale_data()
                    st2 = get_status(gm2)
                    print(f"outHandle gm_val_list: {gm2}, {st2}")
                    if st2 != last_state:
                        break
                    time.sleep(0.001)

            # ---- publish to Adafruit IO (rate-limited) ----
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
                        pub.send("grayscale_left",  int(gm[0]))
                        pub.send("grayscale_mid",   int(gm[1]))
                        pub.send("grayscale_right", int(gm[2]))
                        log("grayscale", {"left": int(gm[0]), "mid": int(gm[1]), "right": int(gm[2])})
                        last_vals = (gm[0], gm[1], gm[2])
                    except Exception as e:
                        print("Publish grayscale error:", e)

                if state != last_sent_state:
                    try:
                        pub.send("line_state", state)  # 'forward' | 'left' | 'right' | 'stop'
                        log("grayscale_state", {"state": state})
                        last_sent_state = state
                    except Exception as e:
                        print("Publish state error:", e)

                last_send_ts = now

            time.sleep(0.02)  # keeps loop responsive

    finally:
        try:
            px.stop()
            px.set_dir_servo_angle(0)
        except Exception:
            pass
        print("stop and exit")

if __name__ == "__main__":
    main()
