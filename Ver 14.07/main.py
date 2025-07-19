from recorder import Recorder
from player   import Player
import RPi.GPIO as GPIO
from adafruit_pn532.i2c import PN532_I2C
import board, busio, time, threading

# Ініціалізація
player   = Player(play_pin=17, vlc_instance=...)
recorder = Recorder(rec_pin=27, max_duration=180, output_dir="records/")
# CNTL NFC PN532…
# Запуск обробника кнопок для play/pause і rec
threading.Thread(target=player.watch_button, daemon=True).start()
threading.Thread(target=recorder.watch_button, daemon=True).start()

while True:
    uid = read_nfc()
    if uid == PLAY_TAG:
        player.prepare_for_playback()
    elif uid == REC_TAG:
        recorder.prepare_for_recording()
    time.sleep(0.1)



