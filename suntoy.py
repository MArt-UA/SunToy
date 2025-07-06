print('Привіт із SunToy!')

# Імпорт бібліотек

import pygame
import os 
import time
import subprocess
from pydub import AudioSegment
from gpiozero import Button
from signal import pause

# Налаштування 

pygame.mixer.init()
volume_level = 0.8 #Початкова гучність

# Кнопки

button_play = Button(17)
button_rec = Button(27)

# Зміна стану 

current_tag = None
is_recording = False
recording_process = None 

# Функції для відтворення звуку

def play_sound (filename):
  pygame.mixer.music.load(filename)
  pygame.mixer.music.set_volume(volume_level)
  pygame.mixer.music.play()
  while pygame.mixer.music.get_busy():
    time.sleep(0.1)

# Привітання та увімкнення

def greeting():
   play_sound('sounds/introTurnOn.mp3')
   #play_sound('sounds/black-sabbath_-_iron-man.mp3')
  
  # Реакція на NFC-мітку

def intro_for_tag(tag_id):
  if tag_id == 'Kotygoroshko123':
    play_sound('sounds/introToy.mp3')
  elif tag_id == 'REC456':
    play_sound('sounds/introToy.mp3')

# Запис мікрофону  
def start_recording():
  global is_recording, recording_process 
  is_recording = True
  print('🎙️ Початок запису...')
  recording_process = subprocess.Popen([
    'arecord',
    '-D', 'plughw:3,0',  # або plughw:1,0 — якщо ваша карта інша
    '-f', 'cd',
    '-t', 'wav',
    '-d', '300',
    '-r', '44100',
    'sounds/recorded_story.wav'
])

  ''' -D plughw:1,0 — вибирає мікрофон (можемо змінити, якщо треба)
-f cd — стандартна якість (16-біт, 44100 Гц)
-t wav — тип файлу
-d 30 — тривалість 30 сек (може обірватися раніше вручну)
& — фоновий режим, щоб програма не зависла'''

  # Завершення запису 
def stop_recording():
  global is_recording, recording_process
  if recording_process:
    recording_process.terminate()
    recording_process.wait()
    print('Запис завершено!')
  is_recording = False
  mix_with_background()
  if not os.path.exists('sounds/final_story.wav'):  # Перевірка чи є об'єднаний файл записаної історії
     print('Файл ще не готовий!')
     return

  # Мікшування запису + музика
def mix_with_background():
  voice = AudioSegment.from_wav('sounds/recorded_story.wav') +10
  music = AudioSegment.from_mp3('sounds/backgroundSoundForRecord.mp3') - 25 #робить звук фону тихіше від -1 до -25
  while len(music) < len(voice):
    music += music
  music = music[:len(voice)]
  final = music.overlay(voice)
  final.export('sounds/final_story.wav', format='wav')
  print('Обєднано з фоном.')

# Робота кнопки Play
def on_play_pressed():
  if current_tag == 'FOX123':
    play_sound('sounds/storyKotygoroshko.mp3')
  elif current_tag == 'REC456':
    play_sound('sounds/final_story.wav')

# Робота кнопки Record
def on_rec_pressed():
  if not is_recording:
    start_recording()
  else:
    stop_recording()      

# Симуляція NFC
def simulate_nfc(tag_id):
  global current_tag
  current_tag = tag_id
  intro_for_tag(tag_id)

# Обробка кнопок 
button_play.when_pressed = on_play_pressed
button_rec.when_pressed = on_rec_pressed

# Привітання
#greeting()

# Очікування (утримання програми в памяті)
#pause()
print('Симуляція мітки REC456 (режим запису)')
simulate_nfc('REC456')
time.sleep(1)

print('Натискання кнопки запису - початок запису')
on_rec_pressed()
time.sleep(10) #записуємо 10 секунд
print('Натискання кнопки запису вдруге - зупинка і мікшування')
on_rec_pressed()

print('Натискання кнопки програвання - відтворення фінального файлу')
on_play_pressed()


#
