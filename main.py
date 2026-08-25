# -*- coding: utf-8 -*-
"""
NUCLEO - fatia vertical 0.1 (versao Android/Kivy)

Port do prototipo HTML original. Mantem a mesma logica: grade de 16x11
tiles de 16px (256x176 internos), movimento com aceleracao e freio,
golpe de espada em arco, impulso (dash), fossos, nucleo e 3 salas.

Tudo desenhado por codigo: nenhum arquivo de imagem externo.
"""

import math
import random
import traceback

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import (Color, Ellipse, Line, PopMatrix, PushMatrix,
                           Rectangle, Rotate, Translate)
from kivy.graphics.fbo import Fbo
from kivy.graphics.instructions import Canvas
from kivy.graphics import ClearBuffers, ClearColor
from kivy.graphics.texture import Texture
from kivy.uix.label import Label
from kivy.uix.widget import Widget

# ---------------------------------------------------------------- dimensoes
T = 16
COLS, ROWS = 16, 11
W, H = COLS * T, ROWS * T          # 256 x 176

# ---------------------------------------------------------------- ajuste fino
VEL_MAX = 66.0        # px/s no passo normal
ACEL = 460.0          # px/s2 para ganhar velocidade
FREIO = 1200.0        # px/s2 para parar (freio > aceleracao = parada seca)
ZONA_MORTA = 0.18     # curso do analogico ignorado no centro
CURVA = 1.7           # >1 = inicio do curso anda devagar (precisao)

ATK_DUR = 0.26        # duracao da varredura
ATK_CD = 0.40         # intervalo entre golpes
ATK_ARCO = 2.5        # amplitude do arco em radianos (~143 graus)
ATK_ALC = 19.0        # alcance da lamina em pixels

DASH_DUR = 0.20
DASH_CD = 0.55
DASH_VEL = 290.0

# ---------------------------------------------------------------- salas
#  #  parede    .  piso      B  bloco     P  placa    D  porta
#  H  fosso     C  nucleo    E  inimigo   S  entrada  X  saida
#  F  pedestal final
SALAS = [
    {"nome": "ANTECAMARA",
     "dica": "Empurre os dois blocos ate as placas.",
     "mapa": [
         "#######DD#######",
         "#..............#",
         "#....P....P....#",
         "#..............#",
         "#..............#",
         "#....B....B....#",
         "#..............#",
         "#..............#",
         "#..............#",
         "#..S...........#",
         "################"]},

    {"nome": "GALERIA DOS TORNOS",
     "dica": "Algo guarda o corredor. O nucleo esta no cofre.",
     "mapa": [
         "#######XX#######",
         "#..............#",
         "#....######....#",
         "#....#....#....#",
         "#..E.#.C..#....#",
         "#....#....#....#",
         "#....#....#....#",
         "#....###.##....#",
         "#..............#",
         "#..............#",
         "#######SS#######"]},

    {"nome": "O VAO",
     "dica": "O impulso atravessa o que os pes nao alcancam.",
     "mapa": [
         "#######FF#######",
         "#..............#",
         "#..............#",
         "#.HHHHHHHHHHHH.#",
         "#.HHHHHHHHHHHH.#",
         "#..............#",
         "#..............#",
         "#..............#",
         "#..............#",
         "#..............#",
         "#######SS#######"]},
]

# ---------------------------------------------------------------- paleta
PAL = {
    'k': (20, 17, 28),
    'S': (244, 220, 186), 's': (224, 185, 143), 'z': (176, 128, 91),
    'r': (176, 100, 47),
    'L': (111, 195, 174), 'l': (78, 154, 138), 'c': (47, 111, 99),
    'd': (27, 71, 64),
    'W': (243, 236, 218), 'w': (217, 207, 180), 'v': (158, 145, 121),
    'M': (239, 192, 120), 'm': (201, 138, 62), 'n': (130, 85, 31),
    'B': (107, 82, 54), 'b': (70, 53, 38), 'y': (36, 28, 19),
    'a': (81, 72, 104), 'g': (42, 36, 64), 'e': (224, 90, 69),
}

M_BAIXO = [
    ".....kkkkk......",
    "....kLLLLLk.....",
    "...kLLllllck....",
    "...kLlrrrrck....",
    "...klSsssszk....",
    "...klSksskzk....",
    "...klSsssszk....",
    "....klsszzk.....",
    ".....kzzzk......",
    "..kmMMmmmmmnk...",
    ".kLllWWwwwvlck..",
    ".kLllWwwwwvlck..",
    ".kLllWwwwwvlck..",
    ".kLszWwwwwvszk..",
    "..klmMmmmmnlk...",
    "..klccccccdlk...",
    "..klccccccdck...",
    "...klccccdck....",
    "...kBbk.kBbk....",
    "...kBbk.kBbk....",
    "...kbbk.kbbk....",
    "...kyyk.kyyk....",
]

M_CIMA = [
    ".....kkkkk......",
    "....kLLLLLk.....",
    "...kLLllllck....",
    "...kLllllllck...",
    "...kLllllllck...",
    "...klllllllck...",
    "...kllllllcck...",
    "....krrrrrk.....",
    ".....kzzzk......",
    "..kmMMmmmmmnk...",
    ".kLlllllllllck..",
    ".kLllWllllllck..",
    ".kLlllWlllllck..",
    ".kLszllWlllszk..",
    "..klmMmmmmnlk...",
    "..klccccccdlk...",
    "..klccccccdck...",
    "...klccccdck....",
    "...kBbk.kBbk....",
    "...kBbk.kBbk....",
    "...kbbk.kbbk....",
    "...kyyk.kyyk....",
]

M_LADO = [
    "......kkkkk.....",
    ".....kLLLLlk....",
    "....kLLllllck...",
    "....kLlrrrlck...",
    "....klSssszk....",
    "....klSkszk.....",
    "....klSssszk....",
    ".....klsszk.....",
    ".....kzzzk......",
    "...kmMMmmmnk....",
    "..kLllWwwwvck...",
    "..kLllWwwwvck...",
    "..kLlsWwwwvck...",
    "..kLlszWwwvck...",
    "...klmMmmnlk....",
    "...klccccdlk....",
    "...klccccdck....",
    "....klccdck.....",
    "....kBbbk.......",
    "....kBbbk.......",
    "....kbbbk.......",
    "....kyyyk.......",
]

M_SENT = [
    "...kkkkkk...",
    "..kaaaaaak..",
    ".kaaaaaaaak.",
    ".kaaaaaaaak.",
    ".kaaeeeeaak.",
    ".kaaeeeeaak.",
    ".kaaaaaaaak.",
    ".kaggggggak.",
    ".kaggggggak.",
    "..kggggggk..",
    "..kggggggk..",
    "...kggggk...",
    "....kggk....",
    "....kkkk....",
]

