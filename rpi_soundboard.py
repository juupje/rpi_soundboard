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
        off_pin = 14

        clk_pin = 2
        dt_pin = 3

        self.pins = [lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, self.switch_pin]
        #turn on the board
        self.switch_pin.switch_to_output(True)
        time.sleep(1)

        # Initialise the lcd class
        self.lcd = characterlcd.Character_LCD_Mono(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6,
                                            lcd_d7, lcd_columns, lcd_rows)
        
        self.sound = 0
        self.page = 0
        self.n_tracks_on_page = 9

        # ===== SETUP GPIO's and connections =====
        GPIO.setmode(GPIO.BCM)
        
        rotary_encoder = RotaryEncoder(clk_pin, dt_pin, GPIO)
        rotary_encoder.set_callback(self.re_callback)
        rotary_encoder.start()

        self.keypad = KeyPad(GPIO, [["1", "2", "3", "A"],["4", "5", "6", "B"],["7", "8", "9", "C"],["*", "0", "#", "D"]],
                        [5,6,13,19], [8,7,16,20])
        self.keypad.addHandler(self.kp_callback)

        self.soundboard = Soundboard()

        GPIO.setup(off_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(off_pin, GPIO.FALLING, callback=self.stop, bouncetime=100)
        self.update_lcd_message()

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
        sys.exit(0)

    def stop(self, channel=None):
        #trigger shutdown
        option = "shutdown"
        cmd = ["bash", f"shutdown", option]
        with open("output.txt", "w+") as file:
            subprocess.run(cmd, stdout=file)
            print("Executed command '" + " ".join(cmd) + "'")
            file.seek(io.SEEK_SET)
            last_line = ""
            output = ""
            for line in file:
                output += line
                last_line = line.strip()
            print("Got response '" + output +"'")
            if(last_line == option):
                print("Shutting down")
                self.lcd.message = "Shutdown..."
                self.cleanup()
            else:
                return f"Shutdown failed... output {output}"

    def update_lcd_message(self):
        message = "Page: " + "ABCD"[self.page] +f" Sound: {self.sound+1:d}"
        try:
            desc = self.soundboard.get_description("ABCD"[self.page], self.sound)
            if(desc):
                if(len(desc) > 16): desc = desc[:16]
                message += f"\n{desc:16s}"
            else:
                print("No description")
        except:
            pass
        self.lcd.message = message

    def setpage(self, _page:str):
        self.page = "ABCD".index(_page)
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
            self.soundboard.play_sound("ABCD"[self.page], self.sound)
        elif(key == "*"):
            pass
        else:
            try:
                self.sound = int(key)-1
                self.update_lcd_message()
                self.soundboard.play_sound("ABCD"[self.page], self.sound)
            except ValueError as e:
                print(e)
