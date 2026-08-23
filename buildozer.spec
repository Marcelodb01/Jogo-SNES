[app]

# Nome exibido no launcher
title = Nucleo

# Nome do pacote (sem espacos, sem acentos)
package.name = nucleo
package.domain = br.imar

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,ttf,ogg,wav

version = 0.1

# SEM fixar a versao do kivy: o p4a usa a versao que ele proprio testa
# junto com o Python que constroi. Fixar kivy==2.3.0 quebrava o build,
# porque essa versao nao compila contra Python 3.14.
requirements = python3,kivy

orientation = landscape
fullscreen = 1

# Icone e splash (descomente quando tiver os arquivos)
# icon.filename = %(source.dir)s/assets/icon.png
# presplash.filename = %(source.dir)s/assets/presplash.png

# ---------------------------------------------------------------
# ATENCAO: as opcoes android.* e p4a.* ficam AQUI, dentro de [app].
# Se forem postas em secoes [android] ou [

android.api = 34
android.minapi = 24p4a], o buildozer IGNORA.
# ---------------------------------------------------------------
android.ndk_api = 24

# Uma arquitetura so enquanto testamos: corta o tempo pela metade.
# Para publicar, volte a incluir , armeabi-v7a
android.archs = arm64-v8a

android.allow_backup = True

# Obrigatorio em CI: sem isso o build trava esperando alguem digitar "y"
android.accept_sdk_license = True

# Jogo offline: nenhuma permissao necessaria.
# android.permissions = INTERNET

android.logcat_filters = *:S python:D

# O p4a compilou o Kivy 2.3.1, que e da geracao do SDL2. Forcar sdl3
# compila, mas o app fecha ao abrir a janela. sdl2 e a combinacao que
# o proprio p4a testa com essa versao do Kivy.
p4a.bootstrap = sdl2

[buildozer]

# 1 = log legivel. 2 gera centenas de milhares de linhas.
log_level = 1
warn_on_root = 1
