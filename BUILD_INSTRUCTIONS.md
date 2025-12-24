# Instrucciones para Construir el Ejecutable

Este documento proporciona instrucciones para construir el ejecutable de la aplicación con PyInstaller después de aplicar el fix para el error `ModuleNotFoundError: No module named 'pdf2docx'`.

## Requisitos Previos

1. **Python 3.9 o superior** instalado
2. **PyInstaller** instalado
3. Todas las dependencias del proyecto instaladas

## Pasos para Construir el Ejecutable

### 1. Activar el Entorno Virtual (si usas uno)

**Windows PowerShell:**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Windows CMD:**
```cmd
.venv\Scripts\activate.bat
```

**Linux/macOS:**
```bash
source .venv/bin/activate
```

### 2. Instalar las Dependencias

```bash
pip install -r requirements.txt
pip install pyinstaller
```

### 3. Limpiar Builds Anteriores (Recomendado)

**Windows:**
```powershell
Remove-Item -Recurse -Force build, dist
```

**Linux/macOS:**
```bash
rm -rf build dist
```

### 4. Construir el Ejecutable GUI

```bash
python -m PyInstaller --noconfirm pdf_to_doc_gui.spec
```

Este comando:
- Usa el archivo `pdf_to_doc_gui.spec` actualizado que incluye el fix
- Crea un ejecutable sin consola para la interfaz gráfica
- Incluye todos los módulos de pdf2docx correctamente

### 5. Construir el Ejecutable CLI (Opcional)

Si también quieres un ejecutable de línea de comandos:

```bash
python -m PyInstaller --noconfirm --onefile --name pdf_to_doc_cli --collect-all pdf2docx --additional-hooks-dir=. converter.py
```

### 6. Ubicación de los Ejecutables

Después de la construcción exitosa, los ejecutables estarán en:

**Windows:**
- GUI: `dist\pdf_to_doc_gui.exe` (sin ventana de consola)
- CLI: `dist\pdf_to_doc_cli.exe` (con ventana de consola)

**Linux:**
- GUI: `dist/pdf_to_doc_gui`
- CLI: `dist/pdf_to_doc_cli`

### 7. Probar el Ejecutable

**Windows:**
```powershell
.\dist\pdf_to_doc_gui.exe
```

**Linux:**
```bash
./dist/pdf_to_doc_gui
```

El ejecutable debería iniciar sin errores. Si antes obtenías el error `ModuleNotFoundError: No module named 'pdf2docx'`, ahora debería funcionar correctamente.

## Cambios Aplicados en el Fix

El fix incluye las siguientes mejoras en `pdf_to_doc_gui.spec`:

1. **Uso de `collect_submodules`**: Recolecta explícitamente todos los submódulos de pdf2docx
2. **Inclusión de PyMuPDF/fitz**: Agrega las dependencias de PyMuPDF correctamente
3. **Lista explícita de hiddenimports**: Incluye todos los módulos críticos de pdf2docx

### Archivo `pdf_to_doc_gui.spec` Actualizado

El archivo spec ahora incluye:

```python
from PyInstaller.utils.hooks import collect_all, copy_metadata, collect_submodules

pdf2docx_submodules = collect_submodules("pdf2docx")
pymupdf_datas, pymupdf_binaries, pymupdf_hiddenimports = collect_all("fitz")

hiddenimports=pdf2docx_hiddenimports + pdf2docx_submodules + pymupdf_hiddenimports + [
    'pdf2docx',
    'pdf2docx.converter',
    'pdf2docx.common',
    'pdf2docx.page',
    'pdf2docx.text',
    # ... y más
]
```

## Verificación del Fix

Para verificar que el fix funciona correctamente:

1. El ejecutable debe iniciar sin errores
2. No debe aparecer el error `ModuleNotFoundError: No module named 'pdf2docx'`
3. La aplicación debe poder convertir archivos PDF a DOCX normalmente

## Tamaño del Ejecutable

**Nota:** El ejecutable será más grande que antes (aproximadamente 100-120 MB) porque ahora incluye todos los submódulos de pdf2docx correctamente. Esto es normal y necesario para que la aplicación funcione.

## Solución de Problemas

### Error: "tkinter installation is broken"

Este error es normal en Linux y no afecta la construcción del ejecutable para Windows. Si estás construyendo en Linux para distribuir en Windows, ignora este warning.

### Error: UPX is not available

Este es un warning informativo. UPX es un compresor de ejecutables que no es estrictamente necesario. Puedes ignorar este mensaje.

### El ejecutable es muy grande

El tamaño del ejecutable es normal. Incluye Python, todas las librerías (pdf2docx, PyMuPDF, OpenCV, NumPy, etc.) y todos los submódulos necesarios.

### Error al importar otros módulos

Si aparecen errores relacionados con otros módulos, verifica que:
1. Todas las dependencias están instaladas: `pip install -r requirements.txt`
2. PyInstaller está actualizado: `pip install --upgrade pyinstaller`

## Distribución

Para distribuir el ejecutable:

1. Copia toda la carpeta `dist/` (no solo el .exe)
2. En Windows, el ejecutable es standalone pero puede requerir Visual C++ Redistributables
3. Para usuarios finales, considera crear un instalador con herramientas como Inno Setup o NSIS

## Soporte

Si encuentras problemas después de aplicar el fix:

1. Asegúrate de haber limpiado los builds anteriores
2. Verifica que estás usando el archivo `pdf_to_doc_gui.spec` actualizado
3. Revisa los logs de PyInstaller en `build/pdf_to_doc_gui/warn-pdf_to_doc_gui.txt`
4. Abre un issue en el repositorio con los detalles del error

---

**Última actualización:** 2025-12-24  
**Fix aplicado para:** ModuleNotFoundError: No module named 'pdf2docx'
