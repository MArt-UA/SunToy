import board
import busio
import threading
import time
import os
import subprocess
import vlc
import RPi.GPIO as GPIO
from pydub import AudioSegment
from adafruit_pn532.i2c import PN532_I2C

# === GPIO PINS ===
RECORD_BTN = 27      # button to start/stop recording
PLAY_BTN = 17        # button to play/pause playback
LED_RED = 16         # red LED during recording
LED_GREEN = 26       # green LED blinking after recording

# === NFC TAG IDS (hex.uids) ===
PLAY_TAG = "53c5be5d720001"      # story playback tag
REC_TAG = "abcdef123456"        # recording tag (replace with your UID)

# === AUDIO PATHS ===
BASE = "/home/pi/SunToy/SunToy/sounds/Record"
RECORD_START = os.path.join(BASE, "record_start.mp3")
RECORD_FINISH = os.path.join(BASE, "record_end.mp3")
BACKGROUND    = os.path.join(BASE, "backgroundSoundForRecord.mp3")
RECORD_FILE   = os.path.join(BASE, "recorded_story.wav")
MERGED_FILE   = os.path.join(BASE, "final_story.wav")
NOT_READY_MP3 = os.path.join(BASE, "black-sabbath_-_iron-man.mp3")

# === STATE ===
record_mode   = False   # ready to record
is_recording  = False
record_process = None
recorded      = False  # has recorded at least once
player        = None
blink_green   = False  # controls green LED blinking
lock          = threading.RLock()

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(RECORD_BTN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PLAY_BTN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(LED_RED, GPIO.OUT)
GPIO.setup(LED_GREEN, GPIO.OUT)

# VLC instance
vlc_instance = vlc.Instance()

# Play any audio file via VLC
def play_audio(path):
    global player
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return
    with lock:
        if player:
            player.stop()
        player = vlc_instance.media_player_new(path)
        player.audio_set_volume(100)
        player.play()
        print(f"[🔊] Playing: {path}")

# Mix recorded voice with background
def mix_with_background():
    print("🔄 Mixing audio...")
    voice = AudioSegment.from_wav(RECORD_FILE) +20
    music = AudioSegment.from_mp3(BACKGROUND) - 20
    # loop music to match voice length
    while len(music) < len(voice):
        music += music
    music = music[:len(voice)]
    final = music.overlay(voice)
    final.export(MERGED_FILE, format="wav")
    print("✅ Mixed final story.")

# Record button handler
def rec_button_pressed(channel=None):
    global is_recording, record_process, recorded, record_mode, blink_green
    with lock:
        if record_mode and not is_recording:
            print("🎙️ Start recording...")
            record_process = subprocess.Popen([
                'arecord','-D','plughw:1,0','-f','cd', '-t','wav',
                '-d','180', RECORD_FILE
            ])
            is_recording = True
            GPIO.output(LED_RED, True)
            blink_green = False
        elif record_mode and is_recording:
            print("🛑 Stop recording")
            if record_process:
                record_process.terminate()
                record_process.wait()
            is_recording = False
            recorded = True
            record_mode = False
            GPIO.output(LED_RED, False)
            play_audio(RECORD_FINISH)
            mix_with_background()
            blink_green = True

# Play/Pause button handler
def play_button_pressed(channel=None):
    global recorded, blink_green
    with lock:
        GPIO.output(LED_GREEN, False)
        blink_green = False
        if recorded and os.path.exists(MERGED_FILE):
            print("▶️ Playing final story")
            play_audio(MERGED_FILE)
        else:
            print("❌ Story not created")
            play_audio(NOT_READY_MP3)

# LED blinking thread
def led_blinker():
    while True:
        if blink_green:
            GPIO.output(LED_GREEN, True)
            time.sleep(1)
            GPIO.output(LED_GREEN, False)
            time.sleep(1)
        else:
            GPIO.output(LED_GREEN, False)
            time.sleep(0.1)

# NFC reader init
i2c = busio.I2C(board.SCL, board.SDA)
pn532 = PN532_I2C(i2c, debug=False)
ic, ver, rev, support = pn532.firmware_version
print(f"PN532 firmware: {ver}.{rev}")
pn532.SAM_configuration()

# Setup button events
gpio_event = GPIO.FALLING
GPIO.add_event_detect(RECORD_BTN, gpio_event, callback=rec_button_pressed, bouncetime=300)
GPIO.add_event_detect(PLAY_BTN, gpio_event, callback=play_button_pressed, bouncetime=300)

# Start LED blinker
t = threading.Thread(target=led_blinker, daemon=True)
t.start()

# Main loop: NFC tag handling
last_uid = None
print("Waiting for NFC tags...")
while True:
    uid = pn532.read_passive_target(timeout=0.5)
    if uid:
        uid_str = uid.hex()
        if uid_str != last_uid:
            print(f"Tag detected: {uid_str}")
            last_uid = uid_str
            if uid_str == "23307f14":
                if not recorded and not record_mode:
                    play_audio(RECORD_START)
                    record_mode = True
                elif recorded and not record_mode:
                    play_audio(RECORD_FINISH)
            elif uid_str == PLAY_TAG:
                # can trigger greeting or other
                play_button_pressed()
    time.sleep(0.2)


