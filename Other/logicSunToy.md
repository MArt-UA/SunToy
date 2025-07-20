# Логіка роботи іграшки "Сонцесяйчик" (SunToy)

## Загальні принципи

- **Фізичний перемикач** живлення (ON/OFF)
- **Автономна робота**, без підключення до інтернету
- **Світлова індикація** працює м'яко, з можливістю відключення (нічний режим)
- **Аудіофайли** та запис зберігаються у файловій структурі з ідентифікаторами фігурок
- **Можливість роботи під час заряджання** (але за потреби — обмеження для безпеки)

---

## Стан 1: Ввімкнення

- Подія: перемикач переведено в ON
- Дія:
  - Програти "hello.wav"
  - Увімкнути жовту індикацію на 2 секунди
  - Перейти в режим очікування

---

## Стан 2: Очікування

- Подія: фігурку встановлено на платформу
- Дія:
  - Зчитати NFC
  - Перевірити UID на валідність (оригінальна фігурка)
  - Якщо вперше — програти інтро (напр. "kotyhoroshko_intro.wav")
  - Підготувати до відтворення казку або запис
  - Індикатор блимає в очікуванні дії

---

## Стан 3: Відтворення

- Подія: натиснуто кнопку ▶️ (Play/Pause)
- Дія:
  - Програти відповідну казку (або запис батьків, якщо він є)
  - Під час відтворення — світлова індикація в такт звуку
  - Повторне натискання ▶️ — пауза

---

## Стан 4: Запис голосу

- Подія: фігурка встановлена ➕ натиснуто і утримано кнопку ⏺️ (Rec)
- Дія:
  - Почати запис з мікрофона (до 5 хвилин)
  - Відпускання або закінчення часу — зберегти запис у `/records/{UID}.wav`

---

## Стан 5: Відтворення запису

- Подія: встановлена фігурка, для якої є запис
- Дія:
  - Зміксувати голосовий запис + фонову музику
  - Програти при натисканні кнопки ▶️

---

## Керування гучністю

- 2 кнопки: ➖ / ➕ (можливо бокові)
- 5 рівнів гучності

---

## Нічний режим

- Подія: натиснуто кнопку 🔕
- Дія:
  - Вимикає повністю світлову індикацію
  - Можливо активується після 21:00 або вручну

---

## Поведінка NFC

- NFC активний постійно, але нову фігурку можна зчитати **тільки у режимі очікування** або після паузи
- Можливо додати таймер блокування NFC на час казки (щоб дитина не плутала фігурки)

---

## Індикація живлення та зарядки

- 🔋 Розряджений акумулятор — **рожеве або червоне світло** (мерехтіння)
- 🔌 Підключено зарядку:
  - Під час зарядки — **жовтий або помаранчевий колір**
  - Повна зарядка — **зелений колір**
- Працює під час заряджання, але можливо з обмеженням підсвітки або гучності (для безпеки)

---

## Файлова структура

```
/audio/
  kotyhoroshko/
    intro.wav
    main.wav

/records/
  kotyhoroshko_user.wav

/system/
  hello.wav
  standby.wav
```

---

## Майбутні ідеї:

- Активація підсвітки відповідно до емоційної інтонації
- Візуальні підказки для ігрової карти (інтеграція з друкованим матеріалом)
- Можливість автооновлення контенту через підключення до ПК (оновлення пакетом)
- Можливість обмеження часу використання (режим сну)
- Введення казкового "будильника" — запуск історії зранку або на вечір
- Додавання реакцій на рух/перекидання (гіроскоп)
- Можливість подачі нічної історії з таймером вимкнення

## Що до чого підключено

subgraph Кнопки та NFC
PiI2C_SDA([GPIO 2 / SDA])───►PN532[NFC-ридер ]
PiI2C_SCL([GPIO 3 / SCL])───►PN532[NFC-ридер ]

PiT1([GPIO 17])───►Touch1[Play/Pause ]
PiT2([GPIO 27])───►Touch2[Rec ]
PiT3([GPIO 22])───►Touch3[Volume ]
end

subgraph LED
PiLED1([GPIO 13])───►LED1[NFC ]
PiLED2([GPIO 19])───►LED2[NFC ]
PiLED4([GPIO 16])───►LED4[Play/Pause ]
PiLED3([GPIO 26])───►LED3[Rec ]
end


pi@raspberrypi:~/SunToy/SunToy $ /usr/bin/python /home/pi/SunToy/SunToy/main.py
[main] PN532 fw 1.6
[main] ▶️ Boot: boosting USB volume
[main] 📡 NFC watch started
[main] 📛 Tag: 53c4be5d720001
[recorder] play_audio(/home/pi/SunToy/SunToy/sounds/Record/record_start.mp3), player=None
[recorder] player.play() CALLED
[recorder] 🔴 Recorder mode ON — press REC (GPIO27) to record
[b2003b28] alsa audio output error: cannot estimate delay: Input/output error
[main] 🔘 REC pressed, mode=recorder
[recorder] 🎙️ Start recording…
[recorder] 🗑️ Видалено старий запис RAW_WAV
[recorder] 🗑️ Видалено старий файл FINAL_WAV
Recording WAVE '/home/pi/SunToy/SunToy/sounds/Record/recorded_story.wav' : Signed 16 bit Little Endian, Rate 44100 Hz, Stereo
[main] 🔘 REC pressed, mode=recorder
[recorder] ⏹️ Stop recording
Aborted by signal Припинено...
arecord: pcm_read:2152: read error: Перерваний системний виклик
[recorder] play_audio(/home/pi/SunToy/SunToy/sounds/Record/record_end.mp3), player=<vlc.MediaPlayer object at 0xb223f148>
[recorder] Stopping old player...
[recorder] player.play() CALLED
[recorder] 🔄 Mixing audio...
[b2b01f08] alsa audio output error: cannot estimate delay: Input/output error
[recorder] ✅ Mixed final story
[main] ▶️ PLAY pressed, mode=recorder
[recorder] toggle_pause_resume CALLED, player=<vlc.MediaPlayer object at 0xb223f238>
[recorder] RESUME
[main] ▶️ PLAY pressed, mode=recorder
[recorder] toggle_pause_resume CALLED, player=<vlc.MediaPlayer object at 0xb223f238>
[recorder] RESUME
^CTraceback (most recent call last):
  File "/home/pi/SunToy/SunToy/main.py", line 156, in <module>
    main()
  File "/home/pi/SunToy/SunToy/main.py", line 153, in main
    time.sleep(1)
KeyboardInterrupt





