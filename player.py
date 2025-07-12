import board
import busio
import time
import threading
import RPi.GPIO as GPIO
from digitalio import DigitalInOut
from adafruit_pn532.i2c import PN532_I2C
import vlc
import os

# === GPIO ===
TOUCH_PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(TOUCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# === ФАЙЛИ ===
greeting_file = "/home/pi/SunToy/SunToy/sounds/introTurnOn.mp3"
kotyhoroshko_intro = "/home/pi/SunToy/SunToy/sounds/fairyTale/storyKotygoroshko.mp3"
kotyhoroshko_story = "/home/pi/SunToy/SunToy/sounds/fairyTale/Kotygoroshko_Full.ogg"

# === СТАНИ ===
story_queued = None
player = None
lock = threading.RLock()

# Функція для відтворення аудіо через VLC
def play_audio(file_path):
    global player
    with lock:
        if not os.path.exists(file_path):
            print(f"[ERROR] ❌ Файл не знайдено: {file_path}")
            return
        if player:
            player.stop()
        player = vlc.MediaPlayer(file_path)
        player.audio_set_volume(100)
        player.play()
        print(f"[🔊] Відтворення: {file_path}")

# Функція для чекання завершення відтворення
def wait_until_done():
    while player and player.is_playing():
        time.sleep(0.1)

# Обробка натискання кнопки
def toggle_pause_resume():
    global story_queued
    with lock:
        print(f"[TOGGLE] queued={story_queued}, playing={player.is_playing() if player else False}")
        if story_queued and (not player or not player.is_playing()):
            file = story_queued
            story_queued = None
            print("▶️ Старт історії")
            play_audio(file)
            return
        if not player:
            return
        if player.is_playing():
            player.pause()
            print("⏸️ Пауза")
        else:
            player.play()
            print("▶️ Відновлення")

# Слухаємо кнопку у окремому потоці
def watch_touch():
    prev = GPIO.input(TOUCH_PIN)
    while True:
        cur = GPIO.input(TOUCH_PIN)
        if prev == GPIO.HIGH and cur == GPIO.LOW:
            print("🔘 Кнопка натиснута")
            toggle_pause_resume()
        prev = cur
        time.sleep(0.05)

# Ініціалізація NFC PN532
i2c = busio.I2C(board.SCL, board.SDA)
pn532 = PN532_I2C(i2c, debug=False)
ic, ver, rev, support = pn532.firmware_version
print(f"🟢 PN532 прошивка: {ver}.{rev}")
pn532.SAM_configuration()

# Головна функція
def main():
    global story_queued
    print("👋 Іграшка увімкнена!")
    play_audio(greeting_file)
    wait_until_done()

    threading.Thread(target=watch_touch, daemon=True).start()

    print("📡 Очікуємо NFC мітку...")
    last_uid = None

    while True:
        uid = pn532.read_passive_target(timeout=0.5)
        if uid:
            uid_str = uid.hex()
            if uid_str != last_uid:
                print(f"📛 Зчитано UID: {uid_str}")
                last_uid = uid_str
                if uid_str == "53c5be5d720001":
                    print("🎙️ Intro Котигорошко")
                    play_audio(kotyhoroshko_intro)
                    wait_until_done()
                    print("⏳ Очікуємо кнопку для старту казки...")
                    story_queued = kotyhoroshko_story
        time.sleep(0.2)

if __name__ == "__main__":
    main()



