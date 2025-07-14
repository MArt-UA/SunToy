# recorder.py
import os, subprocess, time, threading
import vlc, RPi.GPIO as GPIO
from pydub import AudioSegment

# === GPIO PINS ===
LED_RED   = 16
LED_GREEN = 26

# === AUDIO PATHS ===
BASE           = "/home/pi/SunToy/SunToy/sounds/Record"
RECORD_START   = os.path.join(BASE, "record_start.mp3")
RECORD_FINISH  = os.path.join(BASE, "record_end.mp3")
BACKGROUND_MP3 = os.path.join(BASE, "backgroundSoundForRecord.mp3")
RAW_WAV        = os.path.join(BASE, "recorded_story.wav")
FINAL_WAV      = os.path.join(BASE, "final_story.wav")
NOT_READY_MP3  = os.path.join(BASE, "black-sabbath_-_iron-man.mp3")

# === STATE ===
record_mode    = False
is_recording   = False
recorded       = False
record_process = None
blink_green    = False
lock           = threading.RLock()
vlc_instance   = vlc.Instance()
player         = None

# GPIO для LED
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_RED,   GPIO.OUT)
GPIO.setup(LED_GREEN, GPIO.OUT)
GPIO.output(LED_RED,   False)
GPIO.output(LED_GREEN, False)

def play_audio(path):
    global player
    if not os.path.exists(path):
        print(f"[recorder] ERROR: {path} not found")
        return
    with lock:
        if player:
            player.stop()
        player = vlc_instance.media_player_new(path)
        player.audio_set_volume(70)
        player.play()

def mix_with_background():
    print("[recorder] 🔄 Mixing audio...")
    voice = AudioSegment.from_wav(RAW_WAV) + 25
    music = AudioSegment.from_mp3(BACKGROUND_MP3) - 20
    while len(music) < len(voice):
        music += music
    music = music[:len(voice)]
    final = music.overlay(voice)
    final.export(FINAL_WAV, format="wav")
    print("[recorder] ✅ Mixed final story")

def rec_button_pressed():
    """START/STOP запис у режимі record_mode."""
    global is_recording, record_process, recorded, record_mode, blink_green
    with lock:
        if record_mode and not is_recording:
            print("[recorder] 🎙️ Start recording…")
            GPIO.output(LED_RED, True)
            record_process = subprocess.Popen([
                "arecord","-D","plughw:1,0",
                "-f","cd","-t","wav","-d","180", RAW_WAV
            ])
            is_recording = True

        elif record_mode and is_recording:
            print("[recorder] ⏹️ Stop recording")
            record_process.terminate()
            record_process.wait()
            is_recording = False
            recorded     = True
            record_mode  = False
            GPIO.output(LED_RED, False)
            play_audio(RECORD_FINISH)
            mix_with_background()
            blink_green  = True

def play_button_pressed():
    """Відтворити FINAl_WAV чи NOT_READY."""
    global blink_green
    with lock:
        blink_green = False
        GPIO.output(LED_GREEN, False)
        if recorded and os.path.exists(FINAL_WAV):
            print("[recorder] ▶️ Playing final story")
            play_audio(FINAL_WAV)
        else:
            print("[recorder] ❌ Story not ready")
            play_audio(NOT_READY_MP3)

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

# старт блікеру
threading.Thread(target=led_blinker, daemon=True).start()

def start():
    """Викликається з main.py при RECORDER_TAG."""
    global record_mode, blink_green
    record_mode = True
    blink_green = False
    play_audio(RECORD_START)
    print("[recorder] 🔴 Recorder mode ON — press REC (GPIO27) to record")

def stop():
    """Можна викликати з main.py, якщо хочете вийти з recorder-mode."""
    global record_mode
    record_mode = False
    print("[recorder] 🛑 Recorder mode OFF")
