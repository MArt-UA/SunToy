# main.py
#!/usr/bin/env python3
import board, busio, time, threading, subprocess, vlc, RPi.GPIO as GPIO
from adafruit_pn532.i2c import PN532_I2C
import player, recorder

# === GPIO PINS ===
PLAY_PIN     = 17   # Touch1: play/pause
REC_PIN      = 27   # Touch2: record
VOLUME_PIN   = 22   # Touch3: volume

LED_NFC1     = 13   # fades when paused
LED_NFC2     = 19   # lights on REC-tag
LED_PLAY     = 16   # blinks during playback
LED_REC      = 26   # lights when in record-mode

PLAYER_TAG   = "53c5be5d720001"
RECORDER_TAG = "53c4be5d720001"

# === GLOBAL STATE & VOLUME ===
current_mode = None
volume = 1.0  # 0.0–1.0
VOLUME_DOWN_STEP = 0.1
VOLUME_UP_STEP   = 0.05
HOLD_INTERVAL    = 0.5

# GPIO setup
GPIO.setmode(GPIO.BCM)
for pin in (PLAY_PIN, REC_PIN, VOLUME_PIN):
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
for led in (LED_NFC1, LED_NFC2, LED_PLAY, LED_REC):
    GPIO.setup(led, GPIO.OUT)
    GPIO.output(led, False)

# Button callbacks
def on_play(channel):
    if current_mode == "player":
        player.toggle_pause_resume()
    elif current_mode == "recorder":
        recorder.play_button_pressed()

def on_rec(channel):
    if current_mode == "recorder":
        recorder.rec_button_pressed()

GPIO.add_event_detect(PLAY_PIN, GPIO.FALLING, callback=on_play, bouncetime=200)
GPIO.add_event_detect(REC_PIN,  GPIO.FALLING, callback=on_rec,  bouncetime=200)

# Volume thread
def watch_volume():
    global volume
    pressed = False
    last_time = 0
    while True:
        if GPIO.input(VOLUME_PIN) == GPIO.LOW:
            now = time.time()
            if not pressed:
                pressed = True
                volume = max(0.0, volume - VOLUME_DOWN_STEP)
                player.set_volume(int(volume*100))
                print(f"[VOL] {int(volume*100)}%")
                last_time = now
            elif now - last_time >= HOLD_INTERVAL:
                volume = min(1.0, volume + VOLUME_UP_STEP)
                player.set_volume(int(volume*100))
                print(f"[VOL] {int(volume*100)}%")
                last_time = now
        else:
            pressed = False
        time.sleep(0.05)

threading.Thread(target=watch_volume, daemon=True).start()

# Boost USB speaker
USB_CARD, USB_CTRL = 2, "Speaker"
def boost_usb_volume():
    subprocess.run(["amixer","-c",str(USB_CARD),"sset",USB_CTRL,"100%","unmute"],
                   stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def boot():
    print("[main] ▶️ Booting…")
    boost_usb_volume()
    intro = "/home/pi/SunToy/SunToy/sounds/introTurnOn.mp3"
    p = vlc.MediaPlayer(intro)
    p.audio_set_volume(100)
    p.play()
    time.sleep(3)

# PN532 init with retry
i2c = busio.I2C(board.SCL, board.SDA)
while True:
    try:
        pn532 = PN532_I2C(i2c, debug=False)
        ic, ver, rev, support = pn532.firmware_version
        print(f"[main] ✅ PN532 fw {ver}.{rev}")
        pn532.SAM_configuration()
        break
    except Exception as e:
        print(f"[main] ⚠️ PN532 init failed: {e}, retry in 2s")
        time.sleep(2)

# NFC watch thread
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
                # clear previous LEDs/modes
                GPIO.output(LED_PLAY, False)
                GPIO.output(LED_NFC2, False)
                player.stop()
                recorder.stop()

                if u == PLAYER_TAG:
                    current_mode = "player"
                    GPIO.output(LED_NFC1, True)
                    player.start()
                    player.play_story(led_pin=LED_PLAY)
                elif u == RECORDER_TAG:
                    current_mode = "recorder"
                    GPIO.output(LED_NFC2, True)
                    recorder.start(led_rec=LED_REC)
        time.sleep(0.1)

def main():
    boot()
    threading.Thread(target=watch_nfc, daemon=True).start()
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
