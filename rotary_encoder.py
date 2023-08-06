from RPi import GPIO
class RotaryEncoder:
    def __init__(self, clk_pin:int, dt_pin:int, gpio):
        self.clk = clk_pin
        self.dt = dt_pin
        self.gpio = gpio
        self.counter = 0
        gpio.setup(self.clk, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        gpio.setup(self.dt, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        self.clkLastState = gpio.input(self.clk)
        self.isRunning = False
        self.set_callback(None)

    def set_callback(self, callback):
        self.callback = callback
        if(self.isRunning and callback is None):
            print("RotaryEncoder: Changed callback to None, stopping listening...")
            self.stop()

    def _on_clk_change(self, channel):
        clkState = self.gpio.input(self.clk)
        if(self.clkLastState != clkState):
            dtState = self.gpio.input(self.dt)
            delta = 1 if dtState != clkState else -1
            self.counter += delta
            self.clkLastState = clkState
            if(self.callback):
                self.callback(self.counter, delta)
        else:
            # dunno why this was called, but just ignore it
            pass

    def start(self):
        if(self.callback):
            self.gpio.add_event_detect(self.clk, GPIO.BOTH, callback=self._on_clk_change)
            self.isRunning = True

    def stop(self):
        self.gpio.remove_event_detect(self.clk)
        self.isRunning = False