from gpiozero import PWMLED, Button
from signal import pause

# PWM-світлодіоди (fade-режим)
led1 = PWMLED(26)
led2 = PWMLED(16)

# Кнопки (з pull_up=False бо сенсорні)
button1 = Button(17, pull_up=False)
button2 = Button(27, pull_up=False)

# Статус мигання
is_pulsing = False

def toggle_breathing():
    global is_pulsing
    is_pulsing = not is_pulsing

    if is_pulsing:
        print("🌬️ Дихання УВІМКНЕНО")
        led1.pulse(fade_in_time=1, fade_out_time=3, background=True)
        led2.pulse(fade_in_time=1, fade_out_time=1, background=True)
    else:
        print("🛑 Дихання ВИМКНЕНО")
        led1.off()
        led2.off()

# Призначаємо функцію на кнопку
button1.when_pressed = toggle_breathing

# Можна додати дію для другої кнопки
# button2.when_pressed = ...

pause()


