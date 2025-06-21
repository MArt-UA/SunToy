import board
import busio
from digitalio import DigitalInOut
from adafruit_pn532.i2c import PN532_I2C

# Ініціалізація I2C
i2c = busio.I2C(board.SCL, board.SDA)
pn532 = PN532_I2C(i2c, debug=False)

# Отримати версію прошивки для перевірки
ic, ver, rev, support = pn532.firmware_version
print('Found PN532 with firmware version: {0}.{1}'.format(ver, rev))

# Налаштування для зчитування карток
pn532.SAM_configuration()

print('Торкніться NFC міткою до зчитувача')

while True:
    uid = pn532.read_passive_target(timeout=0.5)
    if uid is not None:
        print('Знайдено мітку з UID: 0x{0}'.format(uid.hex()))
