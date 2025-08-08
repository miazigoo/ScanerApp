[app]
title = Barcode Scanner
package.name = barcodescanner
package.domain = argos.net
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,txt
version = 1.0

# Минимальный набор зависимостей
requirements = python3,kivy,kivymd,sqlalchemy,requests

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,ACCESS_NETWORK_STATE

# Используем проверенные версии
android.api = 27
android.minapi = 21
android.ndk = 19c
android.sdk = 27
android.accept_sdk_license = True

android.archs = armeabi-v7a

# Простая конфигурация
p4a.bootstrap = sdl2
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
