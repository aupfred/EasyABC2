# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['../easyabc2/run_easyabc2.py'],
    pathex=['..'],
    binaries=[
        ('../easyabc2/third_party/abcmidi/abc2midi', 'easyabc2/third_party/abcmidi'),
        ('../easyabc2/third_party/abcmidi/midi2abc', 'easyabc2/third_party/abcmidi'),
    ],
    datas=[
        ('../easyabc2/resources', 'easyabc2/resources'),
        ('../easyabc2/third_party/abc2svg', 'easyabc2/third_party/abc2svg'),
    ],
    hiddenimports=[],
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
    [],
    exclude_binaries=True,
    name='EasyABC2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['../easyabc2/resources/img/EasyABC.icns'],
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='EasyABC2',
)

app = BUNDLE(
    coll,
    name='EasyABC2.app',
    icon='../easyabc2/resources/img/EasyABC.icns',
    bundle_identifier='org.easyabc2.app',
    info_plist={
        'CFBundleName': 'EasyABC2',
        'CFBundleDisplayName': 'EasyABC2',
        'CFBundleExecutable': 'EasyABC2',
        'CFBundleIdentifier': 'org.easyabc2.app',
        'CFBundleVersion': '2.0.0',
        'CFBundleShortVersionString': '2.0.0',
        'CFBundleIconFile': 'EasyABC.icns',
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'ABC notation file',
                'CFBundleTypeRole': 'Editor',
                'CFBundleTypeExtensions': ['abc'],
            },
            {
                'CFBundleTypeName': 'MIDI file',
                'CFBundleTypeRole': 'Editor',
                'CFBundleTypeExtensions': ['mid', 'midi'],
            },
        ],
    }
)
