# -*- coding: utf-8 -*-
"""
TESTE MINIMO - nao e o jogo.

Serve para responder uma unica pergunta: o Kivy consegue subir neste APK?

- Se aparecer o texto verde na tela: o build esta bom, o problema estava
  no main.py do jogo, e voltamos para ele sabendo disso.
- Se continuar fechando no "Loading": o problema e do empacotamento, e
  nenhum ajuste no codigo do jogo resolveria.
"""

import sys
import traceback

try:
    import kivy
    from kivy.app import App
    from kivy.uix.label import Label
    from kivy.core.window import Window

    INFO = "FUNCIONOU\n\nKivy " + kivy.__version__ + "\nPython " + sys.version.split()[0]
    ERRO = None
except Exception:
    INFO = None
    ERRO = traceback.format_exc()
    print("FALHA NO IMPORT DO KIVY:\n" + ERRO)
    raise


class TesteApp(App):
    def build(self):
        Window.clearcolor = (0.05, 0.05, 0.08, 1)
        return Label(text=INFO, font_size="22sp", halign="center",
                     color=(0.4, 0.9, 0.5, 1))


if __name__ == "__main__":
    TesteApp().run()
