import RPi.GPIO as GPIO
import time

LED_PIN = 17  # GPIO17

GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)

try:
    while True:
        GPIO.output(LED_PIN, GPIO.HIGH)  # вмикаємо
        time.sleep(0.)
        GPIO.output(LED_PIN, GPIO.LOW)   # вимикаємо
        time.sleep(0.)
except KeyboardInterrupt:
    GPIO.output(LED_PIN, GPIO.LOW)
    GPIO.cleanup()


