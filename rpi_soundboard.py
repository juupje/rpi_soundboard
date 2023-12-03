import time
import sys
import board
import digitalio
import adafruit_character_lcd.character_lcd as characterlcd
from rotary_encoder import RotaryEncoder 
from RPi import GPIO
from keypad import KeyPad
from soundboard import Soundboard
import subprocess, io
import utils

class Controller:
    def __init__(self):
        # Modify this if you have a different sized character LCD
        lcd_columns = 16
        lcd_rows = 2

        # compatible with all versions of RPI as of Jan. 2019
        # v1 - v3B+
        lcd_rs = digitalio.DigitalInOut(board.D22)
        lcd_en = digitalio.DigitalInOut(board.D17)
        lcd_d4 = digitalio.DigitalInOut(board.D25)
        lcd_d5 = digitalio.DigitalInOut(board.D24)
        lcd_d6 = digitalio.DigitalInOut(board.D23)
        lcd_d7 = digitalio.DigitalInOut(board.D18)

        self.switch_pin = digitalio.DigitalInOut(board.D21)

        self.shutdown_flag = 0
        play_pin = 14

        clk_pin = 2
        dt_pin = 3

        self.pins = [lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, self.switch_pin]
        #turn on the board
        self.switch_pin.switch_to_output(True)
        time.sleep(1)

        # Initialise the lcd class
        self.lcd = characterlcd.Character_LCD_Mono(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6,
                                            lcd_d7, lcd_columns, lcd_rows)

        # ===== SETUP GPIO's and connections =====
        GPIO.setmode(GPIO.BCM)
        
        rotary_encoder = RotaryEncoder(clk_pin, dt_pin, GPIO)
        rotary_encoder.set_callback(self.re_callback)
        rotary_encoder.start()

        self.keypad = KeyPad(GPIO, [["1", "2", "3", "A"],["4", "5", "6", "B"],["7", "8", "9", "C"],["*", "0", "#", "D"]],
                        [5,6,13,19], [8,7,16,20])
        self.keypad.addHandler(self.kp_callback)

        self.soundboard = Soundboard()
        self.sound = 0
        self.page = "A"
        self.n_tracks_on_page = self.soundboard.get_ntracks(self.page)

        GPIO.setup(play_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(play_pin, GPIO.FALLING, callback=lambda _: self.play(), bouncetime=200)
        self.lcd.message = f"{utils.getIP()}"

    def __del__(self):
        self.cleanup()

    def cleanup(self, sig=None, frame=None):
        self.lcd.clear()
        del self.lcd
        self.keypad.cleanup()
        self.switch_pin.value = False
        time.sleep(1)
        for pin in self.pins:
            pin.deinit()
        GPIO.cleanup()

    def play(self):
        print("Playing sound!")
        self.soundboard.play_sound(self.page, self.sound)

    def stop(self, channel=None):
        self.cleanup()
        print("shutting down")
        command = "sudo /sbin/shutdown -h now"
        import subprocess
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
        output = process.communicate()[0]
        print(output)

    def set_page_track(self, page:str, track:int):
        if(self.soundboard.page_exists(page)):
            if(0 < track <= self.soundboard.get_ntracks(page)):
                self.page = page
                self.sound = track
                return True
        return False

    def update_lcd_message(self):
        message = "Page: " + self.page +f" Sound: {self.sound+1:d}"
        try:
            desc = self.soundboard.get_description(self.page, self.sound)
            if(desc):
                if(len(desc) > 16): desc = desc[:16]
                message += f"\n{desc:16s}"
            else:
                print("No description")
        except:
            pass
        self.lcd.message = message

    def setpage(self, _page:str):
        self.page = _page
        self.n_tracks_on_page = self.soundboard.get_ntracks(_page)
        if(self.n_tracks_on_page==0):
            print("Selected page doesn't exist")
            self.n_tracks_on_page = 1 # to prevent module 0
        self.sound = self.sound%self.n_tracks_on_page
        self.update_lcd_message()

    # setup the rotary encoder
    def re_callback(self, counter, delta):
        self.sound = (self.sound + delta)%self.n_tracks_on_page
        self.update_lcd_message()

    def kp_callback(self, key:str):
        print("Pressed key:", key)
        if(key in "ABCD"):
            self.setpage(key)
            self.update_lcd_message()
        elif(key == "#"):
            if(self.shutdown_flag > 0 and time.time()-self.shutdown_flag < 5):
                self.stop()
            else:
                self.lcd.message = "Shutdown?       \nPress # again   "
                self.shutdown_flag = time.time()
        elif(key == "*"):
            if(self.page == "D"):
                self.setpage("H")
        else:
            try:
                self.sound = int(key)-1
                self.update_lcd_message()
                self.play()
            except ValueError as e:
                print(e)