# quadros de caminhada: as quatro linhas de baixo sao redesenhadas
PASSO_A = [(18, "..kBbk...kBbk..."), (19, "..kBbk...kBbk..."),
           (20, "..kbbk...kbbk..."), (21, "..kyyk...kyyk...")]
PASSO_B = [(18, "....kBbkBbk....."), (19, "....kBbkBbk....."),
           (20, "....kbbkbbk....."), (21, "....kyykyyk.....")]
LADO_A = [(18, "..kBbk..kBbk...."), (19, "..kBbk..kBbk...."),
          (20, "..kbbk..kbbk...."), (21, "..kyyk..kyyk....")]
LADO_B = [(18, "....kBbbk......."), (19, "....kBbbk......."),
          (20, "....kbbbk......."), (21, "....kyyyk.......")]


def com_linhas(mapa, pares):
    """Devolve copia do mapa com algumas linhas substituidas."""
    novo = list(mapa)
    for i, linha in pares:
        novo[i] = linha
    return novo


def montar_textura(mapa, branco=False):
    """Converte um mapa de caracteres em textura RGBA com filtro nearest.

    A textura do Kivy tem origem embaixo; o mapa e de cima para baixo,
    entao as linhas sao invertidas na hora de escrever o buffer.
    """
    alt = len(mapa)
    larg = len(mapa[0])
    buf = bytearray(larg * alt * 4)
    for r in range(alt):
        linha = mapa[r]
        for c in range(larg):
            ch = linha[c]
            if ch == '.':
                continue
            if branco:
                cor = (154, 147, 176) if ch == 'k' else (255, 255, 255)
            else:
                cor = PAL.get(ch)
                if cor is None:
                    continue
            i = ((alt - 1 - r) * larg + c) * 4
            buf[i] = cor[0]
            buf[i + 1] = cor[1]
            buf[i + 2] = cor[2]
            buf[i + 3] = 255
    tex = Texture.create(size=(larg, alt), colorfmt='rgba')
    tex.blit_buffer(bytes(buf), colorfmt='rgba', bufferfmt='ubyte')
    tex.mag_filter = 'nearest'
    tex.min_filter = 'nearest'
    return tex


def textura_radial(raio, cor, alfa_centro, expoente=1.6):
    """Disco com alfa caindo do centro para a borda.

    Substitui o gradiente radial do canvas: serve para a luz das tochas,
    o brilho do nucleo e a vinheta (esta com o alfa invertido).
    """
    n = raio * 2
    buf = bytearray(n * n * 4)
    for y in range(n):
        for x in range(n):
            dx = x - raio + 0.5
            dy = y - raio + 0.5
            d = math.hypot(dx, dy) / raio
            a = 0.0 if d >= 1.0 else alfa_centro * ((1.0 - d) ** expoente)
            i = (y * n + x) * 4
            buf[i] = cor[0]
            buf[i + 1] = cor[1]
            buf[i + 2] = cor[2]
            buf[i + 3] = int(a * 255)
    tex = Texture.create(size=(n, n), colorfmt='rgba')
    tex.blit_buffer(bytes(buf), colorfmt='rgba', bufferfmt='ubyte')
    return tex


def textura_vinheta(n=96, alfa_borda=0.34):
    """Escurece as bordas da tela; transparente no centro."""
    buf = bytearray(n * n * 4)
    meio = n / 2.0
    for y in range(n):
        for x in range(n):
            d = math.hypot(x - meio + 0.5, y - meio + 0.5) / meio
            a = 0.0 if d < 0.42 else min(1.0, (d - 0.42) / 0.58) * alfa_borda
            i = (y * n + x) * 4
            buf[i] = 6
            buf[i + 1] = 5
            buf[i + 2] = 12
            buf[i + 3] = int(a * 255)
    tex = Texture.create(size=(n, n), colorfmt='rgba')
    tex.blit_buffer(bytes(buf), colorfmt='rgba', bufferfmt='ubyte')
    return tex


def hash_tile(c, r):
    return ((c * 73856093) ^ (r * 19349663)) & 0xFFFFFFFF


class Bloco(object):
    __slots__ = ('c', 'r', 'px', 'py', 'mov')

    def __init__(self, c, r):
        self.c, self.r = c, r
        self.px, self.py = c * T, r * T
        self.mov = None      # (px0, py0, px1, py1, t)


class Inimigo(object):
    __slots__ = ('x', 'y', 'hp', 'dir', 'vel', 'hit')

    def __init__(self, c, r):
        self.x = c * T + 8
        self.y = r * T + 8
        self.hp = 2
        self.dir = 1
        self.vel = 22.0
        self.hit = 0.0


class Faisca(object):
    __slots__ = ('x', 'y', 'vx', 'vy', 't', 'm')

    def __init__(self, x, y):
        a = random.random() * 6.283
        v = 34 + random.random() * 76
        self.m = 0.14 + random.random() * 0.18
        self.x, self.y = x, y
        self.vx = math.cos(a) * v
        self.vy = math.sin(a) * v
        self.t = self.m


