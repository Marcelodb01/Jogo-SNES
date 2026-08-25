# -*- coding: utf-8 -*-
"""
NUCLEO - prototipo mobile (Kivy)
Action-RPG de masmorras: sala fixa por tela, puzzle de blocos, combate simples.

Desktop:  python main.py      (WASD/setas para mover, ESPACO para atacar, R reinicia)
Android:  metade esquerda da tela = analogico virtual, direita = botao de ataque
"""

import math
import traceback

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout

# ------------------------------------------------- diagnostico na tela
_STATUS = {"label": None}


def reportar(onde):
    """Mostra o traceback NA TELA e tambem manda para o logcat."""
    texto = traceback.format_exc()
    print("ERRO EM " + onde + ":\n" + texto)
    lab = _STATUS.get("label")
    if lab is not None:
        linhas = [l for l in texto.strip().split("\n") if l.strip()]
        lab.text = "ERRO em " + onde + "\n" + "\n".join(linhas[-5:])


def guarda(fn):
    """Envolve um metodo: erro vira mensagem na tela, nao fechamento."""
    def wrapper(*a, **kw):
        try:
            return fn(*a, **kw)
        except Exception:
            reportar(fn.__name__)
            return True
    wrapper.__name__ = fn.__name__
    return wrapper

from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.uix.label import Label
from kivy.uix.widget import Widget

# ---------------------------------------------------------------- dados da sala
# '#' parede   '.' chao   'B' bloco   'P' placa   'D' porta
# 'S' inicio   'E' inimigo   'X' saida
ROOM = [
    "################",
    "#.........#....#",
    "#..B......#....#",
    "#.........#....#",
    "#....P....D.X..#",
    "#.........#....#",
    "#..B...P..#....#",
    "#.........#....#",
    "#....S....#....#",
    "#....E....#....#",
    "################",
]

COLS = len(ROOM[0])
ROWS = len(ROOM)

PLAYER_SPEED = 4.2       # tiles por segundo
PLAYER_HALF = 0.32       # meia-largura da hitbox, em tiles
PUSH_DELAY = 0.28        # segundos empurrando antes do bloco ceder
BLOCK_SLIDE = 0.14       # duracao da animacao do bloco
ATTACK_TIME = 0.22
INVULN_TIME = 1.1
ENEMY_SPEED = 1.6
MAX_HP = 3

# paleta
C_BG = (0.05, 0.05, 0.08)
C_FLOOR = (0.16, 0.16, 0.21)
C_GRID = (0.20, 0.20, 0.26)
C_WALL = (0.32, 0.29, 0.38)
C_BLOCK = (0.62, 0.45, 0.26)
C_PLATE_OFF = (0.40, 0.33, 0.22)
C_PLATE_ON = (0.35, 0.72, 0.45)
C_DOOR = (0.72, 0.30, 0.30)
C_EXIT = (0.35, 0.72, 0.90)
C_PLAYER = (0.85, 0.88, 0.95)
C_SWORD = (1.0, 0.95, 0.6)
C_ENEMY = (0.75, 0.35, 0.55)
C_HUD = (0.9, 0.35, 0.4)


class Block(object):
    """Bloco empurravel, alinhado ao grid, com interpolacao visual."""

    def __init__(self, col, row):
        self.col = col
        self.row = row
        self.vc = float(col)   # posicao visual
        self.vr = float(row)
        self.t = 1.0           # progresso da animacao

    def push_to(self, col, row):
        self.col = col
        self.row = row
        self.t = 0.0

    def update(self, dt):
        if self.t < 1.0:
            self.t = min(1.0, self.t + dt / BLOCK_SLIDE)
        self.vc += (self.col - self.vc) * min(1.0, self.t)
        self.vr += (self.row - self.vr) * min(1.0, self.t)


class Enemy(object):
    """Patrulha horizontal simples; morre em um golpe."""

    def __init__(self, col, row):
        self.x = col + 0.5
        self.y = row + 0.5
        self.dir = 1
        self.alive = True


