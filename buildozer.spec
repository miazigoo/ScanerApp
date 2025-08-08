[app]
title = Barcode Scanner
package.name = barcodescanner
package.domain = argos.net
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,txt
version = 1.0

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,ACCESS_NETWORK_STATE

# Стабильные версии для CI
android.api = 28
android.minapi = 21
android.ndk = 21e
android.sdk = 28
android.accept_sdk_license = True

# Только одна архитектура для быстрой сборки в CI
android.archs = armeabi-v7a

p4a.bootstrap = sdl2
p4a.branch = master
requirements = python3,kivy==2.3.1,kivymd==1.2.0,sqlalchemy,pydantic,requests

[buildozer]
log_level = 1
warn_on_root = 0