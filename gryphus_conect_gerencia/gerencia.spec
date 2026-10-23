# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None

base_path = os.path.abspath(SPECPATH)

datas = [
    (os.path.join(base_path, 'assets'), 'assets'),
    (os.path.join(base_path, 'src', 'ui', 'style.qss'), os.path.join('src', 'ui')),
]

# Include .env if available
root_env = os.path.join(os.path.dirname(base_path), '.env')
local_env = os.path.join(base_path, '.env')
if os.path.exists(local_env):
    datas.append((local_env, '.'))
elif os.path.exists(root_env):
    datas.append((root_env, '.'))

hidden_imports = [
    'PyQt6',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.QtSvg',
    'PyQt6.sip',
    'unittest',
    'pyparsing',
    'matplotlib',
    'matplotlib.backends.backend_qtagg',
    'matplotlib.figure',
    'reportlab',
    'reportlab.lib',
    'reportlab.platypus',
    'reportlab.pdfgen',
    'reportlab.lib.styles',
    'reportlab.lib.colors',
    'reportlab.lib.pagesizes',
    'openpyxl',
    'pandas',
    'supabase',
    'supabase_auth',
    'postgrest',
    'storage3',
    'realtime',
    'dotenv',
    'requests',
    'simplejson',
    'packaging',
    'packaging.version',
    'src.version',
    'src.core.updater',
    'src.ui.update_dialog',
]

excludes = [
    'tkinter',
    'IPython',
    'notebook',
    'pytest',
    'wx',
    'scipy',
    'scipy.spatial',
    'scipy.optimize',
    'scipy.sparse',
    'scipy.special',
    'scipy.fft',
    'scipy.interpolate',
    'lxml',
    'matplotlib.tests',
    'pandas.tests',
    'numpy.tests',
    'PIL.tests',
    'pydoc',
    'doctest',
]

a = Analysis(
    [os.path.join(base_path, 'main.py')],
    pathex=[base_path, os.path.join(base_path, 'src')],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Filtrar binarios pesados no requeridos
excluded_binaries = [
    'opengl32sw.dll', 'qt6pdf.dll', 'qt6pdfwidgets.dll', 'qt6quick.dll', 'qt6qml.dll', 
    'qt6networkauth.dll', '_avif.', 'qpdf.dll', 'qtga.dll', 'qtiff.dll', 'qwbmp.dll', 
    'qmng.dll', 'qwebp.dll'
]
a.binaries = [x for x in a.binaries if not any(b.lower() in x[0].lower() for b in excluded_binaries)]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

icon_file = os.path.join(base_path, 'assets', 'gryphus_conect_icon.ico')
if not os.path.exists(icon_file):
    icon_file = os.path.join(base_path, 'assets', 'app_icon.ico')
if not os.path.exists(icon_file):
    icon_file = None

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='GryPhusConectGerencia',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GryPhusConectGerencia',
)
