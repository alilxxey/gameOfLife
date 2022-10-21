from PyQt5.QtCore import QTimer


class GameOfLifeLoop(QTimer):
    def __init__(self):
        super().__init__()

        self.going = False

        self.delay = 100
        self.timeout.connect(self._loop)
        self.setSingleShot(True)

    def _loop(self):
        if self.going and self.isSingleShot() and self.delay > 0:
            self.start(self.delay)

    def set_delay(self, delay_milliseconds):
        self.delay = delay_milliseconds

    def play(self):
        if self.going:
            return None

        self.stop()
        self.going = True
        self.start(self.delay)

    def pause(self):
        if not self.going:
            return None
        self.stop()
        self.going = False
