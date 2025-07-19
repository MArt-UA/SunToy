# recorder.py
import vlc, os, subprocess, threading, time, RPi.GPIO as GPIO
from pydub import AudioSegment

# pins & paths
REC_PIN      = 27
LED_REC      = None  # will be set in start()
RECORD_START = "/home/pi/SunToy/SunToy/sounds/Record/record_start.mp3"
RECORD_FINISH= "/home/pi/SunToy/SunToy/sounds/Record/record_end.mp3"
BACKGROUND   = "/home/pi/SunToy/SunToy/sounds/Record/backgroundSoundForRecord.mp3"
RAW_WAV      = "/home/pi/SunToy/SunToy/sounds/Record/recorded_story.wav"
FINAL_WAV    = "/home/pi/SunToy/SunToy/sounds/Record/final_story.wav"

is_recording = False
stop_flag    = threading.Event()

def play_tone(path):
    if os.path.exists(path):
        p = vlc.MediaPlayer(path); p.play(); time.sleep(0.1)

def mix_background():
    voice = AudioSegment.from_wav(RAW_WAV)+20
    music= AudioSegment.from_mp3(BACKGROUND)-20
    while len(music)<len(voice): music+=music
    final=music.overlay(voice)
    final.export(FINAL_WAV,format="wav")
    print("[recorder] ✅ Mixed")

def rec_button_pressed(channel=None):
    global is_recording
    if not is_recording:
        print("[recorder] 🎙️ Start")
        play_tone(RECORD_START)
        GPIO.output(LED_REC,True)
        proc = subprocess.Popen([
            "arecord","-D","plughw:1,0","-f","cd","-d","180",RAW_WAV
        ])
        is_recording = True
        threading.Thread(target=lambda: proc.wait() or rec_button_pressed(), daemon=True).start()
    else:
        print("[recorder] 🛑 Stop")
        subprocess.run(["pkill","-f","arecord"])
        is_recording = False
        GPIO.output(LED_REC,False)
        play_tone(RECORD_FINISH)
        mix_background()

def play_button_pressed(channel=None):
    if os.path.exists(FINAL_WAV):
        print("[recorder] ▶️ Play")
        p = vlc.MediaPlayer(FINAL_WAV); p.play()
    else:
        print("[recorder] ❌ No recording")

def stop():
    pass

def start(led_rec):
    global LED_REC
    LED_REC = led_rec
    GPIO.add_event_detect(REC_PIN, GPIO.FALLING,
                          callback=rec_button_pressed,bouncetime=300)
    GPIO.add_event_detect(17, GPIO.FALLING,  # play-pin still needed for recorder
                          callback=play_button_pressed,bouncetime=300)
    print("[recorder] ready")

# expose
__all__ = ("start","rec_button_pressed","play_button_pressed","stop")
