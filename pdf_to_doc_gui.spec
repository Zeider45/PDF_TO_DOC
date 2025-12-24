# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, copy_metadata, collect_submodules

pdf2docx_datas, pdf2docx_binaries, pdf2docx_hiddenimports = collect_all("pdf2docx")
try:
    pdf2docx_meta = copy_metadata("pdf2docx")
except Exception:
    pdf2docx_meta = []

# Explicitly collect all pdf2docx submodules to ensure they are included
# This is necessary because pdf2docx uses dynamic imports that PyInstaller
# cannot detect automatically (e.g., when importing Converter class)
pdf2docx_submodules = collect_submodules("pdf2docx")

# Collect PyMuPDF and its dependencies
pymupdf_datas, pymupdf_binaries, pymupdf_hiddenimports = collect_all("fitz")

a = Analysis(
    ['gui.py'],
    pathex=['.'],
    binaries=pdf2docx_binaries + pymupdf_binaries,
    datas=pdf2docx_datas + pdf2docx_meta + pymupdf_datas,
    # Combine all hidden imports - collect_submodules gets all submodules automatically
    hiddenimports=pdf2docx_hiddenimports + pdf2docx_submodules + pymupdf_hiddenimports,
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
