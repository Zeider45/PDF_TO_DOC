# 📄 Conversor Masivo PDF → DOCX

![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

Herramienta profesional en Python para convertir cientos o miles de archivos PDF a formato DOCX de manera eficiente y confiable. Diseñada para procesar lotes grandes (~1500+ archivos) con procesamiento paralelo, manejo robusto de errores y retroalimentación en tiempo real.

## 🌟 Características Principales

- ✅ **Conversión masiva** - Procesa miles de archivos en una sola operación
- 🚀 **Procesamiento paralelo** - Utiliza múltiples hilos para máxima eficiencia
- 🛡️ **Manejo robusto de errores** - Continúa procesando incluso si algunos archivos fallan
- 📊 **Seguimiento en tiempo real** - Barra de progreso y logs detallados
- ⏱️ **Control de timeout** - Evita que archivos problemáticos bloqueen todo el proceso
- 💻 **Interfaz dual** - CLI para automatización y GUI para usuarios
- 📝 **Logging completo** - Registro detallado de todas las operaciones
- 🔄 **Recuperación automática** - Limpieza adecuada de recursos incluso en caso de error

## 🔧 Requisitos del Sistema

- **Python**: 3.9 o superior
- **Sistema Operativo**: Windows, Linux, macOS
- **Espacio en disco**: DOCX puede ser más grande que el PDF original
- **RAM**: Recomendado 4GB+ para lotes grandes

## 📦 Instalación

### Opción 1: Instalación Rápida (Recomendada)

```powershell
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

```bash
# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Opción 2: Instalación Manual

```bash
pip install pdf2docx>=0.5.8 tqdm>=4.66.0
```

## 🚀 Uso

### Interfaz Gráfica (GUI) - Recomendada para Usuarios

La GUI ofrece una experiencia intuitiva con todas las funcionalidades disponibles:

```powershell
python gui.py
```

**Características de la GUI:**
- 📂 Interfaz drag-and-drop amigable
- 📊 Barra de progreso en tiempo real
- 📝 Registro de actividad visible
- ⚙️ Configuración fácil de opciones
- ✅ Validación de entradas
- 🎨 Interfaz moderna con emojis para mejor UX

**Pasos para usar la GUI:**

1. **Agregar archivos/carpetas**: Click en "➕ Agregar archivos" o "📁 Agregar carpeta"
2. **Seleccionar destino**: Click en "📂 Elegir" para la carpeta de salida
3. **Configurar opciones** (opcional):
   - Patrón de búsqueda (default: `*.pdf`)
   - Búsqueda recursiva en subcarpetas
   - Número de workers (threads concurrentes)
   - Máximo de archivos a procesar
   - Timeout por archivo
   - Sobrescribir archivos existentes
4. **Iniciar**: Click en "🚀 Iniciar conversión"
5. **Monitorear**: Observa el progreso en tiempo real y revisa los logs

### Línea de Comandos (CLI) - Para Automatización

Ideal para scripts, tareas programadas y procesamiento por lotes:

```powershell
python converter.py --input <ruta_entrada> --output <ruta_salida> [opciones]
```

#### Parámetros Principales

| Parámetro | Descripción | Requerido | Default |
|-----------|-------------|-----------|---------|
| `--input` | Ruta de archivo PDF o carpeta. Se puede repetir múltiples veces | ✅ Sí | - |
| `--output` | Carpeta destino para archivos DOCX | ✅ Sí | - |
| `--pattern` | Patrón glob para filtrar archivos | ❌ No | `*.pdf` |
| `--recursive` | Buscar en subcarpetas | ❌ No | `True` |
| `--no-recursive` | Desactivar búsqueda recursiva | ❌ No | - |
| `--workers` | Número de hilos concurrentes | ❌ No | CPU-1 |
| `--max-files` | Límite de archivos a procesar | ❌ No | Ilimitado |
| `--timeout-per-file` | Timeout en segundos por archivo | ❌ No | Sin límite |
| `--overwrite` | Sobrescribir archivos DOCX existentes | ❌ No | `False` |

### 📚 Ejemplos de Uso

#### Ejemplo 1: Conversión Simple
```powershell
python converter.py --input ./pdfs --output ./docx
```

#### Ejemplo 2: Lote Grande con Múltiples Workers
```powershell
python converter.py --input D:\documentos\pdfs --output D:\documentos\docx --workers 8 --overwrite
```

#### Ejemplo 3: Múltiples Carpetas de Entrada
```powershell
python converter.py --input ./carpeta1 --input ./carpeta2 --input ./archivo.pdf --output ./salida
```

#### Ejemplo 4: Sin Recursión (Solo Nivel Superior)
```powershell
python converter.py --input ./pdfs --output ./docx --no-recursive
```

#### Ejemplo 5: Limitar Archivos y Agregar Timeout
```powershell
python converter.py --input ./pdfs --output ./docx --max-files 500 --timeout-per-file 120
```

#### Ejemplo 6: Patrón Personalizado
```powershell
python converter.py --input ./docs --output ./docx --pattern "informe_*.pdf"
```

## 🏗️ Arquitectura y Funcionamiento

### Flujo de Conversión

```
1. Validación de entradas
   ↓
2. Expansión de rutas (archivos + carpetas)
   ↓
3. Filtrado por patrón
   ↓
4. Eliminación de duplicados
   ↓
5. Aplicación de límites (max-files)
   ↓
6. Procesamiento paralelo con ThreadPoolExecutor
   ↓
7. Conversión individual con manejo de errores
   ↓
8. Reporte de resultados y errores
```

### Componentes Principales

#### `converter.py` - Motor de Conversión

- **`expand_inputs()`**: Expande rutas y encuentra archivos PDF
- **`convert_single()`**: Convierte un PDF individual usando context manager
- **`process_batch()`**: Procesa múltiples archivos en paralelo
- **`run_conversion()`**: API principal para otras interfaces

#### `gui.py` - Interfaz Gráfica

- Interfaz moderna con Tkinter
- Actualización de progreso en tiempo real
- Log de actividad integrado
- Validación de entradas robusta

### Manejo de Errores

El sistema implementa múltiples capas de manejo de errores:

1. **Validación de entrada**: Verifica archivos y directorios antes de procesar
2. **Context managers**: Garantiza liberación de recursos incluso en error
3. **Try-catch específicos**: Captura errores de memoria, permisos, formato, etc.
4. **Timeout protection**: Evita bloqueos en archivos problemáticos
5. **Logging detallado**: Registra todos los errores para diagnóstico

### Mensajes de Error Comunes

| Error | Causa | Solución |
|-------|-------|----------|
| "El archivo PDF no existe" | Ruta incorrecta | Verificar ruta del archivo |
| "El archivo PDF está vacío" | Archivo corrupto o vacío | Revisar archivo PDF |
| "Memoria insuficiente" | PDF muy grande | Reducir workers o agregar RAM |
| "Sin permisos" | Acceso denegado | Ejecutar con permisos adecuados |
| "Timeout > Xs" | Archivo muy complejo | Aumentar timeout o verificar PDF |

## ⚡ Optimización y Mejores Prácticas

### Configuración de Workers

- **CPU de 4 núcleos**: `--workers 3-4`
- **CPU de 8 núcleos**: `--workers 6-8`
- **CPU de 16+ núcleos**: `--workers 12-16`

**Regla general**: Usar CPU count - 1 o CPU count - 2 para dejar recursos al sistema.

### Manejo de Lotes Grandes

Para más de 2000 archivos, considerar:

1. **Dividir en lotes**:
   ```powershell
   python converter.py --input ./pdfs --output ./docx --max-files 1000
   # Luego procesar los siguientes 1000, etc.
   ```

2. **Usar timeout** para evitar bloqueos:
   ```powershell
   python converter.py --input ./pdfs --output ./docx --timeout-per-file 300
   ```

3. **Monitorear uso de memoria** durante procesamiento

### Espacio en Disco

- DOCX típicamente es **1.5-3x** el tamaño del PDF original
- Verificar espacio disponible antes de procesar lotes grandes
- Considerar usar `--overwrite` con cuidado

### Tipos de PDF Soportados

✅ **Funcionan bien**:
- PDFs basados en texto
- PDFs generados desde Word/Office
- PDFs con fuentes embebidas

⚠️ **Pueden tener problemas**:
- PDFs escaneados (requieren OCR previo)
- PDFs con protección/cifrado
- PDFs con formularios complejos
- PDFs muy grandes (>100 MB)

## 📊 Logs y Debugging

### Niveles de Log

El sistema utiliza diferentes niveles de logging:

- **INFO**: Operaciones normales y progreso
- **WARNING**: Advertencias (archivos omitidos, etc.)
- **ERROR**: Errores en archivos específicos
- **DEBUG**: Información detallada (activar manualmente)

### Activar Debug Mode

```python
# En converter.py o gui.py, cambiar:
logging.basicConfig(level=logging.DEBUG, ...)
```

### Ubicación de Logs

- **CLI**: Salida a consola (stdout)
- **GUI**: Panel de registro de actividad + consola

## 🔨 Generar Ejecutable (Windows)

Para distribuir sin requerir Python instalado:

### 1. Instalar PyInstaller

```powershell
.\.venv\Scripts\Activate.ps1
pip install pyinstaller
```

### 2. Generar Ejecutable GUI

```powershell
.\.venv\Scripts\python -m PyInstaller --noconfirm pdf_to_doc_gui.spec
```

### 3. Generar Ejecutable CLI (Opcional)

```powershell
.\.venv\Scripts\python -m PyInstaller --noconfirm --onefile --name pdf_to_doc_cli --collect-all pdf2docx --additional-hooks-dir=. converter.py
```

### 4. Distribuir

Los ejecutables estarán en la carpeta `dist/`. Copia toda la carpeta al equipo destino.

```
dist/
├── pdf_to_doc_gui.exe  (GUI sin consola)
└── pdf_to_doc_cli.exe  (CLI con consola)
```

## 🐛 Solución de Problemas

### El proceso se queda pegado

**Solución implementada**: Se agregó context manager para garantizar cierre de recursos.

Si aún ocurre:
- Usar `--timeout-per-file 300` (5 minutos)
- Reducir `--workers` a 2-3
- Verificar si archivos PDF específicos son muy grandes

### Errores de memoria

- Reducir número de workers
- Procesar en lotes más pequeños con `--max-files`
- Cerrar otras aplicaciones

### Archivos no se encuentran

- Verificar que el patrón sea correcto: `--pattern "*.pdf"`
- Usar `--recursive` si archivos están en subcarpetas
- Verificar permisos de lectura en carpetas

### GUI no responde

- La conversión está en progreso en segundo plano
- Revisar panel de logs para ver actividad
- No cerrar la ventana hasta que termine

## 📄 Estructura del Proyecto

```
PDF_TO_DOC/
├── converter.py          # Motor de conversión (CLI + API)
├── gui.py               # Interfaz gráfica
├── requirements.txt     # Dependencias
├── README.md           # Este archivo
├── .gitignore          # Archivos ignorados
├── hook-pdf2docx.py    # Hook para PyInstaller
└── pdf_to_doc_gui.spec # Configuración PyInstaller
```

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para más detalles.

## ⚠️ Limitaciones Conocidas

- `pdf2docx` funciona mejor con PDFs basados en texto
- PDFs escaneados requieren OCR previo (no incluido)
- Algunos elementos complejos pueden no convertirse perfectamente
- El formato puede variar dependiendo de la complejidad del PDF original

## 🔗 Enlaces Útiles

- [Documentación pdf2docx](https://github.com/dothinking/pdf2docx)
- [Python Threading](https://docs.python.org/3/library/threading.html)
- [Tkinter Documentation](https://docs.python.org/3/library/tkinter.html)

## 📞 Soporte

Si encuentras problemas:

1. Revisa la sección de Solución de Problemas
2. Verifica los logs para más detalles
3. Abre un issue en GitHub con:
   - Descripción del problema
   - Mensaje de error completo
   - Versión de Python
   - Sistema operativo
   - Comando o pasos para reproducir

---

**Desarrollado con ❤️ para facilitar la conversión masiva de documentos**
