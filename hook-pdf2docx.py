from PyInstaller.utils.hooks import collect_all, collect_submodules

datas, binaries, hiddenimports = collect_all("pdf2docx")

# Explicitly collect all pdf2docx submodules to ensure they are included
hiddenimports += collect_submodules("pdf2docx")
