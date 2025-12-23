import argparse
import concurrent.futures
import logging
import multiprocessing
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Tuple

from pdf2docx import Converter
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

Result = Tuple[str, Path, str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convierte uno o varios PDFs a DOCX en paralelo."
    )
    parser.add_argument(
        "--input",
        dest="inputs",
        action="append",
        required=True,
        help="Ruta de carpeta o archivo PDF. Se puede repetir.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Carpeta destino para los DOCX.",
    )
    parser.add_argument(
        "--pattern",
        default="*.pdf",
        help="Patron glob para buscar PDFs (por defecto *.pdf).",
    )
    parser.add_argument(
        "--recursive",
        dest="recursive",
        action="store_true",
        default=True,
        help="Busca en subcarpetas (por defecto).",
    )
    parser.add_argument(
        "--no-recursive",
        dest="recursive",
        action="store_false",
        help="Desactiva la busqueda en subcarpetas.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=max(1, multiprocessing.cpu_count() - 1),
        help="Numero de hilos concurrentes (por defecto CPU-1).",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        help="Limita la cantidad de archivos a procesar (para lotes enormes).",
    )
    parser.add_argument(
        "--timeout-per-file",
        type=int,
        default=None,
        help="Tiempo maximo en segundos por archivo; si se excede, se marca error y se continua.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Reescribe DOCX existentes si ya hay un archivo convertido.",
    )
    return parser.parse_args()


def expand_inputs(inputs: List[str], pattern: str, recursive: bool) -> List[Path]:
    """
    Expand input paths (files or directories) into a list of PDF files.
    
    Args:
        inputs: List of file or directory paths
        pattern: Glob pattern to filter PDF files (e.g., "*.pdf")
        recursive: Whether to search recursively in directories
        
    Returns:
        List of unique PDF file paths
    """
    collected = []
    for item in inputs:
        path = Path(item)
        if path.is_file() and path.suffix.lower() == ".pdf":
            collected.append(path)
            logger.debug(f"Archivo agregado: {path}")
        elif path.is_dir():
            glob_pattern = f"**/{pattern}" if recursive else pattern
            found_files = sorted(path.glob(glob_pattern))
            collected.extend(found_files)
            logger.debug(f"Carpeta explorada: {path} - {len(found_files)} archivos encontrados")
        else:
            logger.warning(f"Advertencia: {path} no es un archivo PDF ni carpeta válida; se omite.")
    
    # Remove duplicates while preserving order
    seen = set()
    unique: List[Path] = []
    for p in collected:
        if p not in seen:
            unique.append(p)
            seen.add(p)
    
    logger.info(f"Total de archivos únicos encontrados: {len(unique)}")
    return unique


def convert_single(pdf_path: Path, output_dir: Path, overwrite: bool) -> Result:
    """
    Convert a single PDF file to DOCX format.
    
    Args:
        pdf_path: Path to the PDF file to convert
        output_dir: Directory where the DOCX file will be saved
        overwrite: Whether to overwrite existing DOCX files
        
    Returns:
        Tuple of (status, pdf_path, error_message)
        status can be: "ok", "skipped", or "error"
    """
    converter = None
    try:
        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        docx_path = output_dir / f"{pdf_path.stem}.docx"
        
        # Check if file already exists
        if docx_path.exists() and not overwrite:
            logger.info(f"Saltando {pdf_path.name} - ya existe")
            return "skipped", pdf_path, "DOCX ya existe"
        
        # Validate input file
        if not pdf_path.exists():
            error_msg = "El archivo PDF no existe"
            logger.error(f"Error en {pdf_path.name}: {error_msg}")
            return "error", pdf_path, error_msg
            
        if pdf_path.stat().st_size == 0:
            error_msg = "El archivo PDF está vacío"
            logger.error(f"Error en {pdf_path.name}: {error_msg}")
            return "error", pdf_path, error_msg
        
        # Convert with proper cleanup using try/finally
        logger.debug(f"Convirtiendo {pdf_path.name}...")
        converter = Converter(str(pdf_path))
        converter.convert(str(docx_path), start=0, end=None)
        
        logger.info(f"✓ Convertido: {pdf_path.name}")
        return "ok", pdf_path, ""
        
    except MemoryError as exc:
        error_msg = "Memoria insuficiente para procesar este archivo"
        logger.error(f"Error de memoria en {pdf_path.name}: {error_msg}")
        return "error", pdf_path, error_msg
        
    except PermissionError as exc:
        error_msg = f"Sin permisos para acceder al archivo: {str(exc)}"
        logger.error(f"Error de permisos en {pdf_path.name}: {error_msg}")
        return "error", pdf_path, error_msg
        
    except Exception as exc:
        error_msg = f"{type(exc).__name__}: {str(exc)}"
        logger.error(f"Error en {pdf_path.name}: {error_msg}")
        return "error", pdf_path, error_msg
        
    finally:
        # Ensure converter is always closed to prevent hanging
        if converter is not None:
            try:
                converter.close()
            except Exception as e:
                logger.warning(f"Error al cerrar converter para {pdf_path.name}: {e}")


