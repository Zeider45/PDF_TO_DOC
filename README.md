# Conversor masivo PDF → Word

Script en Python para convertir cientos o miles de PDFs a DOCX en una sola operación (pensado para ~1500 archivos por lote).

## Requisitos

- Python 3.9+ en Windows
- Paquetes: `pdf2docx`, `tqdm`

Instalación rápida:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt
```

## Uso rápido

Convierte todos los PDFs de `input_pdf` a DOCX dentro de `output_docx` usando varios hilos:

```powershell
python converter.py --input input_pdf --output output_docx --workers 6 --overwrite
```

Parámetros principales:

- `--input`: ruta de carpeta o archivo PDF. Puedes repetir `--input` varias veces.
- `--output`: carpeta destino para los DOCX.
- `--pattern`: patrón glob para filtrar PDFs (por defecto `*.pdf`).
- `--recursive / --no-recursive`: activar o desactivar búsqueda en subcarpetas (por defecto recursiva).
- `--workers`: número de hilos; usa 4-8 para lotes grandes según tu CPU.
- `--max-files`: tope de archivos a procesar si necesitas dividir un lote muy grande.
- `--overwrite`: reescribe DOCX existentes.
- `--timeout-per-file`: tiempo máximo (s) por archivo; si se excede, se marca como error y se continúa (útil si algún PDF se cuelga).

## Interfaz gráfica (GUI sencilla)

1. Ejecuta:
   ```powershell
   python gui.py
   ```
2. Agrega archivos o carpetas, elige la carpeta de destino y pulsa "Iniciar conversion".
3. Opciones disponibles: patrón (`*.pdf`), recursivo, workers, límite de archivos, timeout por archivo y sobrescritura.

## Generar ejecutable (Windows)

Requiere tener Python instalado en la máquina donde generas el .exe. El ejecutable resultante no requiere Python para correr.

1. Instala PyInstaller en el entorno virtual (asegúrate de activar `.\.venv\Scripts\Activate.ps1` antes):

```powershell
pip install pyinstaller
# si falla, prueba: python -m pip install pyinstaller
```

2. Construye ejecutable de la GUI (sin consola) usando el spec preparado que fuerza la inclusión de `pdf2docx`. Ejecuta PyInstaller con el Python del entorno virtual para evitar el error `PackageNotFoundError`:

```powershell
.\.venv\Scripts\python -m pip install pyinstaller
.\.venv\Scripts\python -m PyInstaller --noconfirm pdf_to_doc_gui.spec
```

3. (Opcional) Construye ejecutable de la CLI (con consola) usando flags directos:

```powershell
.\.venv\Scripts\python -m PyInstaller --noconfirm --onefile --name pdf_to_doc_cli --collect-all pdf2docx --additional-hooks-dir=. converter.py
```

Los .exe quedan en `dist/`. Copia la carpeta `dist` a la máquina destino y ejecuta `pdf_to_doc_gui.exe`.

## Ejemplos

- Procesar 1500 PDFs recursivamente con 8 hilos:

```powershell
python converter.py --input D:\lotes\pdfs --output D:\lotes\docx --workers 8 --overwrite
```

- Procesar solo el primer nivel (sin recursión):

```powershell
python converter.py --input C:\pdfs --output C:\docx --no-recursive
```

- Limitar a 500 archivos para dividir el lote:

```powershell
python converter.py --input C:\pdfs --output C:\docx --max-files 500
```

## Notas y buenas prácticas

- Asegúrate de tener espacio en disco; DOCX suele ser más grande que el PDF original.
- Si un archivo falla, revisa el listado final de errores; el resto seguirá procesando.
- `pdf2docx` funciona mejor con PDFs basados en texto; si son escaneos, necesitarás OCR previo (no incluido aquí).
