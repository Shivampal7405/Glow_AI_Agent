# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for GLOW
# Use this for better control over the build process

block_cipher = None

a = Analysis(
    ['glow_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.example.json', '.'),
        ('LICENSE', '.'),
        ('README.md', '.'),
        ('QUICK_START.md', '.'),
    ],
    hiddenimports=[
        'google.generativeai',
        'anthropic',
        'groq',
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'pyautogui',
        'pywin32',
        'PIL',
        'pytesseract',
        'psutil',
        'pygetwindow',
        'pycaw',
        'comtypes',
        'winshell',
        'docx',
        'openpyxl',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'jupyter',
        'notebook',
        'IPython',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GLOW',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/glow_icon.ico' if os.path.exists('assets/glow_icon.ico') else None,
    version_file=None,
)
