[app]

title = Nucleo
package.name = nucleo
package.domain = br.imar

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,ttf,ogg,wav
source.exclude_patterns = patch_p4a.py,build-apk*.yml,README.md

version = 0.1

requirements = python3,kivy

orientation = landscape
fullscreen = 1

android.api = 34
android.minapi = 24
android.ndk_api = 24
android.archs = arm64-v8a
android.allow_backup = True
android.accept_sdk_license = True
android.logcat_filters = *:S python:D

p4a.bootstrap = sdl2

[buildozer]

log_level = 1
warn_on_root = 1
