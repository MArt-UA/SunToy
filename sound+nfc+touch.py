

import board
import busio
import time
import threading
import RPi.GPIO as GPIO
from digitalio import DigitalInOut
from adafruit_pn532.i2c import PN532_I2C
from pydub import AudioSegment
from pydub.playback import _play_with_simpleaudio


# === GPIO НАСТРОЙКА ===
TOUCH_PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(TOUCH_PIN, GPIO.IN)


# === АУДІО ===
greeting_file = "sounds/introTurnOn.mp3"
kotyhoroshko_intro = "sounds/fairyTale/introKotygoroshko.mp3"
kotyhoroshko_story = "sounds/fairyTale/storyKotygoroshko.mp3"


is_playing = False
player = None
current_audio = None
lock = threading.Lock()


def play_audio(file_path):
    global player, is_playing, current_audio
    with lock:
        if player:
            player.stop()
        current_audio = AudioSegment.from_file(file_path)
        player = _play_with_simpleaudio(current_audio)
        is_playing = True


def toggle_play_stop():
    global player, is_playing, current_audio
    with lock:
        if player:
            if is_playing:
                player.stop()
                is_playing = False
            else:
                player = _play_with_simpleaudio(current_audio)
                is_playing = True


def watch_touch():
    while True:
        if GPIO.input(TOUCH_PIN) == GPIO.HIGH:
            toggle_play_stop()
            time.sleep(0.5)  # Debounce


# === ІНІЦІАЛІЗАЦІЯ NFC ===
i2c = busio.I2C(board.SCL, board.SDA)
pn532 = PN532_I2C(i2c, debug=False)
ic, ver, rev, support = pn532.firmware_version
print(f"Знайдено PN532 з прошивкою: {ver}.{rev}")
pn532.SAM_configuration()


# === ГОЛОВНИЙ СКРИПТ ===
def main():
    print("Іграшка увімкнена!")
    play_audio(greeting_file)


    threading.Thread(target=watch_touch, daemon=True).start()


    print("Очікуємо NFC мітку...")
    last_uid = None


    while True:
        uid = pn532.read_passive_target(timeout=0.5)
        if uid is not None:
            uid_str = uid.hex()
            if uid_str != last_uid:
                print(f"Зчитано мітку UID: 0x{uid_str}")
                last_uid = uid_str
                if uid_str == "80f58339":  # ваш UID мітки
                    print("Розпізнано: Казка про Котигорошка")
                    play_audio(kotyhoroshko_intro)
                    time.sleep(10)
                    play_audio(kotyhoroshko_story)
        time.sleep(0.2)


main()





