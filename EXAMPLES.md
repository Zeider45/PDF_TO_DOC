# Ejemplos de Uso - Conversor PDF → DOCX

Este archivo contiene ejemplos prácticos de cómo usar el conversor.

## 🚀 Ejemplos Básicos

### 1. Conversión simple de una carpeta
```bash
python converter.py --input ./mis_pdfs --output ./mis_docx
```

### 2. Conversión con sobrescritura
```bash
python converter.py --input ./pdfs --output ./docx --overwrite
```

### 3. Conversión sin recursión (solo carpeta principal)
```bash
python converter.py --input ./pdfs --output ./docx --no-recursive
```

## ⚡ Ejemplos Avanzados

### 4. Procesamiento paralelo con 8 workers
```bash
python converter.py --input ./pdfs --output ./docx --workers 8
```

### 5. Limitar número de archivos a procesar
```bash
python converter.py --input ./pdfs --output ./docx --max-files 100
```

### 6. Agregar timeout por archivo (evitar bloqueos)
```bash
python converter.py --input ./pdfs --output ./docx --timeout-per-file 300
```

### 7. Múltiples carpetas de entrada
```bash
python converter.py \
  --input ./carpeta1 \
  --input ./carpeta2 \
  --input ./carpeta3 \
  --output ./salida \
  --workers 6
```

### 8. Patrón personalizado para filtrar archivos
```bash
python converter.py --input ./docs --output ./docx --pattern "reporte_*.pdf"
```

## 📊 Ejemplos de Producción

### 9. Lote grande con todas las optimizaciones
```bash
python converter.py \
  --input D:\documentos\pdfs \
  --output D:\documentos\docx \
  --workers 8 \
  --timeout-per-file 300 \
  --max-files 1000 \
  --overwrite
```

### 10. Procesamiento seguro con logging
```bash
python converter.py \
  --input ./pdfs \
  --output ./docx \
  --workers 4 \
  --timeout-per-file 180 \
  2>&1 | tee conversion_log.txt
```

## 💡 Casos de Uso Específicos

### Dividir lote muy grande en partes
Si tienes 5000 archivos, divídelos en lotes de 1000:

```bash
# Lote 1
python converter.py --input ./pdfs --output ./docx --max-files 1000

# Espera a que termine, luego elimina los PDFs procesados y repite
# O mejor: usa un script para procesar en lotes automáticamente
```

### Procesamiento de emergencia con máxima prioridad
Para archivos críticos que deben procesarse rápido:

```bash
python converter.py \
  --input ./urgente \
  --output ./urgente_docx \
  --workers 16 \
  --timeout-per-file 60 \
  --overwrite
```

### Conversión de prueba (test run)
Antes de procesar miles de archivos, prueba con pocos:

```bash
python converter.py \
  --input ./pdfs \
  --output ./test_output \
  --max-files 5
```

## 🖥️ GUI - Interfaz Gráfica

Para usuarios que prefieren interfaz visual:

```bash
python gui.py
```

Luego:
1. Click "➕ Agregar archivos" o "📁 Agregar carpeta"
2. Click "📂 Elegir" para carpeta de salida
3. Configurar opciones si es necesario
4. Click "🚀 Iniciar conversión"
5. Monitorear progreso en tiempo real

## 🔧 Solución de Problemas Comunes

### Error: "No se encontraron archivos PDF"
```bash
# Verifica que el patrón sea correcto
python converter.py --input ./pdfs --output ./docx --pattern "*.pdf"

# O usa búsqueda recursiva
python converter.py --input ./pdfs --output ./docx --recursive
```

### Error: Proceso muy lento
```bash
# Aumenta el número de workers
python converter.py --input ./pdfs --output ./docx --workers 12
```

### Error: Archivos se quedan "colgados"
```bash
# Usa timeout para evitar bloqueos
python converter.py --input ./pdfs --output ./docx --timeout-per-file 180
```

### Error: Memoria insuficiente
```bash
# Reduce workers y procesa en lotes
python converter.py --input ./pdfs --output ./docx --workers 2 --max-files 500
```

## 📝 Notas Importantes

1. **Espacio en disco**: DOCX suele ser 1.5-3x el tamaño del PDF
2. **Workers óptimos**: CPU cores - 1 o CPU cores - 2
3. **Timeout recomendado**: 180-300 segundos para archivos normales
4. **Lotes grandes**: Dividir en grupos de 500-1000 archivos
5. **PDFs escaneados**: Requieren OCR previo (no incluido)

## 🎯 Mejores Prácticas

- ✅ Siempre hacer prueba con pocos archivos primero
- ✅ Usar `--timeout-per-file` para lotes grandes
- ✅ Monitorear uso de memoria durante procesamiento
- ✅ Guardar logs con `2>&1 | tee log.txt`
- ✅ No usar más workers que cores disponibles
- ❌ No procesar desde/hacia unidades de red lentas
- ❌ No cerrar terminal durante procesamiento
- ❌ No sobrescribir sin backup (`--overwrite` con cuidado)
