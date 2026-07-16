import time
from collections import deque

import board
import busio
import digitalio

led_pins = [board.GP3, board.GP15, board.GP5, board.GP10]
leds = []
for led_pin in led_pins:
    led = digitalio.DigitalInOut(led_pin)
    led.direction = digitalio.Direction.OUTPUT
    led.value = False
    leds.append(led)

uart = busio.UART(board.GP0, board.GP1, baudrate=115200)

spi = busio.SPI(board.GP6, MOSI=board.GP7, MISO=board.GP16)
while not spi.try_lock():
    pass
spi.configure(baudrate=5000000, phase=1, polarity=1)

LEFT, RIGHT, UP, DOWN = 0, 1, 2, 3
cs_pins = [board.GP28, board.GP27, board.GP22, board.GP20]
accelerometers = []

for cs_pin in cs_pins:
    cs = digitalio.DigitalInOut(cs_pin)
    cs.direction = digitalio.Direction.OUTPUT
    cs.value = True
    accelerometers.append(cs)

ADXL345_POWER_CTL = 0x2D
ADXL345_DATA_FORMAT = 0x31
ADXL345_DATAX0 = 0x32

SCALE_FACTOR = 0.004
FILTER_WINDOW = 5
SIDE_SENSITIVITY = 3.0
SHAKE_THRESHOLD = 0.5
DEBOUNCE_TIME = 1.0

history = [deque((0.0, 0.0, 0.0) for _ in range(FILTER_WINDOW), FILTER_WINDOW) for _ in range(4)]
mag_history = [deque((0.0,) * FILTER_WINDOW, FILTER_WINDOW) for _ in range(4)]
last_hit_time = [0.0] * 4

DIRECTION_NAMES = ["LEFT", "RIGHT", "UP", "DOWN"]
DIRECTION_MAP = {"LEFT": LEFT, "RIGHT": RIGHT, "UP": UP, "DOWN": DOWN}


def bytes_to_int16(low_byte, high_byte):
    val = (high_byte << 8) | low_byte
    if val & 0x8000:
        val -= 65536
    return val


def write_register(accel, register, value):
    cs = accelerometers[accel]
    cs.value = False
    spi.write(bytes([register & 0x3F, value]))
    cs.value = True


def read_registers(accel, register, length):
    cs = accelerometers[accel]

    header = register | 0x80
    if length > 1:
        header |= 0x40

    cs.value = False
    spi.write(bytes([header]))

    result = bytearray(length)
    spi.readinto(result)
    cs.value = True

    return result


def low_pass_filter(i, x, y, z):
    history[i].append((x, y, z))
    n = len(history[i])
    sx = sy = sz = 0.0
    for vx, vy, vz in history[i]:
        sx += vx
        sy += vy
        sz += vz
    return sx / n, sy / n, sz / n


for i in range(4):
    write_register(i, ADXL345_DATA_FORMAT, 0x0B)
    write_register(i, ADXL345_POWER_CTL, 0x08)

resting = [(0.0, 0.0, 0.0)] * 4
for _ in range(20):
    for i in range(4):
        data = read_registers(i, ADXL345_DATAX0, 6)
        rx, ry, rz = resting[i]
        resting[i] = (
            rx + bytes_to_int16(data[0], data[1]) * SCALE_FACTOR,
            ry + bytes_to_int16(data[2], data[3]) * SCALE_FACTOR,
            rz + bytes_to_int16(data[4], data[5]) * SCALE_FACTOR,
        )
    time.sleep(0.01)
resting = [(x / 20, y / 20, z / 20) for x, y, z in resting]

for i in range(4):
    leds[i].value = False

rx_buffer = ""

while True:
    magnitudes = [0.0] * 4
    for i in range(4):
        data = read_registers(i, ADXL345_DATAX0, 6)

        x = bytes_to_int16(data[0], data[1]) * SCALE_FACTOR
        y = bytes_to_int16(data[2], data[3]) * SCALE_FACTOR
        z = bytes_to_int16(data[4], data[5]) * SCALE_FACTOR

        fx, fy, fz = low_pass_filter(i, x, y, z)

        rx, ry, rz = resting[i]
        dx = (fx - rx) * SIDE_SENSITIVITY
        dy = (fy - ry) * SIDE_SENSITIVITY
        dz = fz - rz
        magnitude = (dx ** 2 + dy ** 2 + dz ** 2) ** 0.5
        mag_history[i].append(magnitude)
        magnitudes[i] = magnitude

        print(f"ADXL[{i}]: x={fx:.3f}, y={fy:.3f}, z={fz:.3f}, mag={magnitude:.3f}")

    avg_mags = [sum(mh) / len(mh) for mh in mag_history]

    now = time.monotonic()
    if max(magnitudes) > SHAKE_THRESHOLD:
        hit = max(range(4), key=lambda i: avg_mags[i])
        if now - last_hit_time[hit] >= DEBOUNCE_TIME:
            uart.write(f"{DIRECTION_NAMES[hit]}\n".encode())
            last_hit_time[hit] = now

    if uart.in_waiting:
        rx_buffer += uart.read(uart.in_waiting).decode()
        while "\n" in rx_buffer:
            idx = rx_buffer.index("\n")
            command = rx_buffer[:idx]
            rx_buffer = rx_buffer[idx + 2:]
            if command.startswith("LIGHTON+"):
                direction = command[8:]
                if direction in DIRECTION_MAP:
                    leds[DIRECTION_MAP[direction]].value = True
            elif command.startswith("LIGHTOFF+"):
                direction = command[9:]
                if direction in DIRECTION_MAP:
                    leds[DIRECTION_MAP[direction]].value = False

    time.sleep(0.05)
