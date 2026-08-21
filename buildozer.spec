[app]
title = MyPlaneGame
package.name = planegame
package.domain = org.myapp
source.dir = .
source.include_exts = py,png,jpg,ttf,ttc
version = 0.1
requirements = python3,pygame
orientation = portrait
fullscreen = 1

[buildozer]
log_level = 2
warn_on_root = 1

[android]
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a
