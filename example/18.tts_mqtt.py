# ~/picar-x/example/18.tts_mqtt.py
import sys
from os import geteuid
from pathlib import Path
sys.path.append("/home/pi/picar-x")

from robot_hat import Music, TTS
from iot.mqtt_helper import AIOPublisher
import readchar
from iot.logger import log


ROOT  = Path(__file__).resolve().parents[1]  # /home/pi/picar-x
HORN  = ROOT / "sounds" / "car-double-horn.wav"
BGM   = ROOT / "musics" / "slow-trail-Ahjay_Stelino.mp3"

HELP = "space: horn   c: horn(thread)   q: music on/off   t: type & speak   Ctrl+C: exit"

def main():
    if geteuid() != 0:
        print("\033[0;33mRun with sudo for audio.\033[0m")

    music = Music(); music.music_set_volume(20)
    tts = TTS(); tts.lang("en-US")
    pub = AIOPublisher()
    bgm = False
    print(HELP)

    try:
        while True:
            k = readchar.readkey().lower()

            if k == "q":
                bgm = not bgm
                if bgm and BGM.exists():
                    music.music_play(str(BGM))
                else:
                    music.music_stop()

            elif k == readchar.key.SPACE:
                if HORN.exists():
                    music.sound_play(str(HORN))
                else:
                    print(f"Missing horn file: {HORN}")

            elif k == "c":
                if HORN.exists():
                    music.sound_play_threading(str(HORN))
                else:
                    print(f"Missing horn file: {HORN}")

            elif k == "t":
                print("\nType text and press Enter (empty = cancel):")
                try:
                    text = input("> ").strip()
                except EOFError:
                    text = ""
                if text:
                    print(f"TTS: {text}")
                    tts.say(text)
                    try:
                        pub.send("tts", text)
                    except Exception as e:
                        print("Publish error:", e)
                    log("tts", {"text": text})
                print("\n" + HELP)

    except KeyboardInterrupt:
        pass
    finally:
        try: music.music_stop()
        except: pass
        print("Bye.")

if __name__ == "__main__":
    main()
