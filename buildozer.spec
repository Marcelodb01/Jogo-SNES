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
# Se forem postas em secoes [android] ou [p4a], o buildozer IGNORA.
# ---------------------------------------------------------------

android.api = 34
android.minapi = 24
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

# O Kivy 3.x usa SDL3; o buildozer assume sdl2 por padrao.
p4a.bootstrap = sdl3

[buildozer]

# 1 = log legivel. 2 gera centenas de milhares de linhas.
log_level = 1
warn_on_root = 1
