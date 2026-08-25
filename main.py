# -*- coding: utf-8 -*-
"""
TESTE VISUAL 2 - ainda nao e o jogo.

O teste anterior mostrou que o app abre e nao fecha mais, mas a tela
fica preta. Este aqui separa as possibilidades:

- Se a tela PISCAR entre vermelho, verde e azul: o desenho funciona, e o
  problema era so o texto (fonte).
- Se aparecer cor parada, sem piscar: desenha, mas o relogio do Kivy
  nao esta rodando.
- Se continuar preta: o desenho em si nao chega na tela.

O contador no canto tambem diz quantos quadros ja passaram.
"""

import sys

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.uix.label import Label
from kivy.uix.widget import Widget

CORES = [
    (0.9, 0.2, 0.2),   # vermelho
    (0.2, 0.8, 0.3),   # verde
    (0.2, 0.4, 0.9),   # azul
]


class Teste(Widget):

    def __init__(self, **kw):
        super(Teste, self).__init__(**kw)
        self.indice = 0
        self.quadros = 0

        self.rotulo = Label(
            text="iniciando", font_size="26sp",
            color=(1, 1, 1, 1))
        self.add_widget(self.rotulo)

        # desenha uma vez logo de cara, sem depender do relogio
        self.redesenhar()

        Clock.schedule_interval(self.tick, 1.0)
        Clock.schedule_interval(self.contar, 1.0 / 30.0)

    def redesenhar(self, *_):
        cor = CORES[self.indice % len(CORES)]
        self.canvas.before.clear()
        with self.canvas.before:
            Color(cor[0], cor[1], cor[2], 1)
            Rectangle(pos=self.pos, size=self.size)
        self.rotulo.pos = self.pos
        self.rotulo.size = self.size

    def tick(self, dt):
        self.indice += 1
        self.redesenhar()

    def contar(self, dt):
        self.quadros += 1
        self.rotulo.text = ("QUADROS: %d\nPython %s"
                            % (self.quadros, sys.version.split()[0]))


class TesteApp(App):
    def build(self):
        raiz = Teste()
        # redesenha quando a janela ganhar o tamanho real
        raiz.bind(size=raiz.redesenhar, pos=raiz.redesenhar)
        return raiz


if __name__ == "__main__":
    TesteApp().run()