class Jogo(Widget):

    # =================================================== ciclo de vida
    def __init__(self, **kw):
        super(Jogo, self).__init__(**kw)

        self.escala = 1.0
        self.ox = self.oy = 0.0
        self.fbo = None
        self.tex_cenario = None

        self.sprites = {}
        self._preparar_sprites()
        self.tex_luz = textura_radial(48, (255, 196, 118), 0.34)
        self.tex_nucleo = textura_radial(30, (110, 224, 198), 0.26)
        self.tex_vinheta = textura_vinheta()

        self.rotulo = Label(text="", font_size="11sp", halign="center",
                            color=(0.90, 0.886, 0.94, 1))
        self.add_widget(self.rotulo)

        # controles de toque
        self.stick_id = None
        self.stick_centro = (0.0, 0.0)
        self.tx = self.ty = 0.0
        self.botao_golpe = False
        self.botao_imp = False
        self.toques_botao = {}
        self.teclas = set()

        self.tem_impulso = False
        self.sala_idx = 0
        self.fim = False
        self.msg = ""
        self.msg_t = 0.0
        self.tremor = 0.0
        self.pausa = 0.0
        self.faiscas = []
        self.push_timer = 0.0
        self.push_dir = None

        self.carregar(0)
        self._montar_camadas()

        Window.bind(on_key_down=self._tecla_desce, on_key_up=self._tecla_sobe)
        self.bind(size=self._relayout, pos=self._relayout)
        Clock.schedule_interval(self.laco, 1.0 / 60.0)

    def _preparar_sprites(self):
        self.sprites['baixo'] = [montar_textura(M_BAIXO),
                                 montar_textura(com_linhas(M_BAIXO, PASSO_A)),
                                 montar_textura(com_linhas(M_BAIXO, PASSO_B))]
        self.sprites['cima'] = [montar_textura(M_CIMA),
                                montar_textura(com_linhas(M_CIMA, PASSO_A)),
                                montar_textura(com_linhas(M_CIMA, PASSO_B))]
        self.sprites['lado'] = [montar_textura(M_LADO),
                                montar_textura(com_linhas(M_LADO, LADO_A)),
                                montar_textura(com_linhas(M_LADO, LADO_B))]
        self.sprites['sent'] = montar_textura(M_SENT)
        self.sprites['sent_flash'] = montar_textura(M_SENT, branco=True)

    # =================================================== carga de sala
    def carregar(self, i):
        self.sala_idx = i
        sala = SALAS[i]
        self.grade = [list(l) for l in sala["mapa"]]
        self.blocos = []
        self.placas = []
        self.inimigos = []
        self.nucleo = None
        self.porta_aberta = False
        self.entrada = (T + 8, T + 9)

        for r in range(ROWS):
            for c in range(COLS):
                ch = self.grade[r][c]
                if ch == 'B':
                    self.blocos.append(Bloco(c, r))
                    self.grade[r][c] = '.'
                elif ch == 'P':
                    self.placas.append((c, r))
                elif ch == 'E':
                    self.inimigos.append(Inimigo(c, r))
                    self.grade[r][c] = '.'
                elif ch == 'C':
                    self.nucleo = (c * T + 8, r * T + 8)
                    self.grade[r][c] = '.'
                elif ch == 'S':
                    self.entrada = (c * T + 8, r * T + 9)
                    self.grade[r][c] = '.'

        # estado do jogador
        self.px, self.py = self.entrada
        self.vx = self.vy = 0.0
        self.passo = 0.0
        self.dir = 2                      # 0 cima, 1 direita, 2 baixo, 3 esq
        if not hasattr(self, 'hp'):
            self.hp = 3
        self.inv = 0.0
        self.dash_t = 0.0
        self.dash_cd = 0.0
        self.dvx = self.dvy = 0.0
        self.atk = 0.0
        self.atk_cd = 0.0
        self.atk_dir = 2
        self.atk_lado = 1
        self.atingiu = []
        self.cai = 0.0

        self.faiscas = []
        self.msg = sala["dica"]
        self.msg_t = 4.2
        self.tochas = []
        self.cenario_sujo = True

    # =================================================== consultas
    def tile(self, c, r):
        if c < 0 or r < 0 or c >= COLS or r >= ROWS:
            return '#'
        return self.grade[r][c]

    def bloco_em(self, c, r):
        for b in self.blocos:
            if b.c == c and b.r == r and b.mov is None:
                return b
        return None

    def solido(self, c, r):
        t = self.tile(c, r)
        if t == '#':
            return True
        if t == 'D' and not self.porta_aberta:
            return True
        if self.bloco_em(c, r):
            return True
        return False

    def fosso_em(self, px, py):
        return self.tile(int(px // T), int(py // T)) == 'H'

    def colide(self, nx, ny):
        hw, hh = 5.0, 5.5
        c0 = int(math.floor((nx - hw) / T))
        c1 = int(math.floor((nx + hw - 0.01) / T))
        r0 = int(math.floor((ny - hh) / T))
        r1 = int(math.floor((ny + hh - 0.01) / T))
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if self.solido(c, r):
                    return True
        return False

    # =================================================== assistencias
    @staticmethod
    def aproxima(v, alvo, passo):
        if v < alvo:
            return min(v + passo, alvo)
        return max(v - passo, alvo)

    @staticmethod
    def alinha(v, dt):
        """Puxa o personagem para o centro do corredor, suavemente."""
        centro = math.floor(v / T) * T + T / 2.0
        d = centro - v
        if abs(d) < 0.4 or abs(d) > 5.5:
            return v
        return v + math.copysign(min(abs(d), 34 * dt), d)

    def alvo_adiante(self, dir_c, dir_r):
        """O alinhamento so age quando ha algo a frente que exige pontaria."""
        c0 = int(self.px // T)
        r0 = int(self.py // T)
        for i in (1, 2):
            c, r = c0 + dir_c * i, r0 + dir_r * i
            t = self.tile(c, r)
            if t == '#':
                return False
            if t in ('D', 'X', 'F', 'P') or self.bloco_em(c, r):
                return True
        return False

    def escape_quina(self, nx, ny, eixo_x):
        """Desliza 1-4 px para contornar quina em vez de travar."""
        for off in (1, 2, 3, 4):
            if eixo_x:
                if not self.colide(nx, ny - off):
                    return ny - off
                if not self.colide(nx, ny + off):
                    return ny + off
            else:
                if not self.colide(nx - off, ny):
                    return nx - off
                if not self.colide(nx + off, ny):
                    return nx + off
        return None

    def tentar_empurrar(self, dx, dy, dt):
        dir_c = 0 if dx == 0 else (1 if dx > 0 else -1)
        dir_r = 0 if dy == 0 else (1 if dy > 0 else -1)
        if not dir_c and not dir_r:
            self.push_timer = 0.0
            return
        fc = int((self.px + dir_c * 8.0) // T)
        fr = int((self.py + dir_r * 8.5) // T)
        b = self.bloco_em(fc, fr)
        if b is None:
            self.push_timer = 0.0
            self.push_dir = None
            return
        chave = (dir_c, dir_r)
        if self.push_dir != chave:
            self.push_dir = chave
            self.push_timer = 0.0
        self.push_timer += dt
        if self.push_timer > 0.18:
            nc, nr = b.c + dir_c, b.r + dir_r
            if not self.solido(nc, nr) and self.tile(nc, nr) != 'H':
                b.mov = [b.px, b.py, nc * T, nr * T, 0.0]
                b.c, b.r = nc, nr
            self.push_timer = 0.0

    def angulo_golpe(self):
        base = (-math.pi / 2, 0.0, math.pi / 2, math.pi)[self.atk_dir]
        k = 1.0 - self.atk / ATK_DUR
        e = 2 * k * k if k < 0.5 else 1 - ((-2 * k + 2) ** 2) / 2
        return base + self.atk_lado * (-ATK_ARCO / 2 + ATK_ARCO * e)

    def faiscar(self, x, y):
        for _ in range(8):
            self.faiscas.append(Faisca(x, y))

    def dano(self, n):
        self.hp -= n
        self.inv = 1.1
        if self.hp <= 0:
            self.hp = 3
            self.carregar(self.sala_idx)
            self.msg = "Voce caiu. A sala foi reposta."
            self.msg_t = 3.0

    # =================================================== laco
    def laco(self, dt):
        try:
            dt = max(0.0, min(0.05, dt))
            if self.pausa > 0:
                self.pausa -= dt
            else:
                self.atualizar(dt)
            self.desenhar()
        except Exception:
            texto = traceback.format_exc()
            print("ERRO NO LACO:\n" + texto)
            linhas = [l for l in texto.strip().split("\n") if l.strip()]
            self.rotulo.text = "ERRO\n" + "\n".join(linhas[-4:])
            return False

    def entrada_direcao(self):
        kx = ky = 0.0
        if 'left' in self.teclas:
            kx -= 1
        if 'right' in self.teclas:
            kx += 1
        if 'up' in self.teclas:
            ky -= 1
        if 'down' in self.teclas:
            ky += 1
        km = math.hypot(kx, ky)
        if km > 1:
            kx, ky = kx / km, ky / km

        dx, dy = kx, ky
        tm = math.hypot(self.tx, self.ty)
        if not km and tm > ZONA_MORTA:
            f = ((tm - ZONA_MORTA) / (1 - ZONA_MORTA)) ** CURVA
            dx = (self.tx / tm) * f
            dy = (self.ty / tm) * f
        m = math.hypot(dx, dy)
        if m > 1:
            dx, dy = dx / m, dy / m
        return dx, dy, m

    def atualizar(self, dt):
        if self.fim:
            return

        dx, dy, m = self.entrada_direcao()
        if m > 0.25:
            if abs(dx) > abs(dy):
                self.dir = 1 if dx > 0 else 3
            else:
                self.dir = 2 if dy > 0 else 0

        self.dash_cd = max(0.0, self.dash_cd - dt)
        self.atk_cd = max(0.0, self.atk_cd - dt)
        self.atk = max(0.0, self.atk - dt)
        self.inv = max(0.0, self.inv - dt)

        # impulso
        if (self.botao_imp and self.tem_impulso
                and self.dash_cd <= 0 and self.dash_t <= 0):
            v = ((0, -1), (1, 0), (0, 1), (-1, 0))[self.dir]
            self.dvx = dx if (dx or dy) else v[0]
            self.dvy = dy if (dx or dy) else v[1]
            n = math.hypot(self.dvx, self.dvy) or 1.0
            self.dvx /= n
            self.dvy /= n
            self.dash_t = DASH_DUR
            self.dash_cd = DASH_CD

        # golpe
        if (self.botao_golpe and self.atk_cd <= 0
                and self.dash_t <= 0 and self.cai <= 0):
            self.atk = ATK_DUR
            self.atk_cd = ATK_CD
            self.atk_dir = self.dir
            self.atk_lado *= -1
            self.atingiu = []

        # velocidade
        if self.dash_t > 0:
            self.vx = self.dvx * DASH_VEL
            self.vy = self.dvy * DASH_VEL
        elif self.cai > 0:
            self.vx = self.vy = 0.0
        else:
            freio = 0.40 if self.atk > 0 else 1.0
            self.vx = self.aproxima(self.vx, dx * VEL_MAX * freio,
                                    (ACEL if dx else FREIO) * dt)
            self.vy = self.aproxima(self.vy, dy * VEL_MAX * freio,
                                    (ACEL if dy else FREIO) * dt)

        # alinhamento contextual
        if self.dash_t <= 0:
            if abs(dx) > 0.5 and abs(dy) < 0.25 and \
                    self.alvo_adiante(1 if dx > 0 else -1, 0):
                self.py = self.alinha(self.py, dt)
            if abs(dy) > 0.5 and abs(dx) < 0.25 and \
                    self.alvo_adiante(0, 1 if dy > 0 else -1):
                self.px = self.alinha(self.px, dt)

        # eixo X primeiro; o desvio de quina altera py, por isso o passo
        # vertical so pode ser calculado depois
        nx = self.px + self.vx * dt
        if not self.colide(nx, self.py):
            self.px = nx
        else:
            e = self.escape_quina(nx, self.py, True) if abs(self.vx) > 4 else None
            if e is not None:
                self.px, self.py = nx, e
            else:
                self.vx = 0.0
                if self.dash_t <= 0:
                    self.tentar_empurrar(dx, 0, dt)

        ny = self.py + self.vy * dt
        if not self.colide(self.px, ny):
            self.py = ny
        else:
            e = self.escape_quina(self.px, ny, False) if abs(self.vy) > 4 else None
            if e is not None:
                self.px, self.py = e, ny
            else:
                self.vy = 0.0
                if self.dash_t <= 0:
                    self.tentar_empurrar(0, dy, dt)

        if not dx and not dy:
            self.push_timer = 0.0

        self.passo += math.hypot(self.vx, self.vy) * dt
        self.tremor = max(0.0, self.tremor - dt * 15)

        for f in self.faiscas[:]:
            f.t -= dt
            f.x += f.vx * dt
            f.y += f.vy * dt
            f.vx *= 0.90
            f.vy *= 0.90
            if f.t <= 0:
                self.faiscas.remove(f)

        if self.dash_t > 0:
            self.dash_t -= dt

        # fosso
        if (self.cai <= 0 and self.dash_t <= 0
                and self.fosso_em(self.px, self.py)
                and self.fosso_em(self.px, self.py + 3)):
            self.cai = 0.55
        if self.cai > 0:
            self.cai -= dt
            if self.cai <= 0:
                self.dano(1)
                self.px, self.py = self.entrada

        # blocos em movimento
        for b in self.blocos:
            if b.mov:
                b.mov[4] += dt / 0.14
                k = min(1.0, b.mov[4])
                b.px = b.mov[0] + (b.mov[2] - b.mov[0]) * k
                b.py = b.mov[1] + (b.mov[3] - b.mov[1]) * k
                if k >= 1.0:
                    b.px, b.py = b.mov[2], b.mov[3]
                    b.mov = None

        # placas e porta
        if self.placas:
            self.porta_aberta = all(
                any(b.c == c and b.r == r and b.mov is None
                    for b in self.blocos)
                for c, r in self.placas)

        # nucleo
        if self.nucleo and math.hypot(self.px - self.nucleo[0],
                                      self.py - self.nucleo[1]) < 11:
            self.nucleo = None
            self.tem_impulso = True
            self.msg = "N-01 IMPULSO adquirido - atravesse o intransponivel."
            self.msg_t = 4.0

        self.atualizar_inimigos(dt)

        # transicoes
        tc, tr = int(self.px // T), int(self.py // T)
        aqui = self.tile(tc, tr)
        if aqui == 'X' or (aqui == 'D' and self.porta_aberta):
            if self.sala_idx < len(SALAS) - 1:
                self.carregar(self.sala_idx + 1)
                return
        if aqui == 'F':
            self.fim = True

        if self.msg_t > 0:
            self.msg_t -= dt

    def atualizar_inimigos(self, dt):
        for e in self.inimigos:
            if e.hp <= 0:
                continue
            e.hit = max(0.0, e.hit - dt)
            ny2 = e.y + e.dir * e.vel * dt
            c = int(e.x // T)
            r = int((ny2 + (7 if e.dir > 0 else -7)) // T)
            if self.solido(c, r) or self.tile(c, r) == 'H':
                e.dir *= -1
            else:
                e.y = ny2

            if self.atk > 0 and e not in self.atingiu:
                ang = self.angulo_golpe()
                vx2 = e.x - self.px
                vy2 = e.y - (self.py - 2)
                d = math.hypot(vx2, vy2)
                if 2 < d < ATK_ALC:
                    da = math.atan2(vy2, vx2) - ang
                    while da > math.pi:
                        da -= 6.283
                    while da < -math.pi:
                        da += 6.283
                    if abs(da) < 0.62:
                        e.hp -= 1
                        e.hit = 0.4
                        self.atingiu.append(e)
                        e.x += vx2 / d * 5
                        e.y += vy2 / d * 5
                        self.tremor = 2.4
                        self.pausa = 0.055
                        self.faiscar(self.px + math.cos(ang) * 12,
                                     self.py - 2 + math.sin(ang) * 12)

            if (e.hp > 0 and self.inv <= 0
                    and abs(e.x - self.px) < 11 and abs(e.y - self.py) < 11):
                self.dano(1)


def hexa(s, a=1.0):
    return (int(s[1:3], 16) / 255.0, int(s[3:5], 16) / 255.0,
            int(s[5:7], 16) / 255.0, a)


# ------------------------------------------------------------- geometria
def _relayout(self, *_):
    """Escala inteira sempre que possivel: pixel art nao gosta de fracao."""
    self.escala = min(self.width / float(W), self.height / float(H))
    self.ox = self.x + (self.width - W * self.escala) / 2.0
    self.oy = self.y + (self.height - H * self.escala) / 2.0
    lado = self.width * 0.5
    self.rotulo.size = (lado * 1.4, 30)
    self.rotulo.text_size = self.rotulo.size
    self.rotulo.pos = (self.center_x - lado * 0.7, self.oy + 4)


def _rect(self, x, y, w, h):
    """Retangulo em coordenadas do jogo (y para baixo) -> tela do Kivy."""
    s = self.escala
    return ((self.ox + x * s, self.oy + (H - y - h) * s), (w * s, h * s))


def _cor_rect(self, cor, x, y, w, h):
    Color(*cor)
    pos, size = self._rect(x, y, w, h)
    Rectangle(pos=pos, size=size)


def _sprite(self, tex, x, y, espelha=False, escala=1.0):
    """Desenha com o pe apoiado em (x, y), espelhando se olhar a esquerda."""
    if tex is None:
        return
    lg, al = tex.width, tex.height * escala
    base = y + 6 * escala
    pos, size = self._rect(x - lg / 2.0, base - al, lg, al)
    if espelha:
        coords = (1, 0, 0, 0, 0, 1, 1, 1)
        Rectangle(texture=tex, pos=pos, size=size, tex_coords=coords)
    else:
        Rectangle(texture=tex, pos=pos, size=size)


# ------------------------------------------------------------- cenario
def _fr(self, cor, x, y, w, h):
    """Retangulo dentro do FBO do cenario (1:1 com os pixels internos)."""
    Color(*cor)
    Rectangle(pos=(x, H - y - h), size=(w, h))


def pinta_piso(self, c, r):
    x, y = c * T, r * T
    h = hash_tile(c, r)
    self._fr(hexa(('#2E2B3D', '#322F44', '#2A2739', '#353149')[h % 4]),
             x, y, T, T)
    # junta entre lajes: sombra embaixo e a direita, luz em cima e a esquerda
    self._fr((0, 0, 0, 0.24), x, y + 15, T, 1)
    self._fr((0, 0, 0, 0.24), x + 15, y, 1, T)
    self._fr((1, 1, 1, 0.05), x, y, T, 1)
    self._fr((1, 1, 1, 0.05), x, y, 1, T)

    d = h % 13                                   # desgaste da pedra
    if d == 0:
        self._fr(hexa('#262336'), x + 4, y + 6, 5, 1)
        self._fr(hexa('#262336'), x + 8, y + 7, 3, 1)
    elif d == 1:
        self._fr(hexa('#3B3654'), x + 10, y + 3, 2, 2)
        self._fr(hexa('#3B3654'), x + 3, y + 11, 1, 1)
    elif d == 2:
        self._fr(hexa('#2F4A3E'), x + 2, y + 12, 4, 2)
        self._fr(hexa('#2F4A3E'), x + 6, y + 13, 2, 1)
    elif d == 3:
        for i in range(4):
            self._fr(hexa('#272334'), x + 3 + i * 3, y + 9, 1, 1)
    elif d == 4:
        self._fr(hexa('#252132'), x + 9, y + 9, 4, 4)      # ralo
        self._fr(hexa('#1D1A28'), x + 10, y + 10, 1, 2)
        self._fr(hexa('#1D1A28'), x + 12, y + 10, 1, 2)

    # sombra projetada pela parede: e o que da altura ao mundo
    if self.tile(c, r - 1) == '#':
        self._fr((0, 0, 0, 0.34), x, y, T, 2)
        self._fr((0, 0, 0, 0.18), x, y + 2, T, 2)
        self._fr((0, 0, 0, 0.07), x, y + 4, T, 2)
    if self.tile(c - 1, r) == '#':
        self._fr((0, 0, 0, 0.20), x, y, 2, T)
    if self.tile(c + 1, r) == '#':
        self._fr((0, 0, 0, 0.12), x + 14, y, 2, T)


def pinta_parede(self, c, r):
    x, y = c * T, r * T
    h = hash_tile(c, r)
    if self.tile(c, r + 1) != '#':                # face frontal
        self._fr(hexa('#3A3348'), x, y, T, T)
        self._fr(hexa('#565069'), x, y, T, 4)     # coroamento
        self._fr(hexa('#6C6482'), x, y, T, 1)
        self._fr(hexa('#242030'), x, y + 4, T, 1)
        self._fr(hexa('#312B3E'), x, y + 9, T, 1)
        j = 4 if (h % 2) else 11                  # fiadas de blocos
        self._fr(hexa('#312B3E'), x + j, y + 5, 1, 4)
        self._fr(hexa('#312B3E'), x + ((j + 7) % 15) + 1, y + 10, 1, 5)
        if h % 9 == 0:
            self._fr(hexa('#2A2536'), x + 5, y + 6, 4, 1)
        self._fr(hexa('#1B1724'), x, y + 14, T, 2)   # rodape em sombra
    else:                                          # topo / teto
        self._fr(hexa('#201C2A'), x, y, T, T)
        if h % 7 == 0:
            self._fr(hexa('#292435'), x + 3, y + 4, 6, 2)
        if h % 7 == 1:
            self._fr(hexa('#181521'), x + 8, y + 9, 5, 2)
    if self.tile(c - 1, r) != '#':
        self._fr((0, 0, 0, 0.26), x, y, 2, T)
    if self.tile(c + 1, r) != '#':
        self._fr((0, 0, 0, 0.26), x + 14, y, 2, T)


def pinta_fosso(self, c, r):
    x, y = c * T, r * T
    self._fr(hexa('#07060C'), x, y, T, T)
    if self.tile(c, r - 1) != 'H':                # labio de pedra em cima
        self._fr(hexa('#3A3348'), x, y, T, 3)
        self._fr(hexa('#565069'), x, y, T, 1)
        self._fr(hexa('#100E17'), x, y + 3, T, 4)
    if self.tile(c, r + 1) != 'H':
        self._fr(hexa('#1A1723'), x, y + 13, T, 3)
    if self.tile(c - 1, r) != 'H':
        self._fr(hexa('#131120'), x, y, 2, T)
    if self.tile(c + 1, r) != 'H':
        self._fr(hexa('#131120'), x + 14, y, 2, T)


def pintar_cenario(self):
    """Pinta a sala uma unica vez num buffer fora de tela.

    No laco so se copia a imagem pronta: detalhe por tile sem custo
    por quadro.
    """
    self.tochas = []
    self.fbo = Fbo(size=(W, H))
    with self.fbo:
        ClearColor(0, 0, 0, 0)
        ClearBuffers()
    with self.fbo:
        for r in range(ROWS):
            for c in range(COLS):
                t = self.grade[r][c]
                if t == '#':
                    self.pinta_parede(c, r)
                elif t == 'H':
                    self.pinta_fosso(c, r)
                else:
                    self.pinta_piso(c, r)
                    if t == 'F':                  # pedestal do fim
                        x, y = c * T, r * T
                        self._fr(hexa('#1B1724'), x + 2, y + 5, 12, 10)
                        self._fr(hexa('#3B3654'), x + 2, y + 4, 12, 10)
                        self._fr(hexa('#4A4468'), x + 2, y + 4, 12, 2)
                        self._fr(hexa('#C98A3E'), x + 5, y + 1, 6, 4)
                        self._fr(hexa('#F2D9A0'), x + 6, y + 2, 4, 1)

        # suportes de tocha: espacados e deterministicos
        for r in range(ROWS):
            for c in range(1, COLS - 1):
                if self.grade[r][c] != '#' or self.tile(c, r + 1) == '#':
                    continue
                if self.tile(c, r + 1) in ('D', 'X'):
                    continue
                if c % 5 != 2 or hash_tile(c, r) % 3 == 0:
                    continue
                x, y = c * T + 8, r * T + 10
                self._fr(hexa('#1B1724'), x - 2, y - 1, 4, 5)
                self._fr(hexa('#8A5D28'), x - 2, y - 2, 4, 4)
                self._fr(hexa('#C98A3E'), x - 2, y - 2, 4, 1)
                self.tochas.append((x, y - 4, hash_tile(c, r) % 100))

    self.fbo.draw()
    self.tex_cenario = self.fbo.texture
    self.tex_cenario.mag_filter = 'nearest'
    self.tex_cenario.min_filter = 'nearest'
    self.cenario_sujo = False


# ------------------------------------------------------------- quadro
def _montar_camadas(self):
    """Tres camadas: estatica (refeita so quando muda), dinamica (por
    quadro) e interface. Evita reconstruir ~100 instrucoes 60x por
    segundo, que era o gargalo."""
    self.c_est = Canvas()
    self.c_din = Canvas()
    self.c_ui = Canvas()
    self.canvas.before.add(PushMatrix())
    self.tr_tremor = Translate(0, 0, 0)
    self.canvas.before.add(self.tr_tremor)
    self.canvas.before.add(self.c_est)
    self.canvas.before.add(self.c_din)
    self.c_luz = Canvas()
    self.canvas.before.add(self.c_luz)
    self.canvas.before.add(PopMatrix())
    self.canvas.before.add(self.c_ui)
    self._assin_est = None


def _assinatura_estatica(self):
    """Muda quando algo da camada estatica precisa ser repintado."""
    return (self.sala_idx, self.porta_aberta, round(self.escala, 3),
            round(self.ox, 1), round(self.oy, 1),
            tuple(any(b.c == c and b.r == r and b.mov is None
                      for b in self.blocos) for c, r in self.placas))


def desenhar(self):
    if not self.escala:
        return
    if self.cenario_sujo or self.tex_cenario is None:
        self.pintar_cenario()
        self._assin_est = None

    # --- camada estatica: so quando algo realmente mudou ---
    assin = self._assinatura_estatica()
    if assin != self._assin_est:
        self._assin_est = assin
        self.c_est.clear()
        with self.c_est:
            Color(0.07, 0.066, 0.10, 1)
            Rectangle(pos=self.pos, size=self.size)
            Color(1, 1, 1, 1)
            pos, size = self._rect(0, 0, W, H)
            Rectangle(texture=self.tex_cenario, pos=pos, size=size)
            self._desenhar_placas()
            self._desenhar_portas()
        self.c_luz.clear()
        with self.c_luz:
            self._desenhar_halos()

    # --- tremor: desloca as camadas do mundo, nao a interface ---
    if self.tremor > 0.06:
        self.tr_tremor.x = round((random.random() - 0.5) * self.tremor) * self.escala
        self.tr_tremor.y = round((random.random() - 0.5) * self.tremor) * self.escala
    elif self.tr_tremor.x or self.tr_tremor.y:
        self.tr_tremor.x = self.tr_tremor.y = 0

    # --- camada dinamica ---
    self.c_din.clear()
    with self.c_din:
        self._desenhar_blocos()
        self._desenhar_nucleo()
        self._desenhar_inimigos()
        self._desenhar_jogador()
        self._desenhar_faiscas()
        self._desenhar_tochas()

    # --- interface: vinheta, vitalidade e controles ---
    self.c_ui.clear()
    with self.c_ui:
        Color(1, 1, 1, 1)
        pos, size = self._rect(0, 0, W, H)
        Rectangle(texture=self.tex_vinheta, pos=pos, size=size)
        self._desenhar_hud()
        self._desenhar_controles()

    self.rotulo.text = self.msg if self.msg_t > 0 else ""
    if self.fim:
        self.rotulo.text = "FIM DA FATIA VERTICAL"


def _desenhar_placas(self):
    for c, r in self.placas:
        ligada = any(b.c == c and b.r == r and b.mov is None
                     for b in self.blocos)
        x, y = c * T, r * T
        self._cor_rect(hexa('#1A1724'), x + 2, y + 3, 12, 11)
        self._cor_rect(hexa('#332E48'), x + 2, y + 2, 12, 11)
        self._cor_rect(hexa('#413B5C'), x + 2, y + 2, 12, 1)
        self._cor_rect(hexa('#2F6F63' if ligada else '#272338'),
                       x + 4, y + 4, 8, 7)
        if ligada:
            self._cor_rect(hexa('#7FD8C4'), x + 5, y + 5, 6, 5)
            brilho = 0.20 + 0.10 * math.sin(Clock.get_boottime() * 4.5)
            self._cor_rect(hexa('#7FD8C4', brilho), x + 1, y + 1, 14, 13)
        else:
            self._cor_rect(hexa('#1E1B2B'), x + 5, y + 5, 6, 5)


def _desenhar_portas(self):
    for r in range(ROWS):
        for c in range(COLS):
            t = self.grade[r][c]
            if t not in ('D', 'X'):
                continue
            x, y = c * T, r * T
            aberta = (t == 'X') or self.porta_aberta
            self._cor_rect(hexa('#0A0910'), x, y, T, T)
            if not aberta:
                self._cor_rect(hexa('#6B5230'), x, y + 2, T, 12)
                self._cor_rect(hexa('#C98A3E'), x, y + 2, T, 2)
                self._cor_rect(hexa('#C98A3E'), x, y + 11, T, 1)
                self._cor_rect(hexa('#8A6A3C'), x + 7, y + 4, 2, 7)
            else:
                self._cor_rect(hexa('#3A2C1A'), x, y, T, 3)


def _desenhar_blocos(self):
    for b in self.blocos:
        x, y = b.px, b.py
        Color(0, 0, 0, 0.34)
        pos, size = self._rect(x + 1, y + 12.5, 14, 5)
        Ellipse(pos=pos, size=size)
        self._cor_rect(hexa('#5E4522'), x + 1, y + 1, 14, 14)
        self._cor_rect(hexa('#7A5B2E'), x + 1, y + 1, 14, 12)
        self._cor_rect(hexa('#9C7538'), x + 1, y + 1, 14, 1)
        self._cor_rect(hexa('#3E2D16'), x + 1, y + 14, 14, 1)
        self._cor_rect(hexa('#5E4522'), x + 1, y + 7, 14, 1)
        self._cor_rect(hexa('#8A6A3C'), x + 1, y + 8, 14, 1)
        for bx in (2, 12):
            for by in (2, 11):
                self._cor_rect(hexa('#C98A3E'), x + bx, y + by, 2, 2)
                self._cor_rect(hexa('#E0AE6A'), x + bx, y + by, 1, 1)


def _desenhar_nucleo(self):
    if not self.nucleo:
        return
    t = Clock.get_boottime() * 2.63
    fl = math.sin(t) * 2
    nx, ny = self.nucleo[0], self.nucleo[1] + fl
    Color(1, 1, 1, 1)
    pos, size = self._rect(nx - 30, ny - 30, 60, 60)
    Rectangle(texture=self.tex_nucleo, pos=pos, size=size)
    # losango
    Color(*hexa('#4E9A8A'))
    pos, size = self._rect(nx - 5, ny - 6, 10, 12)
    Ellipse(pos=pos, size=size, segments=4)
    self._cor_rect(hexa('#BFF3E4'), nx - 1, ny - 3, 2, 6)


def _desenhar_inimigos(self):
    for e in self.inimigos:
        if e.hp <= 0:
            continue
        bob = math.sin(Clock.get_boottime() * 2.3 + e.y) * 1.5
        Color(0, 0, 0, 0.28)
        pos, size = self._rect(e.x - 7, e.y + 5.5, 14, 5)
        Ellipse(pos=pos, size=size)
        Color(1, 1, 1, 1)
        tex = self.sprites['sent_flash'] if e.hit > 0 else self.sprites['sent']
        self._sprite(tex, e.x, e.y + bob + 3)


def _desenhar_jogador(self):
    if self.inv > 0 and int(Clock.get_boottime() * 14) % 2:
        return
    x, y = self.px, self.py
    esc = max(0.12, self.cai / 0.55) if self.cai > 0 else 1.0

    Color(0, 0, 0, 0.28)
    pos, size = self._rect(x - 6, y + 3.5, 12, 5)
    Ellipse(pos=pos, size=size)

    nome_dir = ('cima', 'lado', 'baixo', 'lado')[self.dir]
    espelha = (self.dir == 3)

    # rastro do impulso
    if self.dash_t > 0:
        q = self.sprites[nome_dir][0]
        for k, al in ((10, 0.14), (5, 0.24)):
            Color(1, 1, 1, al)
            self._sprite(q, x - self.dvx * k, y - self.dvy * k, espelha)

    Color(1, 1, 1, 1)
    andando = math.hypot(self.vx, self.vy) > 8
    ciclo = int(self.passo / 7) % 4
    quadro = (1, 0, 2, 0)[ciclo] if andando else 0
    bob = -1 if (andando and quadro == 0) else 0
    self._sprite(self.sprites[nome_dir][quadro], x, y + bob, espelha, esc)

    if self.atk > 0:
        self._desenhar_espada(x, y - 2)


def _desenhar_espada(self, x, cy):
    ang = self.angulo_golpe()
    k = 1.0 - self.atk / ATK_DUR
    ini = ang - self.atk_lado * min(1.15, ATK_ARCO * k)

    # o arco do Kivy conta em graus a partir do norte, no sentido horario;
    # o angulo do jogo conta a partir do leste com y para baixo: +90 alinha
    a1 = math.degrees(min(ini, ang)) + 90
    a2 = math.degrees(max(ini, ang)) + 90
    s = self.escala
    cx_s = self.ox + x * s
    cy_s = self.oy + (H - cy) * s

    Color(*hexa('#F2D9A0', 0.22 * (1 - k * 0.7)))
    Line(circle=(cx_s, cy_s, 14 * s, a1, a2), width=max(1.0, 3.5 * s))
    Color(*hexa('#FFF6E0', 0.55 * (1 - k * 0.6)))
    Line(circle=(cx_s, cy_s, 15 * s, a1, a2), width=max(1.0, 1.25 * s))

    # lamina: retangulos girados junto com o gume
    PushMatrix()
    Translate(cx_s, cy_s, 0)
    Rotate(angle=-math.degrees(ang), axis=(0, 0, 1), origin=(0, 0))
    for cor, lx, ly, lw, lh in (
            ('#4A3A28', 2, -1, 5, 3),      # punho
            ('#C98A3E', 6, -4, 2, 9),      # guarda
            ('#8A5D28', 6, 3, 2, 2),
            ('#7E7794', 8, -2, 11, 4),     # contorno da lamina
            ('#C9C2D6', 8, -1, 11, 2),
            ('#FFFFFF', 9, -1, 9, 1)):     # fio
        Color(*hexa(cor))
        Rectangle(pos=(lx * s, (-ly - lh) * s), size=(lw * s, lh * s))
    PopMatrix()


def _desenhar_faiscas(self):
    for f in self.faiscas:
        a = min(1.0, f.t / f.m)
        cor = '#FFF6E0' if f.t > f.m * 0.5 else '#E07A22'
        self._cor_rect(hexa(cor, a), int(f.x), int(f.y), 1, 1)


def _desenhar_tochas(self):
    """So a chama: retangulos pequenos, baratos de refazer por quadro."""
    p = Clock.get_boottime()
    for tx, ty, fase in self.tochas:
        s1 = math.sin(p * 9 + fase) + math.sin(p * 23.7 + fase * 2) * 0.4
        alt = 5 + int(round(s1 * 0.9))
        lat = int(round(math.sin(p * 13 + fase) * 1.2))
        self._cor_rect(hexa('#8A3A18'), tx - 2 + lat, ty - alt, 4, alt + 2)
        self._cor_rect(hexa('#E07A22'), tx - 1 + lat, ty - alt + 1, 2, alt)
        self._cor_rect(hexa('#F2D9A0'), tx + lat, ty - alt + 3, 1, 2)


def _desenhar_halos(self):
    """Luz quente das tochas. Vai numa camada propria porque a posicao
    nunca muda: refazer isso a cada quadro custava caro na GPU."""
    for tx, ty, fase in self.tochas:
        raio = 46
        Color(1, 1, 1, 1)
        pos, size = self._rect(tx - raio, ty - raio, raio * 2, raio * 2)
        Rectangle(texture=self.tex_luz, pos=pos, size=size)


def _desenhar_hud(self):
    """Vitalidade em tracinhos de latao, no alto da area de jogo."""
    for i in range(3):
        cor = hexa('#C98A3E') if i < self.hp else hexa('#2A2636')
        self._cor_rect(cor, 4 + i * 6, 4, 4, 8)
        self._cor_rect(hexa('#7A4E1C' if i < self.hp else '#201D2B'),
                       4 + i * 6, 12, 4, 1)
    if self.tem_impulso:
        self._cor_rect(hexa('#4E9A8A'), W - 14, 4, 10, 9)
        self._cor_rect(hexa('#BFF3E4'), W - 12, 6, 6, 5)


def _desenhar_controles(self):
    s = self.escala
    # analogico: so aparece quando o dedo esta na tela
    if self.stick_id is not None:
        cx, cy = self.stick_centro
        raio = 66 * s
        Color(1, 1, 1, 0.10)
        Ellipse(pos=(cx - raio, cy - raio), size=(raio * 2, raio * 2))
        Color(*hexa('#C98A3E', 0.30))
        kr = 26 * s
        knx = cx + self.tx * raio * 0.75
        kny = cy - self.ty * raio * 0.75
        Ellipse(pos=(knx - kr, kny - kr), size=(kr * 2, kr * 2))

    # botoes A (golpe) e B (impulso)
    for nome, (bx, by), ativo in self._areas_botoes():
        raio = 33 * s
        Color(*(hexa('#C98A3E', 0.35) if ativo else (1, 1, 1, 0.10)))
        Ellipse(pos=(bx - raio, by - raio), size=(raio * 2, raio * 2))


def _areas_botoes(self):
    """Posicao dos dois botoes, em pixels de tela."""
    s = self.escala
    dir_x = self.right - 60 * s
    base_y = self.y + 60 * s
    return (("A", (dir_x, base_y), self.botao_golpe),
            ("B", (dir_x - 78 * s, base_y + 46 * s), self.botao_imp))


# ------------------------------------------------------------- entrada
def on_touch_down(self, touch):
    for nome, (bx, by), _ in self._areas_botoes():
        if math.hypot(touch.x - bx, touch.y - by) < 46 * self.escala:
            self.toques_botao[touch.uid] = nome
            if nome == "A":
                self.botao_golpe = True
            else:
                self.botao_imp = True
            return True
    if touch.x < self.center_x:
        self.stick_id = touch.uid
        self.stick_centro = (touch.x, touch.y)
        self.tx = self.ty = 0.0
        return True
    return True


def on_touch_move(self, touch):
    if touch.uid == self.stick_id:
        raio = 54.0 * self.escala
        dx = touch.x - self.stick_centro[0]
        dy = touch.y - self.stick_centro[1]
        d = math.hypot(dx, dy) or 1.0
        m = min(d, raio)
        self.tx = (dx / d) * (m / raio)
        self.ty = -(dy / d) * (m / raio)     # tela sobe, jogo desce
    return True


def on_touch_up(self, touch):
    if touch.uid == self.stick_id:
        self.stick_id = None
        self.tx = self.ty = 0.0
    nome = self.toques_botao.pop(touch.uid, None)
    if nome == "A":
        self.botao_golpe = False
    elif nome == "B":
        self.botao_imp = False
    return True


_MAPA_TECLAS = {273: 'up', 274: 'down', 276: 'left', 275: 'right',
                119: 'up', 115: 'down', 97: 'left', 100: 'right'}


def _tecla_desce(self, window, key, *args):
    if key in _MAPA_TECLAS:
        self.teclas.add(_MAPA_TECLAS[key])
    elif key in (106, 122):          # J / Z
        self.botao_golpe = True
    elif key in (107, 120, 32):      # K / X / espaco
        self.botao_imp = True
    elif key == 114:                 # R
        self.carregar(self.sala_idx)
    return True


def _tecla_sobe(self, window, key, *args):
    if key in _MAPA_TECLAS:
        self.teclas.discard(_MAPA_TECLAS[key])
    elif key in (106, 122):
        self.botao_golpe = False
    elif key in (107, 120, 32):
        self.botao_imp = False
    return True


# ------------------------------------------------------------- anexar
for _nome in (
        '_relayout',
        '_montar_camadas',
        '_assinatura_estatica',
        '_rect',
        '_cor_rect',
        '_sprite',
        '_fr',
        'pinta_piso',
        'pinta_parede',
        'pinta_fosso',
        'pintar_cenario',
        'desenhar',
        '_desenhar_placas',
        '_desenhar_portas',
        '_desenhar_blocos',
        '_desenhar_nucleo',
        '_desenhar_inimigos',
        '_desenhar_jogador',
        '_desenhar_espada',
        '_desenhar_faiscas',
        '_desenhar_tochas',
        '_desenhar_halos',
        '_desenhar_hud',
        '_desenhar_controles',
        '_areas_botoes',
        'on_touch_down',
        'on_touch_move',
        'on_touch_up',
        '_tecla_desce',
        '_tecla_sobe',
):
    setattr(Jogo, _nome, globals()[_nome])


# ================================================================== app
class NucleoApp(App):
    def build(self):
        Window.clearcolor = (0.07, 0.066, 0.10, 1)
        try:
            return Jogo()
        except Exception:
            texto = traceback.format_exc()
            print("FALHA AO CRIAR O JOGO:\n" + texto)
            linhas = [l for l in texto.strip().split("\n") if l.strip()]
            return Label(text="ERRO\n" + "\n".join(linhas[-5:]),
                         font_size="12sp", halign="center",
                         color=(1, 0.5, 0.5, 1))


if __name__ == "__main__":
    NucleoApp().run()
