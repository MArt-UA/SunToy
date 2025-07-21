import board
import busio
import time
from adafruit_pn532.i2c import PN532_I2C

# --- 1. Налаштування I2C ---
i2c = busio.I2C(board.SCL, board.SDA)
pn532 = PN532_I2C(i2c, debug=False)

# --- 2. Налаштування для Mifare Classic ---
KEY_DEFAULT = b'\xFF\xFF\xFF\xFF\xFF\xFF'  # Стандартний ключ

def read_all_blocks():
    print("ПРИКЛАДІТЬ ПЕРШУ МІТКУ (оригінал)...")
    uid = pn532.read_passive_target(timeout=0.5)
    while uid is None:
        uid = pn532.read_passive_target(timeout=0.5)
    uid = bytes(uid)
    print("UID raw:", uid, type(uid))
    print("UID:", [hex(i) for i in uid])
    all_data = []
    for block_num in range(0, 64):
        if block_num % 4 == 3:
            all_data.append(None)
            continue
        try:
            if pn532.mifare_classic_authenticate_block(
                uid, block_num, 0x60, KEY_DEFAULT  # <--- порядок!
            ):
                block = pn532.mifare_classic_read_block(block_num)
                all_data.append(block)
            else:
                all_data.append(None)
        except Exception as e:
            print(f"Block {block_num}: error {e}")
            all_data.append(None)
    return all_data

def write_all_blocks(all_data):
    print("ПРИКЛАДІТЬ ДРУГУ МІТКУ (порожню для запису)...")
    uid = pn532.read_passive_target(timeout=0.5)
    while uid is None:
        uid = pn532.read_passive_target(timeout=0.5)
    uid = bytes(uid)
    print("UID (нова):", [hex(i) for i in uid])
    for block_num, block in enumerate(all_data):
        if block is None or block_num % 4 == 3:
            continue
        try:
            if pn532.mifare_classic_authenticate_block(
                uid, block_num, 0x60, KEY_DEFAULT
            ):
                ok = pn532.mifare_classic_write_block(block_num, block)
                if ok:
                    print(f"Block {block_num} записано")
                else:
                    print(f"Block {block_num} НЕ записано")
        except Exception as e:
            print(f"Block {block_num}: error {e}")



if __name__ == "__main__":
    data = read_all_blocks()
    time.sleep(2)
    write_all_blocks(data)
    print("Готово!")



