import board
import neopixel
import time

NUM_PIXELS = 8
PIXEL_PIN = board.D18  # GPIO18

pixels = neopixel.NeoPixel(PIXEL_PIN, NUM_PIXELS, brightness=0.5, auto_write=False)

while True:
    for i in range(NUM_PIXELS):
        pixels[i] = (255, 0, 0)  # червоний
        pixels.show()
        time.sleep(0.1)
        pixels[i] = (0, 0, 0)


