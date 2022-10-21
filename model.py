import numpy as np
from collections import deque


class GameOfLife:
    def __init__(self, initial_state):
        # Состояния хранятся в матрице из bool
        # A[i, j] == True -- клетка i, j живая
        self.initial_state = initial_state.copy()
        self.state = initial_state.copy()
        self.prev_state = initial_state.copy()

        # Номер поколения
        self.age = 1

        # Предыдущие состояния
        self.history = deque(maxlen=100)

        # Завершена ли игра (все клетки мертвы или состояние стабильное)
        # Если да, то хранится причина завершения в виде строки
        self._finished = False
        self._finish_reason = None

        # Находится ли игра в периодическом состоянии
        # Если да, то хранится информация в виде строки об этом состоянии
        self._periodic = False
        self._periodic_info = None

    # Get методы состояния игры и его описания

    def is_finished(self):
        return self._finished

    def finish_reason(self):
        return self._finish_reason

    def is_periodic(self):
        return self._periodic

    def periodic_info(self):
        return self._periodic_info

    # Полная очистка игры, размеры сохраняются
    def clear(self):
        self.initial_state[:, :] = False
        self.prev_state[:, :] = False
        self.state[:, :] = False
        self.history.clear()
        self.age = 1
        self._finished = False
        self._finish_reason = None
        self._periodic = False
        self._periodic_info = None

    # Высота и ширина игрового поля в кол-ве клеток
    def height(self):
        return self.state.shape[0]

    def width(self):
        return self.state.shape[1]

    # Смена состояния клетки i, j
    def toggle_cell(self, i, j):
        self.state[i, j] = not self.state[i, j]
        if self.age == 1:
            self.initial_state[i, j] = self.state[i, j]

    # Шаг игры
    def next(self):
        if self._finished:
            return None

        # Смена состояний
        self.prev_state, self.state = self.state, self.prev_state
        # Сохранение истории
        self.history.appendleft(self.prev_state.copy())

        # Обозначение клеток-соседей (компас)
        # nw nn ne
        # ww    ee
        # sw ss se

        N, M = self.prev_state.shape
        for i in range(N):
            for j in range(M):
                n, s = (i - 1) % N, (i + 1) % N
                w, e = (j - 1) % M, (j + 1) % M

                ww = self.prev_state[i, w]
                ee = self.prev_state[i, e]
                nn = self.prev_state[n, j]
                ss = self.prev_state[s, j]
                nw = self.prev_state[n, w]
                ne = self.prev_state[n, e]
                sw = self.prev_state[s, w]
                se = self.prev_state[s, e]

                # print(i, j)
                # print((n, w), (n, j), (n, e))
                # print((i, w), (i, j), (i, e))
                # print((s, w), (s, j), (s, e))

                live_neighbours = (
                         int(ww) + int(ee) + int(nn) + int(ss)
                       + int(nw) + int(ne) + int(sw) + int(se)
                )

                # print(f"live_neighbours = {live_neighbours}")

                if self.prev_state[i, j]:
                    # Правила для живой клетки
                    self.state[i, j] = live_neighbours == 2 or live_neighbours == 3
                else:
                    # Правило для мёртвой клетки
                    self.state[i, j] = live_neighbours == 3

        self.age += 1

        if not self._periodic:
            self._finished = self._check_finished()
            self._periodic = self._check_periodic()

        return self.state

    def _check_finished(self):
        if np.all(self.state == False):
            self._finish_reason = f"Все клетки мертвы. Поколение {self.age}."
            return True

        if np.all(self.state == self.prev_state):
            self._finish_reason = f"Стабильная конфигурация. Поколение {self.age}."
            return True

        return False

    def _check_periodic(self):
        # Просмотр истории, сравнение с текущим состоянием
        for (i, state) in enumerate(self.history):
            if i == 0:  # Игнорирование предыдущего состояния (стабильный случай)
                continue
            if np.all(self.state == state):
                self._periodic_info = f"Периодическая конфигурация. Поколения {self.age - i - 1} и {self.age}."
                return True
        return False


# Утилиты для создания/изменения игры
class GameOfLifeMaker:
    @classmethod
    def fromio(cls, io):
        rows, cols = None, None

        while rows is None or cols is None:
            line = io.readline()

            if not line.strip():
                continue
            if line.startswith("#"):
                continue

            if line.startswith("rows = "):
                rows = int(line.split()[2])
            if line.startswith("cols = "):
                cols = int(line.split()[2])

        io.readline()
        state = GameOfLifeLoader.string_to_matrix(io.read(), minsize=(rows, cols))
        return GameOfLife(state)

    # Загрузка из файла формата patterns/glider.txt
    @classmethod
    def fromtxt(cls, path):
        with open(path) as io:
            return GameOfLifeMaker.fromio(io)

    # Создать пустую игру с полем размера w x h
    @classmethod
    def empty(cls, w, h):
        m = np.zeros((w, h), dtype=np.bool_)
        return GameOfLife(m)

    # Обновление игры по записи из базы данных
    @classmethod
    def update_from_database(cls, game, age, init_str, curr_str, size=None):
        size = (size or (game.width(), game.height()))

        game.clear()
        game.age = age
        game.initial_state = GameOfLifeLoader.string_to_matrix(init_str, minsize=size)
        game.prev_state = game.initial_state.copy()
        game.state = GameOfLifeLoader.string_to_matrix(curr_str, minsize=size)


# Утилиты конвертации состояния поля
class GameOfLifeLoader:
    @classmethod
    def string_to_matrix(cls, string, minsize=(30, 30)):
        # Создаёт матрицу для игры из строки
        # Cтрочка поля отделяется newline
        # Клетка -- один символ
        # Живая клетка -- "x"
        # Мёртвая клетка -- не "x"
        # Например "..x\n.x.\nx.." соответствует полю
        #   False False True
        #   False True  False
        #   True  False False
        # Допустимо, чтобы строка была "не квадратной". Это экономит память
        # Например "..x\n.x\nx" соответствует полю выше

        rows = string.splitlines()

        rows_count = max(minsize[0], len(rows))
        # Для числа столбцов надо ещё найти самую длинную строку (string не "квадратная")
        cols_count = max(minsize[1], max(map(len, rows)))

        # Наверняка, в numpy есть для этого функция
        matrix = np.zeros((rows_count, cols_count), dtype=np.bool_)
        for (i, row) in enumerate(rows):
            for (j, char) in enumerate(row):
                matrix[i, j] = char == "x"

        return matrix

    @classmethod
    def matrix_to_string(cls, matrix):
        # Конвертирует матрицу в строку, соответствующую формату
        # GameOfLifeLoader.string_to_matrix
        s = ""
        for i in range(matrix.shape[0]):
            row = ""
            for j in range(matrix.shape[1]):
                row += "x" if matrix[i, j] else "."
            s += row.rstrip(".")  # Обрезка мёртвых клеток справа, не несут информации
            s += "\n"
        return s
