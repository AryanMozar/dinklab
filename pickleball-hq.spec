# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Pickleball HQ.

Build:
    pyinstaller pickleball-hq.spec

Output:
    Windows: dist/Pickleball HQ/Pickleball HQ.exe
    macOS:   dist/Pickleball HQ.app
"""

import sys
from pathlib import Path

block_cipher = None

# Bundle the frontend files (HTML/CSS/JS) so Flask can find them at runtime
datas = [
    ('frontend/templates', 'frontend/templates'),
    ('frontend/static', 'frontend/static'),
]

a = Analysis(
    ['launcher.py'],
    pathex=['backend'],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'flask',
        'werkzeug',
        'jinja2',
        'requests',
        'webview',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Pickleball HQ',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,           # No terminal window pops up
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='assets/icon.ico',  # uncomment when you add an icon
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Pickleball HQ',
)

# macOS-only: wrap into a proper .app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='Pickleball HQ.app',
        # icon='assets/icon.icns',  # uncomment when you add an icon
        bundle_identifier='com.aryanmozar.pickleballhq',
        info_plist={
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
            'NSHighResolutionCapable': True,
        },
    )