def process_batch(
    pdf_files: Iterable[Path],
    output_dir: Path,
    workers: int,
    overwrite: bool,
    timeout_secs: Optional[float] = None,
    progress_cb: Optional[Callable[[int, int], None]] = None,
) -> Tuple[Counter, List[Tuple[Path, str]]]:
    """
    Process a batch of PDF files in parallel.
    
    Args:
        pdf_files: Iterable of PDF file paths to convert
        output_dir: Directory where DOCX files will be saved
        workers: Number of concurrent workers
        overwrite: Whether to overwrite existing DOCX files
        timeout_secs: Optional timeout in seconds for each file
        progress_cb: Optional callback function to report progress
        
    Returns:
        Tuple of (counts, errors) where:
        - counts: Counter with status counts (ok, skipped, error)
        - errors: List of (path, error_message) tuples for failed conversions
    """
    counts: Counter = Counter()
    errors: List[Tuple[Path, str]] = []
    files_list = pdf_files if isinstance(pdf_files, list) else list(pdf_files)
    total = len(files_list)
    
    if total == 0:
        logger.warning("No hay archivos para procesar")
        return counts, errors

    logger.info(f"Iniciando conversión de {total} archivos con {workers} workers...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        future_map = {
            executor.submit(convert_single, pdf_path, output_dir, overwrite): pdf_path
            for pdf_path in files_list
        }

        if timeout_secs is None:
            # Process without timeout
            for future in tqdm(
                concurrent.futures.as_completed(future_map),
                total=len(future_map),
                desc="Convirtiendo",
                unit="pdf",
            ):
                try:
                    status, pdf_path_res, info = future.result()
                    counts[status] += 1
                    if status == "error":
                        errors.append((pdf_path_res, info))
                    if progress_cb is not None:
                        progress_cb(sum(counts.values()), total)
                except Exception as exc:
                    # Handle unexpected errors from future.result()
                    pdf_path_res = future_map.get(future, Path("unknown"))
                    logger.error(f"Error inesperado procesando {pdf_path_res}: {exc}")
                    counts["error"] += 1
                    errors.append((pdf_path_res, str(exc)))
                    if progress_cb is not None:
                        progress_cb(sum(counts.values()), total)
            return counts, errors

        # Process with timeout
        start_times = {fut: time.time() for fut in future_map}
        pending = set(future_map.keys())
        processed = 0
        
        # Calculate check interval: min of 5 seconds or half the timeout
        check_interval = min(timeout_secs / 2, 5.0) if timeout_secs else 5.0

        with tqdm(total=total, desc="Convirtiendo", unit="pdf") as pbar:
            while pending:
                done, still_pending = concurrent.futures.wait(
                    pending,
                    timeout=check_interval,
                    return_when=concurrent.futures.FIRST_COMPLETED,
                )

                # Check for timeouts
                now = time.time()
                expired = [
                    fut
                    for fut in still_pending
                    if now - start_times.get(fut, now) >= timeout_secs
                ]
                
                for fut in expired:
                    fut.cancel()
                    pdf_path_res = future_map[fut]
                    error_msg = f"Timeout > {timeout_secs}s"
                    logger.warning(f"Timeout en {pdf_path_res.name}: {error_msg}")
                    counts["error"] += 1
                    errors.append((pdf_path_res, error_msg))
                    pending.discard(fut)
                    still_pending.discard(fut)
                    processed += 1
                    pbar.update(1)
                    if progress_cb is not None:
                        progress_cb(sum(counts.values()), total)

                # Process completed tasks
                for fut in done:
                    pending.discard(fut)
                    pdf_path_res = future_map[fut]
                    try:
                        status, pdf_path_ret, info = fut.result()
                    except Exception as exc:
                        logger.error(f"Error inesperado en {pdf_path_res.name}: {exc}")
                        status, pdf_path_ret, info = "error", pdf_path_res, str(exc)
                    
                    counts[status] += 1
                    if status == "error":
                        errors.append((pdf_path_ret, info))
                    processed += 1
                    pbar.update(1)
                    if progress_cb is not None:
                        progress_cb(sum(counts.values()), total)
                        
    return counts, errors


