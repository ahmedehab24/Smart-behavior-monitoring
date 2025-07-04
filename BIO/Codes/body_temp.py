import time
import board
import busio
import adafruit_mlx90614

# Setup I2C
i2c = busio.I2C(board.SCL, board.SDA)

# Wait until I2C is ready
while not i2c.try_lock():
    pass

def safe_i2c_scan(i2c_bus):
    found = []
    for address in range(0x08, 0x78):
        try:
            i2c_bus.writeto(address, b"")
            found.append(address)
        except Exception:
            pass
    return found

try:
    devices = safe_i2c_scan(i2c)
    if devices:
        print("I2C devices found:", [hex(dev) for dev in devices])
    else:
        print("No I2C devices found. Check wiring and power.")
        i2c.unlock()
        exit(1)
finally:
    i2c.unlock()

if 0x5A not in devices:
    print("MLX90614 not detected at address 0x5A.")
    exit(1)

# Initialize sensor
try:
    mlx = adafruit_mlx90614.MLX90614(i2c, address=0x5A)
except Exception as e:
    print("Failed to initialize MLX90614:", e)
    exit(1)

# Read loop
try:
    while True:
        try:
            ambient_temp = mlx.ambient_temperature
            object_temp = mlx.object_temperature

            # Core body temp estimation using fixed offset
            offset = 1.0  # You can fine-tune this (1.5–2.5 typically)
            core_est = object_temp + offset

            print(f"Ambient Temperature      : {ambient_temp:.2f} °C")
            print(f"Measured Skin Temp       : {object_temp:.2f} °C")
            print(f"Estimated Core Body Temp : {core_est:.2f} °C")
            print("-" * 40)

        except OSError:
            print("Read error (OSError 121). Sensor may be disconnected or busy. Retrying...")
        except Exception as e:
            print(f"Unexpected error: {e}")
        
        time.sleep(1.5)  # Prevents overloading the sensor

except KeyboardInterrupt:
    print("Program stopped manually.")
