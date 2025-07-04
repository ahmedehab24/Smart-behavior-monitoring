# max30102_driver.py

import time
from smbus2 import SMBus

MAX30102_I2C_ADDRESS = 0x57

# Register addresses
REG_INTR_STATUS_1 = 0x00
REG_INTR_ENABLE_1 = 0x02
REG_FIFO_WR_PTR = 0x04
REG_OVF_COUNTER = 0x05
REG_FIFO_RD_PTR = 0x06
REG_FIFO_DATA = 0x07
REG_MODE_CONFIG = 0x09
REG_SPO2_CONFIG = 0x0A
REG_LED1_PA = 0x0C
REG_LED2_PA = 0x0D

class MAX30102:
    def __init__(self, bus_num=1):
        self.bus = SMBus(bus_num)
        self.address = MAX30102_I2C_ADDRESS
        self.setup()

    def setup(self):
        self.bus.write_byte_data(self.address, REG_INTR_ENABLE_1, 0xC0)  # Interrupts
        self.bus.write_byte_data(self.address, REG_FIFO_WR_PTR, 0x00)
        self.bus.write_byte_data(self.address, REG_OVF_COUNTER, 0x00)
        self.bus.write_byte_data(self.address, REG_FIFO_RD_PTR, 0x00)
        self.bus.write_byte_data(self.address, REG_MODE_CONFIG, 0x03)    # SpO2 mode
        self.bus.write_byte_data(self.address, REG_SPO2_CONFIG, 0x27)    # 100 Hz, 411us, 18-bit
        self.bus.write_byte_data(self.address, REG_LED1_PA, 0x4F)        # Red LED current
        self.bus.write_byte_data(self.address, REG_LED2_PA, 0x4F)        # IR LED current

    def read_fifo(self):
        # Read 6 bytes from FIFO (3 bytes Red, 3 bytes IR)
        try:
            data = self.bus.read_i2c_block_data(self.address, REG_FIFO_DATA, 6)
            red_val = (data[0] << 16) | (data[1] << 8) | data[2]
            ir_val = (data[3] << 16) | (data[4] << 8) | data[5]
            red_val &= 0x3FFFF
            ir_val &= 0x3FFFF
            return red_val, ir_val
        except Exception as e:
            print("Read error:", e)
            return None, None

    def shutdown(self):
        self.bus.write_byte_data(self.address, REG_MODE_CONFIG, 0x80)
        self.bus.close()
