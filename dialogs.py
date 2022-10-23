from PyQt5 import QtCore
from PyQt5.QtWidgets import QDialog, QDialogButtonBox
from PyQt5.QtWidgets import QLabel, QLineEdit, QVBoxLayout
from PyQt5.QtWidgets import QTableWidget
from PyQt5.QtWidgets import QTableWidgetItem
import sqlite3
from model import GameOfLifeMaker


class GameFinishedDialog(QDialog):
    def __init__(self, message, title=open("utils/text.txt").read()):
        try:
            super().__init__()
            self.setWindowTitle(title)

            layout = QVBoxLayout()
            self.setLayout(layout)

            label = QLabel(message)
            buttons = QDialogButtonBox(QDialogButtonBox.Ok)

            layout.addWidget(label)
            layout.addWidget(buttons)

            buttons.accepted.connect(self.accept)
        except Exception as e:
            print(e)


class GamePeriodicDialog(QDialog):
    def __init__(self, message, title="Игра в периодическом состоянии"):
        try:
            super().__init__()

            self.user_wants_continue = False

            self.setWindowTitle(title)

            layout = QVBoxLayout()
            self.setLayout(layout)

            label = QLabel(message)
            buttons = QDialogButtonBox(QDialogButtonBox.Yes | QDialogButtonBox.No)

            layout.addWidget(label)
            layout.addWidget(QLabel("Вы хотите продолжить игру?"))
            layout.addWidget(buttons)

            buttons.accepted.connect(self.accept)
            buttons.rejected.connect(self.reject)

            buttons.accepted.connect(self._yes_clicked)
            buttons.rejected.connect(self._no_clicked)
        except Exception as e:
            print(e)

    def _yes_clicked(self):
        self.user_wants_continue = True

    def _no_clicked(self):
        self.user_wants_continue = False


class GameSaveDialog(QDialog):
    def __init__(self, title="Сохранение игры"):
        try:
            super().__init__()

            self.game_name = None

            self.setWindowTitle(title)

            layout = QVBoxLayout()
            self.setLayout(layout)

            label = QLabel("Введите название игры")
            self.name_edit = QLineEdit()
            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

            layout.addWidget(label)
            layout.addWidget(self.name_edit)
            layout.addWidget(buttons)

            buttons.accepted.connect(self.accept)
            buttons.accepted.connect(self._read_name)
            buttons.rejected.connect(self.reject)
        except Exception as e:
            print(e)

    def _read_name(self):
        self.game_name = (self.name_edit.text().strip() or "Без названия")


class TableWidget(QTableWidget):
    def __init__(self, parent=None):
        try:
            super(TableWidget, self).__init__(parent)
            self.mouse_press = None
        except Exception as e:
            print(e)

    def mousePressEvent(self, event):
        try:
            if event.button() == QtCore.Qt.LeftButton:
                self.mouse_press = "mouse left press"
            elif event.button() == QtCore.Qt.RightButton:
                self.mouse_press = "mouse right press"
            elif event.button() == QtCore.Qt.MidButton:
                self.mouse_press = "mouse middle press"
            super(TableWidget, self).mousePressEvent(event)
        except Exception as e:
            print(e)


class GameLoadDialog(QDialog):
    def __init__(self, game, title="Загрузка игры из БД"):
        try:
            super().__init__()
            self.game = game
            self.load_success = False
            self.game_age = None
            self.game_init_str = None
            self.game_curr_str = None
            self.size = None
            self.resize(300, 300)
            self.setWindowTitle(title)

            layout = QVBoxLayout()
            self.setLayout(layout)

            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

            con = sqlite3.connect('utils/database.db')
            cur = con.cursor()
            items = cur.execute("""SELECT * FROM data
            """)
            k = []
            for i in items:
                k.append(i)
            self.tableWidget = TableWidget()
            self.tableWidget.setRowCount(len(k))

            self.tableWidget.setColumnCount(2)
            self.tableWidget.resize(100, 100)
            self.tableWidget.setHorizontalHeaderLabels(['имя', 'поколение'])
            # Этот сигнал испускается всякий раз, когда ячейка в таблице нажата.
            # Указанная строка и столбец - это ячейка, которая была нажата.
            self.tableWidget.cellPressed[int, int].connect(self.clickedRowColumn)

            for i in range(len(k)):
                for j in range(2):
                    item = QTableWidgetItem(str(k[i][j]))
                    item.setTextAlignment(QtCore.Qt.AlignHCenter)
                    self.tableWidget.setItem(i, j, item)

            layout.addWidget(self.tableWidget)
            layout.addWidget(buttons)
            con.close()

            buttons.accepted.connect(self.accept)
            # buttons.accepted.connect(self._load_game)
            buttons.rejected.connect(self.close)
        except Exception as e:
            print(e)

    def clickedRowColumn(self, r, c):
        try:
            con = sqlite3.connect('utils/database.db')
            cur = con.cursor()
            items = cur.execute(f"""SELECT * FROM 'data'
             WHERE game_name = '{self.tableWidget.item(r, 0).text()}'
                    """)
            for i in items:
                k = i
            print(k)
            self.load_success = True
            self.game_age = k[1]
            self.game_init_str = k[2]
            self.game_curr_str = k[3]
            self.size = k[4]
            print(k[4])
            #GameOfLifeMaker.update_from_database(
            #                                     self.game,
            #                                     age=k[1],
            #                                    init_str=k[2],
            #                                     curr_str=k[3]
            #                                     )

            con.close()
            return k
        except Exception as e:
            print(e)
