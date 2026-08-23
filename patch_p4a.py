# -*- coding: utf-8 -*-
"""
Corrige um bug do python-for-android (master, 2026).

O p4a resolve as dependencias Python puras consultando o PyPI COM as flags
de plataforma do Android. Quando um pacote publica wheel compilado para
Android (caso do charset-normalizer 3.x, dependencia do requests, que por
sua vez vem junto com o Kivy), ele pega esse wheel e manda instalar --
mas o pip da instalacao roda no Linux do runner e SEM as flags de
plataforma. O pip entao recusa:

    ERROR: charset_normalizer-...-android_24_arm64_v8a.whl
           is not a supported wheel on this platform

A correcao passa as MESMAS flags de plataforma na hora de instalar.

Uso:  python3 patch_p4a.py <caminho-do-clone-do-p4a>
"""

import sys
import os

MARCA = "_p4a_platform_flags"

AJUDANTE = '''

def _p4a_platform_flags(ctx, arch):
    """PATCH: informa ao pip que o alvo e Android, nao o host."""
    try:
        tags = PyProjectRecipe.get_wheel_platform_tags(arch.arch, ctx)
        flags = " ".join("--platform={}".format(t) for t in tags)
        try:
            pyver = Recipe.get_recipe("hostpython3", ctx).version
        except Exception:
            pyver = "{}.{}.{}".format(*sys.version_info[:3])
        return flags + " --python-version " + pyver + " --only-binary=:all:"
    except Exception:
        return ""

'''

ALVO = '''                "install -v --target '{0}' --no-deps -r requirements.txt"'''

TROCA = ('''                "install -v --target '{0}' --no-deps " +'''
         '''\n                _p4a_platform_flags(ctx, arch) +'''
         '''\n                " -r requirements.txt"''')

ANCORA = "def run_pymodules_install("


def main():
    if len(sys.argv) != 2:
        print("uso: python3 patch_p4a.py <dir-do-p4a>")
        return 1

    caminho = os.path.join(sys.argv[1], "pythonforandroid", "build.py")
    if not os.path.isfile(caminho):
        print("ERRO: nao encontrei", caminho)
        return 1

    codigo = open(caminho, encoding="utf-8").read()

    if MARCA in codigo:
        print(">>> patch ja aplicado, nada a fazer.")
        return 0

    if codigo.count(ALVO) != 1:
        print("ERRO: o comando pip mudou de forma; achei",
              codigo.count(ALVO), "ocorrencias.")
        print("      O p4a provavelmente ja corrigiu isso sozinho.")
        return 1

    if ANCORA not in codigo:
        print("ERRO: nao achei a funcao run_pymodules_install.")
        return 1

    codigo = codigo.replace(ALVO, TROCA)
    codigo = codigo.replace(ANCORA, AJUDANTE.lstrip("\n") + ANCORA, 1)

    open(caminho, "w", encoding="utf-8").write(codigo)
    print(">>> patch aplicado em", caminho)
    return 0


if __name__ == "__main__":
    sys.exit(main())
