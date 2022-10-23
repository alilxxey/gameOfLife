import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
import configparser
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWidgets import QLabel, QPushButton, QSlider, QWidget
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout
from PyQt5.QtWidgets import QSizePolicy
import sqlite3
from model import GameOfLifeLoader, GameOfLifeMaker
from dialogs import GameFinishedDialog, GamePeriodicDialog, GameSaveDialog, GameLoadDialog
import ast


# Цвета для клеток
class GameFieldViewSettings:
    cfg = configparser.ConfigParser()
    cfg.read('utils/config.ini')

    live_cell_color = ast.literal_eval(cfg['VIEW']['live_cell_color'])
    dead_cell_color = ast.literal_eval(cfg['VIEW']['dead_cell_color'])


# Пример использования
# v = GameFieldView()
# v.attach_model(GameOfLife(...))
# v.update()  # только после этой команды поле загружено на экран
class GameFieldView(QLabel):
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)

        self.show_settings = GameFieldViewSettings()
        self.model = None

    def attach_model(self, model):
        # Теперь виджет знает, откуда брать данные (model: GameOfLife)
        self.model = model

        # Размер клетки -- 20px х 20px
        self.resize(20*model.height(), 20*model.width())
        self.update()

    def update(self):
        # Обновляет поле в соответсвии состояниию модели
        # 1. Сгенерировать изображение
        # 2. Создать pixmap для показа изображения
        # 3. Показать pixmap, натянув на реальные размеры виджета
        image = self.toImage(self.model.state)
        pixmap = QPixmap().fromImage(image)
        self.setPixmap(pixmap.scaled(self.size(), Qt.KeepAspectRatio))

    def toImage(self, matrix):
        # Создание изображения из матрицы bool-ов

        # Матрица, в ячейка хранится rgb код
        rgb = np.zeros((matrix.shape[0], matrix.shape[1], 3), dtype=np.uint8)
        # Цвет живых клеток
        rgb[np.where(matrix)] = self.show_settings.live_cell_color
        # Цвет мёртвых клеток
        rgb[np.where(np.invert(matrix))] = self.show_settings.dead_cell_color
        # Изображение -- матрица, ширина на высоту, число байтов в строке, формат хранения -- RGB
        img = QImage(rgb, rgb.shape[1], rgb.shape[0], rgb.strides[0], QImage.Format_RGB888)
        return img

    def pixel_to_cell(self, x, y):
        # Конвертирует положение пикселя виджета x, y в индекс клетки на игровом поле
        i = int(self.model.height() * (y / self.height()))
        j = int(self.model.width() * (x / self.width()))
        return i, j

    def mousePressEvent(self, e):
        # Рисование
        # Происходит по клику левой кнопки мыши
        # Вычисляем по какой клетке из модели произошёл клик и перекрашиываем клетку
        if e.button() == Qt.LeftButton:
            i, j = self.pixel_to_cell(e.pos().x(), e.pos().y())
            self.model.toggle_cell(i, j)
            self.update()


