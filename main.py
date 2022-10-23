import ast
from loop import GameOfLifeLoop
from model import GameOfLifeMaker
from view import MainWindow
from PyQt5.QtWidgets import QApplication
import configparser


if __name__ == "__main__":

    app = QApplication([])
    cfgmain = configparser.ConfigParser()
    cfgmain.read('utils/config.ini')
    # game = GameOfLifeMaker.fromtxt("patterns/glider.txt")
    game = GameOfLifeMaker.empty(*ast.literal_eval(cfgmain['MAIN']['SIZE']))
    game_loop = GameOfLifeLoop()

    window = MainWindow(game, game_loop)
    window.show()

    app.exec_()