class Game(Widget):

    def __init__(self, **kw):
        super(Game, self).__init__(**kw)
        self.msg = Label(text="", font_size="18sp", halign="center",
                         color=(1, 1, 1, 0.85))
        self.add_widget(self.msg)
        _STATUS["label"] = self.msg

        self.crashed = False
        self.joy_origin = None     # (x, y) em pixels
        self.joy_pos = None
        self.joy_touch = None
        self.attack_touch = None
        self.keys = set()

        self.reset()
        self.bind(size=self._relayout, pos=self._relayout)
        Window.bind(on_key_down=self._on_key_down, on_key_up=self._on_key_up)
        Clock.schedule_interval(self.update, 1.0 / 60.0)

    # ------------------------------------------------------------- estado
    def reset(self, *_):
        self.grid = [list(line) for line in ROOM]
        self.blocks = []
        self.plates = []
        self.enemies = []
        self.exit_cell = None
        self.px = self.py = 1.5

        for r, line in enumerate(self.grid):
            for c, ch in enumerate(line):
                if ch == "B":
                    self.blocks.append(Block(c, r))
                    self.grid[r][c] = "."
                elif ch == "P":
                    self.plates.append((c, r))
                elif ch == "S":
                    self.px, self.py = c + 0.5, r + 0.5
                    self.grid[r][c] = "."
                elif ch == "E":
                    self.enemies.append(Enemy(c, r))
                    self.grid[r][c] = "."
                elif ch == "X":
                    self.exit_cell = (c, r)

        self.hp = MAX_HP
        self.face = (0.0, -1.0)
        self.attack_t = 0.0
        self.invuln = 0.0
        self.push_dir = None
        self.push_t = 0.0
        self.door_open = False
        self.finished = False
        self.msg.text = ""

    # ------------------------------------------------------------- geometria
    @guarda
    def _relayout(self, *_):
        self.tile = min(self.width / float(COLS), self.height / float(ROWS))
        self.ox = self.x + (self.width - self.tile * COLS) / 2.0
        self.oy = self.y + (self.height - self.tile * ROWS) / 2.0
        self.msg.size = (self.width, 40)
        self.msg.text_size = self.msg.size
        self.msg.pos = (self.x, self.y + self.height * 0.72)

    def to_px(self, col, row):
        """Converte coordenada de tile (origem no topo) para pixel do Kivy."""
        return (self.ox + col * self.tile,
                self.oy + (ROWS - 1 - row) * self.tile)

    # ------------------------------------------------------------- colisao
    def solid(self, c, r):
        if c < 0 or r < 0 or c >= COLS or r >= ROWS:
            return True
        ch = self.grid[r][c]
        if ch == "#":
            return True
        if ch == "D" and not self.door_open:
            return True
        return False

    def block_at(self, c, r):
        for b in self.blocks:
            if b.col == c and b.row == r:
                return b
        return None

    def move_axis(self, delta, axis, dt):
        """axis 0 = horizontal, 1 = vertical (em coordenadas de tile, y cresce p/ baixo)."""
        if delta == 0:
            return
        sign = 1 if delta > 0 else -1
        if axis == 0:
            nx = self.px + delta
            edge = nx + sign * PLAYER_HALF
            c = int(math.floor(edge))
            rows = (int(math.floor(self.py - PLAYER_HALF + 0.001)),
                    int(math.floor(self.py + PLAYER_HALF - 0.001)))
            hit_block = None
            blocked = False
            for r in set(rows):
                if self.solid(c, r):
                    blocked = True
                b = self.block_at(c, r)
                if b is not None:
                    blocked = True
                    hit_block = b
            if not blocked:
                self.px = nx
                return
            self.px = c + (0.5 - sign * 0.5) - sign * PLAYER_HALF - sign * 0.001
            self._attempt_push(hit_block, (sign, 0), dt)
        else:
            ny = self.py + delta
            edge = ny + sign * PLAYER_HALF
            r = int(math.floor(edge))
            cols = (int(math.floor(self.px - PLAYER_HALF + 0.001)),
                    int(math.floor(self.px + PLAYER_HALF - 0.001)))
            hit_block = None
            blocked = False
            for c in set(cols):
                if self.solid(c, r):
                    blocked = True
                b = self.block_at(c, r)
                if b is not None:
                    blocked = True
                    hit_block = b
            if not blocked:
                self.py = ny
                return
            self.py = r + (0.5 - sign * 0.5) - sign * PLAYER_HALF - sign * 0.001
            self._attempt_push(hit_block, (0, sign), dt)

    def _attempt_push(self, block, direction, dt):
        if block is None:
            self.push_dir = None
            self.push_t = 0.0
            return
        if self.push_dir != direction:
            self.push_dir = direction
            self.push_t = 0.0
        self.push_t += dt
        if self.push_t < PUSH_DELAY or block.t < 1.0:
            return
        tc = block.col + direction[0]
        tr = block.row + direction[1]
        if self.solid(tc, tr) or self.block_at(tc, tr) is not None:
            return
        block.push_to(tc, tr)
        self.push_t = 0.0

    # ------------------------------------------------------------- loop
    def update(self, dt):
        """Envolve o quadro num try/except: se algo estourar, o erro
        aparece NA TELA do celular em vez do app simplesmente fechar."""
        try:
            self._update(dt)
        except Exception:
            reportar("loop do jogo")
            self.crashed = True
            return False   # para o relogio: nao tenta de novo

    def _update(self, dt):
        if not hasattr(self, "tile"):
            self._relayout()
        dt = min(dt, 1.0 / 30.0)

        dx, dy = self.read_input()
        if dx or dy:
            mag = math.hypot(dx, dy)
            dx, dy = dx / mag, dy / mag
            self.face = (dx, dy)
            if self.attack_t <= 0 and not self.finished:
                self.move_axis(dx * PLAYER_SPEED * dt, 0, dt)
                self.move_axis(dy * PLAYER_SPEED * dt, 1, dt)
        else:
            self.push_dir = None
            self.push_t = 0.0

        for b in self.blocks:
            b.update(dt)

        self.update_enemies(dt)

        if self.attack_t > 0:
            self.attack_t -= dt
            self.resolve_attack()
        if self.invuln > 0:
            self.invuln -= dt

        self.check_puzzle()
        self.check_exit()
        self.draw()

    def read_input(self):
        dx = dy = 0.0
        if self.joy_origin and self.joy_pos:
            vx = self.joy_pos[0] - self.joy_origin[0]
            vy = self.joy_pos[1] - self.joy_origin[1]
            dead = self.tile * 0.35
            if math.hypot(vx, vy) > dead:
                dx, dy = vx, -vy     # y invertido: grid cresce para baixo
        if "left" in self.keys:
            dx -= 1
        if "right" in self.keys:
            dx += 1
        if "up" in self.keys:
            dy -= 1
        if "down" in self.keys:
            dy += 1
        return dx, dy

    def update_enemies(self, dt):
        for e in self.enemies:
            if not e.alive:
                continue
            nx = e.x + e.dir * ENEMY_SPEED * dt
            c = int(math.floor(nx + e.dir * 0.3))
            r = int(math.floor(e.y))
            if self.solid(c, r) or self.block_at(c, r) is not None:
                e.dir *= -1
            else:
                e.x = nx
            if self.invuln <= 0 and not self.finished:
                if abs(e.x - self.px) < 0.6 and abs(e.y - self.py) < 0.6:
                    self.hp -= 1
                    self.invuln = INVULN_TIME
                    kx = self.px - e.x
                    ky = self.py - e.y
                    m = math.hypot(kx, ky) or 1.0
                    self.px += kx / m * 0.5
                    self.py += ky / m * 0.5
                    if self.hp <= 0:
                        self.finished = True
                        self.msg.text = "Voce caiu. Toque duas vezes para reiniciar."

    def attack(self):
        if self.attack_t <= 0 and not self.finished:
            self.attack_t = ATTACK_TIME

    def sword_rect(self):
        fx, fy = self.face
        return (self.px + fx * 0.7, self.py + fy * 0.7, 0.45)

    def resolve_attack(self):
        sx, sy, sr = self.sword_rect()
        for e in self.enemies:
            if e.alive and abs(e.x - sx) < sr and abs(e.y - sy) < sr:
                e.alive = False

    def check_puzzle(self):
        if self.door_open:
            return
        if not self.plates:
            return
        if all(self.block_at(c, r) is not None for c, r in self.plates):
            self.door_open = True
            self.msg.text = "A porta se abriu."
            Clock.schedule_once(lambda *_: setattr(self.msg, "text", ""), 2.0)

    def check_exit(self):
        if self.finished or not self.exit_cell:
            return
        c, r = self.exit_cell
        if int(self.px) == c and int(self.py) == r:
            self.finished = True
            self.msg.text = "Sala concluida. Toque duas vezes para reiniciar."

    # ------------------------------------------------------------- desenho
    def draw(self):
        t = self.tile
        # canvas.before: desenhar em self.canvas e dar clear() apagaria
        # tambem os widgets filhos (o rotulo de mensagens some).
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*C_BG)
            Rectangle(pos=self.pos, size=self.size)

            for r in range(ROWS):
                for c in range(COLS):
                    ch = self.grid[r][c]
                    x, y = self.to_px(c, r)
                    if ch == "#":
                        Color(*C_WALL)
                        Rectangle(pos=(x, y), size=(t, t))
                    else:
                        Color(*C_FLOOR)
                        Rectangle(pos=(x, y), size=(t, t))
                        Color(*C_GRID)
                        Line(rectangle=(x, y, t, t), width=1)

            for c, r in self.plates:
                x, y = self.to_px(c, r)
                on = self.block_at(c, r) is not None
                Color(*(C_PLATE_ON if on else C_PLATE_OFF))
                Line(rectangle=(x + t * 0.18, y + t * 0.18, t * 0.64, t * 0.64),
                     width=max(2, t * 0.05))

            if self.exit_cell:
                x, y = self.to_px(*self.exit_cell)
                Color(*C_EXIT)
                Rectangle(pos=(x + t * 0.2, y + t * 0.2), size=(t * 0.6, t * 0.6))

            for r in range(ROWS):
                for c in range(COLS):
                    if self.grid[r][c] == "D":
                        x, y = self.to_px(c, r)
                        if self.door_open:
                            Color(C_DOOR[0], C_DOOR[1], C_DOOR[2], 0.25)
                            Line(rectangle=(x, y, t, t), width=2)
                        else:
                            Color(*C_DOOR)
                            Rectangle(pos=(x, y), size=(t, t))

            for b in self.blocks:
                x, y = self.to_px(b.vc, b.vr)
                Color(*C_BLOCK)
                Rectangle(pos=(x + t * 0.06, y + t * 0.06), size=(t * 0.88, t * 0.88))

            for e in self.enemies:
                if not e.alive:
                    continue
                x, y = self.to_px(e.x - 0.35, e.y + 0.35)
                Color(*C_ENEMY)
                Ellipse(pos=(x, y), size=(t * 0.7, t * 0.7))

            if self.attack_t > 0:
                sx, sy, sr = self.sword_rect()
                x, y = self.to_px(sx - sr, sy + sr)
                Color(*C_SWORD)
                Rectangle(pos=(x, y), size=(t * sr * 2, t * sr * 2))

            blink = self.invuln > 0 and int(self.invuln * 12) % 2 == 0
            if not blink:
                x, y = self.to_px(self.px - PLAYER_HALF, self.py + PLAYER_HALF)
                Color(*C_PLAYER)
                Rectangle(pos=(x, y), size=(t * PLAYER_HALF * 2, t * PLAYER_HALF * 2))

            self.draw_hud()

    def draw_hud(self):
        t = self.tile
        Color(*C_HUD)
        for i in range(self.hp):
            Ellipse(pos=(self.x + 12 + i * (t * 0.5), self.y + self.height - t * 0.6),
                    size=(t * 0.35, t * 0.35))

        if self.joy_origin and self.joy_pos:
            ox, oy = self.joy_origin
            Color(1, 1, 1, 0.18)
            Ellipse(pos=(ox - t, oy - t), size=(t * 2, t * 2))
            Color(1, 1, 1, 0.35)
            jx, jy = self.joy_pos
            vx, vy = jx - ox, jy - oy
            m = math.hypot(vx, vy)
            if m > t:
                vx, vy = vx / m * t, vy / m * t
            Ellipse(pos=(ox + vx - t * 0.4, oy + vy - t * 0.4), size=(t * 0.8, t * 0.8))

        Color(1, 1, 1, 0.28 if self.attack_t <= 0 else 0.5)
        bx = self.x + self.width - t * 2.2
        by = self.y + t * 0.9
        Ellipse(pos=(bx, by), size=(t * 1.4, t * 1.4))

    # ------------------------------------------------------------- entrada
    @guarda
    def on_touch_down(self, touch):
        if self.finished and touch.is_double_tap:
            self.reset()
            return True
        if touch.x < self.x + self.width / 2:
            self.joy_touch = touch.uid
            self.joy_origin = (touch.x, touch.y)
            self.joy_pos = (touch.x, touch.y)
        else:
            self.attack_touch = touch.uid
            self.attack()
        return True

    @guarda
    def on_touch_move(self, touch):
        if touch.uid == self.joy_touch:
            self.joy_pos = (touch.x, touch.y)
        return True

    @guarda
    def on_touch_up(self, touch):
        if touch.uid == self.joy_touch:
            self.joy_touch = None
            self.joy_origin = None
            self.joy_pos = None
        if touch.uid == self.attack_touch:
            self.attack_touch = None
        return True

    @guarda
    def _on_key_down(self, window, key, *args):
        m = {273: "up", 274: "down", 276: "left", 275: "right",
             119: "up", 115: "down", 97: "left", 100: "right"}
        if key in m:
            self.keys.add(m[key])
        elif key == 32:
            self.attack()
        elif key == 114:
            self.reset()
        return True

    @guarda
    def _on_key_up(self, window, key, *args):
        m = {273: "up", 274: "down", 276: "left", 275: "right",
             119: "up", 115: "down", 97: "left", 100: "right"}
        if key in m:
            self.keys.discard(m[key])
        return True


class NucleoApp(App):
    def build(self):
        Window.clearcolor = C_BG
        try:
            return Game()
        except Exception:
            texto = traceback.format_exc()
            print("FALHA AO CRIAR O JOGO:\n" + texto)
            linhas = [l for l in texto.strip().split("\n") if l.strip()]
            return Label(text="ERRO\n" + "\n".join(linhas[-5:]),
                         font_size="13sp", halign="center",
                         color=(1, 0.5, 0.5, 1))


if __name__ == "__main__":
    NucleoApp().run()