# Главное окно приложения
# Связующее GameOfLife, отображения и игрового цикла
class MainWindow(QMainWindow):
    def __init__(self, game, game_loop):
        super().__init__()

        self.setWindowTitle("Игра жизнь")

        # Игра (GameOfLife), игровой таймер, отображения поля
        self.game = game
        self.game_loop = game_loop
        self.field = GameFieldView()
        self.field.attach_model(game)

        # Игровой цикл каждую итерацию
        # Обновляет модель и её отображение на экране
        # Проверяет, закончилась ли игра
        self.game_loop.timeout.connect(self.game.next)
        self.game_loop.timeout.connect(self.field.update)
        self.game_loop.timeout.connect(self.update_age)

        self.game_loop.timeout.connect(self.check_game_finished)
        self.game_loop.timeout.connect(self.check_game_periodic)

        # Попала ли игра в периодическое состояние (флаг)
        self._game_entered_periodic_state = self.game.is_periodic()

        # Интерфейс
        # Разметка: в горизонтальном боксе находятся два вертикальных (два столбца в итоге)
        layout_window = QHBoxLayout()

        layout_left = QVBoxLayout()
        layout_right = QVBoxLayout()
        layout_window.addLayout(layout_left)
        layout_window.addLayout(layout_right)

        self._age_label = QLabel()

        layout_left.addWidget(self.field)
        layout_left.addWidget(self._age_label)
        layout_left.addStretch()

        self.play = QPushButton("Запуск")
        self.pause = QPushButton("Пауза")
        self.speed = QSlider(Qt.Horizontal)
        # Скорость -- обратная величина периоду обновления
        self.speed.setMinimum(10)    # 10 мс
        self.speed.setMaximum(1000)  # 1000 мс = 1 сек
        self.speed.setValue(800)
        self.speed.setTickInterval(50)  # Шаг слайдера 50 мс
        self.speed_changed()  # Обновляет начальный период для игрового таймера

        layout_right.addWidget(self.play)
        layout_right.addWidget(self.pause)
        layout_right.addWidget(QLabel("Скорость"))
        layout_right.addWidget(self.speed)

        self.newgame = QPushButton("Новая игра")
        self.load = QPushButton("Загрузить")
        self.save = QPushButton("Сохранить")

        layout_right.addStretch()  # Разделитель между кнопками сверху и снизу
        layout_right.addWidget(self.newgame)
        layout_right.addWidget(self.load)
        layout_right.addWidget(self.save)

        w = QWidget()
        w.setLayout(layout_window)
        self.setCentralWidget(w)

        # События
        self.play.clicked.connect(self.play_clicked)
        self.pause.clicked.connect(self.pause_clicked)
        self.speed.valueChanged.connect(self.speed_changed)
        self.newgame.clicked.connect(self.newgame_clicked)
        self.save.clicked.connect(self.save_clicked)
        self.load.clicked.connect(self.load_clicked)

        # Начальное состояние интерфейса
        self.newgame_ui_state()

    def newgame_ui_state(self):
        self.play.setEnabled(True)
        self.pause.setEnabled(False)
        self.speed.setEnabled(True)
        self.newgame.setEnabled(True)
        self.load.setEnabled(True)
        self.save.setEnabled(False)

    def game_finished_ui_state(self):
        # Когда игра закончилась, разрешаем начать новую или сохранить
        self.play.setEnabled(False)
        self.pause.setEnabled(False)
        self.speed.setEnabled(False)
        self.newgame.setEnabled(True)
        self.load.setEnabled(False)
        self.save.setEnabled(True)

    def play_clicked(self):
        # Продолжаем игру, запрещаем все действия, кроме скорости и паузы
        self.game_loop.play()

        self.play.setEnabled(False)
        self.pause.setEnabled(True)
        self.speed.setEnabled(True)
        self.save.setEnabled(False)
        self.load.setEnabled(False)
        self.newgame.setEnabled(False)

    def pause_clicked(self):
        # Ставим таймер на паузу
        # Разрешаем продолжить игру, изменить скорость, сохранение или начало новой
        self.game_loop.pause()

        self.play.setEnabled(True)
        self.pause.setEnabled(False)
        self.speed.setEnabled(True)
        self.save.setEnabled(True)
        self.load.setEnabled(False)
        self.newgame.setEnabled(True)

    def newgame_clicked(self):
        # Создание новой игры с тем же полем
        self.game_loop.pause()

        self.game.clear()
        self.field.update()
        self.update_age()
        self._game_entered_periodic_state = self.game.is_periodic()
        self.newgame_ui_state()

    def update_age(self):
        self._age_label.setText(str(self.game.age))

    def speed_changed(self):
        # Задержка цикла -- обратная скорости величина
        delay = (self.speed.minimum() + self.speed.maximum()) - self.speed.value()
        self.game_loop.set_delay(delay)

    def resizeEvent(self, ev):
        # Перегрузка стандартного события для виджета
        # Нужна для обновления игрового поля при запуске
        self.field.update()
        super().resizeEvent(ev)

    def check_game_finished(self):
        if not self.game.is_finished():
            return None

        # Игра закончилась
        # Останавливаем игровой цикл
        # Показываем сообщение об остановке
        self.game_loop.pause()

        dialog = GameFinishedDialog(self.game.finish_reason())
        dialog.exec_()

        self.game_finished_ui_state()

    def check_game_periodic(self):
        if not self.game.is_periodic():
            return None

        if self._game_entered_periodic_state:
            return None

        # Игра обнаружила периодическое состояние
        # Ставим на паузу
        # Показываем сообщение
        # Обрабатываем, хочет ли юзер продолжить
        self._game_entered_periodic_state = True
        self.game_loop.pause()

        dialog = GamePeriodicDialog(self.game.periodic_info())
        dialog.exec_()

        if dialog.user_wants_continue:
            self.game_loop.play()
        else:
            self.game_finished_ui_state()

    def save_clicked(self):
        # Сохранение игры
        # Ставим таймер на паузу
        # Показывает окно для сохранения, юзер там что-то вводит
        # Обрабатывает ввод пользователя
        self.game_loop.pause()

        dialog = GameSaveDialog()
        dialog.exec_()

        if dialog.game_name is None:
            return None

        game_name = dialog.game_name
        age = self.game.age
        initial_state = self.game.initial_state
        current_state = self.game.state
        size = (self.game.width(), self.game.height())
        init_str = GameOfLifeLoader.matrix_to_string(initial_state)
        curr_str = GameOfLifeLoader.matrix_to_string(current_state)

        con = sqlite3.connect('utils/database.db')
        cur = con.cursor()
        cur.execute("""
                        INSERT INTO data
                         (game_name, age, init_str, curr_str, size)
                         VALUES
                         (?, ?, ?, ?, ?)
                        """,
                    (game_name, age, init_str, curr_str, str(size)))
        con.commit()
        con.close()
        print(repr(game_name))  # str
        print(repr(age))        # int
        print(repr(init_str))   # str
        print(repr(curr_str))   # str

    def load_clicked(self):
        # Загрузка игры
        # Ставим на паузу
        # Показываем окно для загрузки
        # Пользователь там что-то выбрал
        # Обновляем состояние глобальной игры с той, что из базы данных
        self.game_loop.pause()

        dialog = GameLoadDialog(self.game)
        dialog.exec_()
        if not dialog.load_success:
            return None

        GameOfLifeMaker.update_from_database(
            game=self.game,
            age=dialog.game_age,
            init_str=dialog.game_init_str,
            curr_str=dialog.game_curr_str,
            size=dialog.size
            # TODO: size=() # done

        )
        self.field.update()
        self.update_age()
        self.newgame_ui_state()

