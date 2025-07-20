#!/usr/bin/env python3
import board, busio, time, threading, subprocess, vlc, RPi.GPIO as GPIO
from adafruit_pn532.i2c import PN532_I2C

import player, recorder

# === GPIO PINS ===
PLAY_PIN     = 17
REC_PIN      = 27
VOLUME_PIN   = 22

# === NFC TAGS ===
PLAYER_TAG   = "53c5be5d720001"
RECORDER_TAG = "53c4be5d720001"

# === GLOBAL STATE ===
current_mode = None

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(PLAY_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(REC_PIN,  GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(VOLUME_PIN,  GPIO.IN, pull_up_down=GPIO.PUD_UP)

def on_play_pressed(channel):
    print(f"[main] ▶️ PLAY pressed, mode={current_mode}")
    if current_mode == "player":
        player.toggle_pause_resume()
    elif current_mode == "recorder":
        recorder.play_button_pressed()
    else:
        print("[main] ▶️ PLAY ignored, no mode")

def on_rec_pressed(channel):
    print(f"[main] 🔘 REC pressed, mode={current_mode}")
    if current_mode == "recorder":
        recorder.rec_button_pressed()
    else:
        print("[main] 🔘 REC ignored, not in recorder mode")

def on_volume_pressed(channel):
    print(f"[main] 🔊 VOLUME pressed (mode={current_mode})")
    player.change_volume()
    recorder.change_volume()

# bind events
GPIO.add_event_detect(PLAY_PIN, GPIO.FALLING,
                      callback=on_play_pressed, bouncetime=200)
GPIO.add_event_detect(REC_PIN,  GPIO.FALLING,
                      callback=on_rec_pressed,  bouncetime=200)
GPIO.add_event_detect(VOLUME_PIN, GPIO.FALLING,
                      callback=on_volume_pressed, bouncetime=200)

# boost USB volume on boot
USB_CARD    = 2
USB_CONTROL = 'Speaker'
def boost_usb_volume():
    subprocess.run(
        ['amixer', '-c', str(USB_CARD),
         'sset', USB_CONTROL, '80%', 'unmute'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def boot():
    print("[main] ▶️ Boot: boosting USB volume")
    boost_usb_volume()
    intro = "/home/pi/SunToy/SunToy/sounds/introTurnOn.mp3"
    p = vlc.MediaPlayer(intro)
    p.audio_set_volume(80)
    p.play()
    time.sleep(3)

# NFC init
i2c   = busio.I2C(board.SCL, board.SDA)
pn532 = PN532_I2C(i2c, debug=False)
ic, ver, rev, support = pn532.firmware_version
print(f"[main] PN532 fw {ver}.{rev}")
pn532.SAM_configuration()

def watch_nfc():
    global current_mode
    last = None
    print("[main] 📡 NFC watch started")
    while True:
        uid = pn532.read_passive_target(timeout=0.5)
        if uid:
            u = uid.hex()
            if u != last:
                print(f"[main] 📛 Tag: {u}")
                last = u
                # вимикаємо попередній режим
                if current_mode == "player":
                    player.stop()
                elif current_mode == "recorder":
                    recorder.stop()

                if u == PLAYER_TAG:
                    current_mode = "player"
                    player.start()
                    player.play_story()

                elif u == RECORDER_TAG:
                    current_mode = "recorder"
                    recorder.start()
        time.sleep(0.1)

def main():
    boot()
    threading.Thread(target=watch_nfc, daemon=True).start()
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
