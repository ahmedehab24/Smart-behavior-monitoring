import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import busio
import smbus2
import board

class ADS1115Reader:
    def __init__(self, channel=0, gain=1):
        # Setup I2C manually
        import RPi.GPIO as GPIO
        import smbus

        self.i2c = busio.I2C(board.SCL, board.SDA)  # This will actually work if you have I2C enabled
        self.ads = ADS.ADS1115(self.i2c)
        self.ads.gain = gain

        self.channel = AnalogIn(self.ads, getattr(ADS, f'P{channel}'))

    def read_voltage(self):
        return self.channel.voltage
