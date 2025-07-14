# player.py
import os, vlc, time, threading
import RPi.GPIO as GPIO

# === GPIO PINS ===
VOLUME_PIN = 27   # кнопка гучності

# === AUDIO PATHS ===
INTRO_FILE  = "/home/pi/SunToy/SunToy/sounds/introTurnOn.mp3"
STORY_INTRO = "/home/pi/SunToy/SunToy/sounds/fairyTale/storyKotygoroshko.mp3"
STORY_FULL  = "/home/pi/SunToy/SunToy/sounds/fairyTale/Kotygoroshko_Full.mp3"

# === VOLUME SETTINGS ===
volume           = 0.7    # 0.0–1.0
VOLUME_DOWN_STEP = 0.1
VOLUME_UP_STEP   = 0.05
HOLD_INTERVAL    = 0.5

# === STATE ===
player        = None
story_queued  = None
active        = False     # ← тільки в режимі player реагує на volume-button
lock          = threading.Lock()
vlc_instance  = vlc.Instance()

# Ініціалізуємо GPIO для volume
GPIO.setmode(GPIO.BCM)
GPIO.setup(VOLUME_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def _play(path):
    global player
    if not os.path.exists(path):
        print(f"[player] ERROR: {path} not found")
        return
    if player:
        player.stop()
    player = vlc_instance.media_player_new(path)
    player.audio_set_volume(int(volume*100))
    player.play()

def play_story():
    """Запускаємо інтро, потім ставимо в чергу повну історію."""
    global story_queued
    _play(STORY_INTRO)
    while player.is_playing():
        time.sleep(0.1)
    story_queued = STORY_FULL
    print("[player] ▶️ Story queued, press PLAY (17) to start")

def toggle_pause_resume():
    """PLAY-пауза/продовження або старт queued story."""
    global story_queued
    with lock:
        if story_queued and not (player and player.is_playing()):
            path = story_queued
            story_queued = None
            print("[player] ▶️ Starting full story")
            _play(path)
            return
        if not player:
            return
        if player.is_playing():
            player.pause()
            print("[player] ⏸️ Paused")
        else:
            player.play()
            print("[player] ▶️ Resumed")

def watch_volume_button():
    """Керування гучністю, тільки коли active==True."""
    global volume
    pressed = False
    last_time = 0.0
    while True:
        if not active:
            time.sleep(0.1)
            continue
        state = GPIO.input(VOLUME_PIN)
        now = time.time()
        if state == GPIO.LOW:
            if not pressed:
                pressed = True
                volume = max(0.0, volume - VOLUME_DOWN_STEP)
                if player:
                    player.audio_set_volume(int(volume*100))
                print(f"[player] 🔉 Vol: {int(volume*100)}%")
                last_time = now
            else:
                if now - last_time >= HOLD_INTERVAL:
                    volume = min(1.0, volume + VOLUME_UP_STEP)
                    if player:
                        player.audio_set_volume(int(volume*100))
                    print(f"[player] 🔊 Vol: {int(volume*100)}%")
                    last_time = now
        else:
            pressed = False
        time.sleep(0.05)

def start():
    """Викликається з main.py при PLAYER_TAG."""
    global active
    active = True
    threading.Thread(target=watch_volume_button, daemon=True).start()
    print("[player] 🚀 Player mode ON — VOLUME on GPIO27, PLAY on GPIO17")

def stop():
    """Викликається з main.py при виході з player-mode."""
    global active
    active = False
    print("[player] 🛑 Player mode OFF")
