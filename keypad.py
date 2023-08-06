from RPi import GPIO
import time
from threading import Timer 
DEFAULT_KEY_DELAY = 300
DEFAULT_REPEAT_DELAY = 1.0
DEFAULT_REPEAT_RATE = 2.0
DEFAULT_DEBOUNCE_TIME = 50

class KeyPad:
    def __init__(self, gpio, keypad:list[list[int]], row_pins:list[int], col_pins:list[int],
                 key_delay:int=DEFAULT_KEY_DELAY, repeat_delay:int=DEFAULT_REPEAT_DELAY, repeat_rate:int=DEFAULT_REPEAT_RATE,
                 debouncetime:int=DEFAULT_DEBOUNCE_TIME):
        self._gpio = gpio
        self.keypad = keypad
        self.row_pins = row_pins
        self.col_pins = col_pins
        assert len(keypad)==len(row_pins), "Keypad rows does not match row_pins"
        assert len(keypad[0])==len(col_pins), "Keypad columns does not match col_pins"
        self.key_delay = key_delay
        assert (repeat_delay is None)==(repeat_rate is None), "Both repeat_delay and repeat_rate should be provided or neither"
        self.repeat_delay = repeat_delay
        self.repeat_rate = repeat_rate
        self._repeat = repeat_delay or repeat_delay
        self.debouncetime = debouncetime

        self._handlers = []

        self._last_key_press_time = 0
        self._first_repeat = False
        self._repeat_timer = None

        self._initRows()
        self._initCols()

    def _repeatTimerCallback(self):
        self._repeat_timer = None
        self._onKeyPressed()

    def addHandler(self, handler):
        self._handlers.append(handler)

    def remoteHandler(self, handler):
        self._handlers.remove(handler)

    def _onKeyPressed(self, channel=None):
        now_millis = time.time()*1000
        if now_millis < self._last_key_press_time + self.key_delay:
            return
        keyPressed = self.getKey()
        if keyPressed is not None:
            for handler in self._handlers:
                handler(keyPressed)
            self._last_key_press_time = now_millis
            if self._repeat:
                self._repeat_timer = Timer(self.repeat_delay if self._first_repeat else 1.0/self.repeat_rate, self._repeatTimerCallback)
                self._first_repeat = False
                self._repeat_timer.start()
        else:
            if self._repeat_timer is not None:
                self._repeat_timer.cancel()
            self._repeat_timer = None
            self._first_repeat = True

    def getKey(self):
        # first check the rows
        key = None
        row, rowpin = None, None
        for i, pin in enumerate(self.row_pins):
            if(self._gpio.input(pin) == GPIO.LOW):
                row = i
                rowpin = pin
                break
        
        #now scan the columns
        col = None
        if row is not None:
            for i, pin in enumerate(self.col_pins):
                self._gpio.output(pin, GPIO.HIGH)
                if self._gpio.input(rowpin) == GPIO.HIGH:
                    self._gpio.output(pin, GPIO.LOW)
                    col = i
                    break
                self._gpio.output(pin, GPIO.LOW)
        if(col is not None): #if row is None, col will automatically be None too
            key = self.keypad[row][col]
        return key

    def _initRows(self):
        for pin in self.row_pins:
            self._gpio.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            self._gpio.add_event_detect(pin, GPIO.FALLING, callback=self._onKeyPressed, bouncetime=self.debouncetime)

    def _initCols(self):
        for pin in self.col_pins:
            self._gpio.setup(pin, GPIO.OUT)
            self._gpio.output(pin, GPIO.LOW)

    def cleanup(self):
        if(self._repeat_timer):
            self._repeat_timer.cancel()
