# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main_ui.py'],
    pathex=[],
    binaries=[],
    datas=[('cash_tab1.png', '.'), ('cash_tab2.png', '.'), ('miumiu.png', '.'), ('sell_btn.png', '.'), ('ch.png', '.'), ('exit_shop_btn.png', '.'), ('x.png', '.'), ('투명.png', '.')],
    hiddenimports=['tkinter', 'tkinter.messagebox', 'cv2', 'mss', 'pydirectinput', 'pygetwindow', 'keyboard', 'pygame', 'win32api', 'win32con', 'requests'],
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
    name='secure_ui',
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
    uac_admin=True,
    manifest='admin.manifest',
)
