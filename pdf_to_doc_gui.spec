# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, copy_metadata

pdf2docx_datas, pdf2docx_binaries, pdf2docx_hiddenimports = collect_all("pdf2docx")
try:
    pdf2docx_meta = copy_metadata("pdf2docx")
except Exception:
    pdf2docx_meta = []

a = Analysis(
    ['gui.py'],
    pathex=['.'],
    binaries=pdf2docx_binaries,
    datas=pdf2docx_datas + pdf2docx_meta,
    hiddenimports=pdf2docx_hiddenimports + ['pdf2docx'],
    hookspath=['.'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='pdf_to_doc_gui',
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
