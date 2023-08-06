import time
import signal, sys
import board
import digitalio
import adafruit_character_lcd.character_lcd as characterlcd
from rotary_encoder import RotaryEncoder 
from RPi import GPIO
from keypad import KeyPad
from soundboard import Soundboard
import subprocess, io

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

switch_pin = digitalio.DigitalInOut(board.D21)
off_pin = 14

clk_pin = 2
dt_pin = 3

pins = [lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, switch_pin]
#turn on the board
switch_pin.switch_to_output(True)
time.sleep(1)

def cleanup(sig=None, frame=None):
    global lcd
    lcd.clear()
    del lcd
    keypad.cleanup()
    switch_pin.value = False
    time.sleep(1)
    for pin in pins:
        pin.deinit()
    GPIO.cleanup()
    sys.exit(0)
signal.signal(signal.SIGINT, cleanup)

def stop(channel=None):
    #trigger shutdown
    option = "shutdown"
    cmd = ["bash", f"shutdown", option]
    with open("output.txt", "w+") as file:
        subprocess.run(cmd, stdout=file)         
        print("Executed command '" + " ".join(cmd) + "'");#
        file.seek(io.SEEK_SET)
        last_line = ""
        output = ""
        for line in file:
            output += line
            last_line = line.strip()
        print("Got response '" + output +"'")
        if(last_line == option):
            print("Shutting down")
            lcd.message = "Shutdown..."
            cleanup()
        else:
            return f"Shutdown failed... output {output}"

# Initialise the lcd class
lcd = characterlcd.Character_LCD_Mono(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6,
                                      lcd_d7, lcd_columns, lcd_rows)

# ===== SETUP GPIO's and connections =====
GPIO.setmode(GPIO.BCM)

# setup the LCD screen
lcd = characterlcd.Character_LCD_Mono(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6,
                                      lcd_d7, lcd_columns, lcd_rows)
sound = 0
page = 0
n_tracks_on_page = 9

def update_lcd_message():
    message = "Page: " + "ABCD"[page] +f" Sound: {sound+1:d}"
    try:
        desc = soundboard.get_description("ABCD"[page], sound)
        if(desc):
            if(len(desc) > 16): desc = desc[:16]
            message += f"\n{desc:16s}"
        else:
            print("No description")
    except:
        pass
    lcd.message = message

def setpage(_page:str):
    global page, n_tracks_on_page, sound
    page = "ABCD".index(_page)
    n_tracks_on_page = soundboard.get_ntracks(_page)
    if(n_tracks_on_page==0):
        print("Selected page doesn't exist")
        n_tracks_on_page = 1 # to prevent module 0
    sound = sound%n_tracks_on_page
    update_lcd_message()

# setup the rotary encoder
rotary_encoder = RotaryEncoder(clk_pin, dt_pin, GPIO)
def re_callback(counter, delta):
    global sound
    sound = (sound + delta)%n_tracks_on_page
    update_lcd_message()

def kp_callback(key:str):
    global page, sound
    print("Pressed key:", key)
    if(key in "ABCD"):
        setpage(key)
        update_lcd_message()
    elif(key == "#"):
        soundboard.play_sound("ABCD"[page], sound)
    elif(key == "*"):
        pass
    else:
        try:
            sound = int(key)-1
            update_lcd_message()
            soundboard.play_sound("ABCD"[page], sound)
        except ValueError as e:
            print(e)

rotary_encoder.set_callback(re_callback)
rotary_encoder.start()
update_lcd_message()

keypad = KeyPad(GPIO, [["1", "2", "3", "A"],["4", "5", "6", "B"],["7", "8", "9", "C"],["*", "0", "#", "D"]],
                [5,6,13,19], [8,7,16,20])
keypad.addHandler(kp_callback)

soundboard = Soundboard()

GPIO.setup(off_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(off_pin, GPIO.FALLING, callback=stop, bouncetime=100)

time.sleep(1000)
cleanup()