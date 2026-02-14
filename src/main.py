# ---------- Import Libraries ------------
import machine
import time
#Import display driver, from https://github.com/stlehmann/micropython-ssd1306
import ssd1306 
#Import custom icons library
import icons

# ---------- AHT10 Driver ------------
class AHT10:
    def __init__(self, i2c, addr=0x38):
        self.i2c = i2c
        self.addr = addr
        self.reset()
        time.sleep(0.1)
        self.calibrate()
        time.sleep(0.1)

    def reset(self):
        self.i2c.writeto(self.addr, b'\xBA')  # soft reset

    def calibrate(self):
        self.i2c.writeto(self.addr, b'\xE1\x08\x00')

    def measure(self):
        self.i2c.writeto(self.addr, b'\xAC\x33\x00')
        time.sleep(0.08)
        data = self.i2c.readfrom(self.addr, 6)
        if (data[0] & 0x80) != 0:
            raise Exception("AHT10 busy")
        t = ((data[3] & 0x0F) << 16 | data[4] << 8 | data[5]) * 200 / 1048576 - 50
        h = ((data[1] << 16 | data[2] << 8 | (data[3] & 0xF0)) >> 4) * 100 / 1048576
        return t, h

    @property
    def temperature(self):
        t, _ = self.measure()
        return t

    @property
    def relative_humidity(self):
        _, h = self.measure()
        return h

# ---------- Initialize I2C ----------
i2c_oled = machine.I2C(0, sda=machine.Pin(0), scl=machine.Pin(1)) #Pin GP0 and GP1
i2c_sensor = machine.I2C(1, sda=machine.Pin(2), scl=machine.Pin(3)) #Pin GP2 and GP3

# ---------- Initialize devices ----------
oled = ssd1306.SSD1306_I2C(128, 32, i2c_oled)
sensor = AHT10(i2c_sensor)

# ---------- Main loop ----------
def draw_icon(oled, icon, x, y):
    for row, bits in enumerate(icon):
        for col in range(8):
            if (bits >> (7 - col)) & 1:
                oled.pixel(x + col, y + row, 1)
epoch = time.time()
icon_toggle = False

while True:
    temp = sensor.temperature
    hum = sensor.relative_humidity
    oled.fill(0)
    #Show if the PI has crashed by not moving the icon on the top left anymore
    if temp > 25:
        if icon_toggle:
            draw_icon(oled, icons.fire1_icon, 0, 0)
        else:
            draw_icon(oled, icons.fire2_icon, 0, 0)
    elif temp < 21:
        #draw toggle freezing icon
        draw_icon(oled, icons.ice_icon, 0, 0)
    elif 21 < temp and temp < 25:
        draw_icon(oled, icons.alright_icon, 0, 0)
    if hum > 60:
        if icon_toggle:
            draw_icon(oled, icons.rain1_icon, 0, 10)
        else:
            draw_icon(oled, icons.rain2_icon, 0, 10)
    if hum < 40:
        if icon_toggle:
            draw_icon(oled, icons.ball1_icon, 0, 10)
        else:
            draw_icon(oled, icons.ball2_icon, 0, 10)
    elif 40 < hum and hum < 60 :
        draw_icon(oled, icons.alright_icon, 0, 10)
        
    #Main text
    print("Temp: {:.1f}C".format(temp))
    print("Hum:  {:.1f}%".format(hum))
    oled.text("Temp: {:.1f}C".format(temp), 10, 0)
    oled.text("Hum:  {:.1f}%".format(hum), 10, 10)
    
    #Time counter since the PI has been turned on
    cur_time = time.time() - epoch
    if cur_time <= 59 :
        if cur_time == 1:
            oled.text("On for " + str(cur_time) + " Second", 1, 20)
        else:
            oled.text("On for " + str(cur_time) + " Seconds", 1, 20)
    elif cur_time >= 86400:
        cur_time_day = cur_time // 86400
        if cur_time_day == 1:
            oled.text("On for " + str(cur_time_day) + " Day", 1, 20)
        else:
            oled.text("On for " + str(cur_time_day) + " Days", 1, 20)
    elif cur_time >= 3600 :
        cur_time_hour = cur_time // 3600
        if cur_time_hour == 1:
            oled.text("On for " + str(cur_time_hour) + " Hour", 1, 20)
        else:
            oled.text("On for " + str(cur_time_hour) + " Hours", 1, 20)
    elif cur_time >= 60 :
        cur_time_min = cur_time // 60
        if cur_time_min == 1:
            oled.text("On for " + str(cur_time_min) + " Minute", 1, 20)
        else:
            oled.text("On for " + str(cur_time_min) + " Minutes", 1, 20)
            
    icon_toggle = not icon_toggle
    oled.show()
    time.sleep(1)