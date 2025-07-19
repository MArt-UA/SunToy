# player.py
import vlc, os, threading, time, RPi.GPIO as GPIO

# files
GREETING   = "/home/pi/SunToy/SunToy/sounds/introTurnOn.mp3"
INTRO      = "/home/pi/SunToy/SunToy/sounds/fairyTale/storyKotygoroshko.mp3"
STORY      = "/home/pi/SunToy/SunToy/sounds/fairyTale/Kotygoroshko_Full.ogg"

# state
player      = None
story_ready = None
stop_flag   = threading.Event()
lock        = threading.Lock()

def set_volume(vol_percent):
    with lock:
        if player:
            player.audio_set_volume(vol_percent)

def play_audio(path):
    global player
    with lock:
        if not os.path.exists(path):
            print(f"[player] missing {path}")
            return
        if player:
            player.stop()
        player = vlc.MediaPlayer(path)
        player.audio_set_volume(100)
        player.play()

def toggle_pause_resume():
    with lock:
        if story_ready and (not player or not player.is_playing()):
            print("[player] ▶️ Start story")
            play_audio(story_ready)
            story_ready = None
            return
        if not player: return
        if player.is_playing():
            player.pause()
        else:
            player.play()

def stop():
    with lock:
        if player:
            player.stop()

def fade_led(pin):
    # PWM fade in/out
    pwm = GPIO.PWM(pin, 100)
    pwm.start(0)
    try:
        while not stop_flag.is_set():
            for dc in list(range(0,101,5))+list(range(100,-1,-5)):
                pwm.ChangeDutyCycle(dc)
                time.sleep(0.03)
                if stop_flag.is_set(): break
            if stop_flag.is_set(): break
    finally:
        pwm.stop()
        GPIO.output(pin, False)

def blink_led(pin):
    while not stop_flag.is_set():
        GPIO.output(pin, True); time.sleep(0.5)
        GPIO.output(pin, False); time.sleep(0.5)
    GPIO.output(pin, False)

def start():
    pass  # nothing on module load

def play_story(led_pin):
    # greeting
    print("[player] 👋 greeting")
    play_audio(GREETING)
    time.sleep(1)
    # intro
    print("[player] 🎙️ intro")
    play_audio(INTRO)
    while player.is_playing(): time.sleep(0.1)
    # queue story
    global story_ready
    story_ready = STORY
    print("[player] ⏳ ready, press Play")
    # start fade thread on pause-led
    stop_flag.clear()
    threading.Thread(target=fade_led, args=(13,), daemon=True).start()
    # blink thread on play-led
    threading.Thread(target=blink_led, args=(led_pin,), daemon=True).start()

# expose API
__all__ = ("play_story","toggle_pause_resume","set_volume","stop","start")
