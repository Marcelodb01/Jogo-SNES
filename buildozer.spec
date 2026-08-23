[app]

# Nome exibido no launcher
title = Nucleo

# Nome do pacote (sem espacos, sem acentos)
package.name = nucleo
package.domain = br.imar

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,ttf,ogg,wav

version = 0.1

# Kivy fixo numa versao testada evita surpresa no build
requirements = python3,kivy==2.3.0

orientation = landscape
fullscreen = 1

# Icone e splash (descomente quando tiver os arquivos)
# icon.filename = %(source.dir)s/assets/icon.png
# presplash.filename = %(source.dir)s/assets/presplash.png

[android]

android.api = 34
android.minapi = 24
android.ndk_api = 24
android.archs = arm64-v8a
android.allow_backup = True

# Obrigatorio em CI: sem isso o build trava esperando voce digitar "y"
android.accept_sdk_license = True

# Jogo offline: nenhuma permissao necessaria.
# android.permissions = INTERNET

# Debug ligado ajuda a ler o traceback com `buildozer android logcat`
android.logcat_filters = *:S python:D

[buildozer]

log_level = 1
warn_on_root = 1
