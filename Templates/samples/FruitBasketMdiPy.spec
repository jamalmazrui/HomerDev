# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['FruitBasketMdiPy.py'],
    pathex=['C:/HomerDev'],
    binaries=[],
    datas=[],
    hiddenimports=['homer', 'homer.inix', 'homer.lbc', 'homer.log', 'homer.mdi', 'homer.paths', 'homer.say', 'homer.util', 'homer.web'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='FruitBasketMdiPy',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
