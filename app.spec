# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['work_clock_main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('components/*', 'components'),
        ('music/*', 'music'),
        ('resources/*', 'resources')
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='WorkClock',
    debug=False,
    upx=True,
    console=False,
    icon='resources/icon2.ico',
)