def run_conversion(
    inputs: List[str],
    output: str,
    pattern: str = "*.pdf",
    recursive: bool = True,
    workers: int = max(1, multiprocessing.cpu_count() - 1),
    max_files: Optional[int] = None,
    overwrite: bool = False,
    timeout_secs: Optional[float] = None,
) -> Tuple[Counter, List[Tuple[Path, str]]]:
    """
    API reusable for converting PDFs to DOCX.
    
    Args:
        inputs: List of input file or directory paths
        output: Output directory path for DOCX files
        pattern: Glob pattern to filter PDF files (default: "*.pdf")
        recursive: Whether to search recursively in directories (default: True)
        workers: Number of concurrent workers (default: CPU count - 1)
        max_files: Optional limit on number of files to process
        overwrite: Whether to overwrite existing DOCX files (default: False)
        timeout_secs: Optional timeout in seconds for each file conversion
        
    Returns:
        Tuple of (counts, errors) for use by CLI/GUI interfaces
    """
    logger.info("=" * 60)
    logger.info("Iniciando proceso de conversión PDF → DOCX")
    logger.info("=" * 60)
    
    output_dir = Path(output)
    
    # Validate output directory
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        error_msg = f"Sin permisos para crear el directorio de salida: {output_dir}"
        logger.error(error_msg)
        return Counter(), [(Path(""), error_msg)]
    
    # Expand and validate input files
    pdf_files = expand_inputs(inputs, pattern, recursive)
    if not pdf_files:
        error_msg = "No se encontraron archivos PDF con los parámetros dados"
        logger.warning(error_msg)
        return Counter(), [(Path(""), error_msg)]

    # Apply file limit if specified
    if max_files is not None:
        logger.info(f"Limitando a {max_files} archivos de {len(pdf_files)} encontrados")
        pdf_files = pdf_files[:max_files]

    # Process the batch
    counts, errors = process_batch(pdf_files, output_dir, workers, overwrite, timeout_secs)
    
    logger.info("=" * 60)
    logger.info("Proceso de conversión completado")
    logger.info("=" * 60)
    
    return counts, errors


def main() -> None:
    """
    Main entry point for CLI interface.
    Parses arguments and initiates the PDF to DOCX conversion process.
    """
    args = parse_args()
    
    # Expand input files
    pdf_files = expand_inputs(args.inputs, args.pattern, args.recursive)
    if not pdf_files:
        logger.error("❌ No se encontraron archivos PDF según los parámetros indicados.")
        return

    # Apply file limit if specified
    if args.max_files is not None:
        pdf_files = pdf_files[:args.max_files]

    logger.info(f"📂 Archivos a procesar: {len(pdf_files)}")
    logger.info(f"⚙️  Workers: {args.workers}")
    logger.info(f"📁 Carpeta de salida: {args.output}")
    
    # Process batch
    counts, errors = process_batch(
        pdf_files,
        Path(args.output),
        args.workers,
        args.overwrite,
        args.timeout_per_file,
    )

    # Print summary
    print("\n" + "=" * 60)
    print("RESUMEN DE CONVERSIÓN")
    print("=" * 60)
    print(f"✅ Exitosos     : {counts.get('ok', 0)}")
    print(f"⏭️  Saltados     : {counts.get('skipped', 0)}")
    print(f"❌ Errores      : {counts.get('error', 0)}")
    print("=" * 60)

    if errors:
        print("\n⚠️  DETALLES DE ERRORES:")
        print("-" * 60)
        for path, info in errors:
            print(f"  📄 {path.name if path != Path('') else 'General'}")
            print(f"     ↳ {info}")
        print("-" * 60)


if __name__ == "__main__":
    main()
