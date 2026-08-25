[app]

title = Nucleo
package.name = nucleo
package.domain = br.imar

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,ttf,ogg,wav
source.exclude_patterns = patch_p4a.py,build-apk*.yml,README.md,main_teste.py,jogo_backup.py

version = 0.1

requirements = python3,kivy==2.3.0

orientation = landscape
fullscreen = 1

android.api = 33
android.minapi = 21
android.ndk_api = 21
android.archs = arm64-v8a
android.allow_backup = True
android.accept_sdk_license = True
android.logcat_filters = *:S python:D

p4a.branch = v2024.01.21
p4a.bootstrap = sdl2

[buildozer]

log_level = 1
warn_on_root = 1
