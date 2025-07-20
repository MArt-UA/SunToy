# recorder.py
import os, subprocess, time, threading
import vlc, RPi.GPIO as GPIO
from pydub import AudioSegment

# === GPIO PINS ===
LED_RED   = 16
LED_GREEN = 26
VOLUME_PIN = 22   # кнопка гучності

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
vlc_instance = vlc.Instance('--aout=alsa')
player         = None

# GPIO для LED
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_RED,   GPIO.OUT)
GPIO.setup(LED_GREEN, GPIO.OUT)
GPIO.output(LED_RED,   False)
GPIO.output(LED_GREEN, False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(VOLUME_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)


# === VOLUME SETTINGS ===
volume           = 0.7    # 0.0–1.0
VOLUME_DOWN_STEP = 0.1
VOLUME_UP_STEP   = 0.05
HOLD_INTERVAL    = 0.5

def play_audio(path):
    global player
    if not os.path.exists(path):
        print(f"[recorder] ERROR: {path} not found")
        return
    with lock:
        if player:
            player.stop()
        player = vlc_instance.media_player_new(path)
        player.audio_set_volume(int(volume * 100))
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
            if os.path.exists(RAW_WAV):
                os.remove(RAW_WAV)
                print("[recorder] 🗑️ Видалено старий запис RAW_WAV")
            if os.path.exists(FINAL_WAV):
                os.remove(FINAL_WAV)
                print("[recorder] 🗑️ Видалено старий файл FINAL_WAV")
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

def change_volume():
    """Змінює гучність циклічно (80 → 100 → 40 → 80)."""
    global volume, player
    if   volume < 0.8: volume = 0.8
    elif volume < 1.0: volume = 1.0
    elif volume < 1.1: volume = 0.4
    else: volume = 0.8
    if player:
        player.audio_set_volume(int(volume * 100))
    print(f"[recorder] 🌀 Vol: {int(volume*100)}%")

def toggle_pause_resume():
    """Play/Pause/Resume для записаної історії."""
    global player, recorded
    with lock:
        # Перевірка існування файла та валідності
        if not os.path.exists(FINAL_WAV) or os.path.getsize(FINAL_WAV) < 10000:
            print("[recorder] ❌ Story not ready (no file or too small)")
            play_audio(NOT_READY_MP3)
            return
        # Додаємо: запис дійсно був — прапорець true
        recorded = True
        if not player:
            play_audio(FINAL_WAV)
            print("[recorder] ▶️ Start playing")
        elif player.is_playing():
            player.pause()
            print("[recorder] ⏸️ Paused")
        else:
            player.play()
            print("[recorder] ▶️ Resumed")




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
    global record_mode, blink_green, player
    record_mode = True
    blink_green = False
    if player:
        player.stop()
        player = None
    play_audio(RECORD_START)
    print("[recorder] 🔴 Recorder mode ON — press REC (GPIO27) to record")


def stop():
    global record_mode, player
    record_mode = False
    if player:
        player.stop()
        player = None
    print("[recorder] 🛑 Recorder mode OFF")

def stop_playback():
    global player
    if player:
        player.stop()
        player = None
        print("[recorder] 🛑 Playback stopped")

