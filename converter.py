import argparse
import concurrent.futures
import multiprocessing
import time
from collections import Counter
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Tuple

from pdf2docx import Converter
from tqdm import tqdm

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
    collected = []
    for item in inputs:
        path = Path(item)
        if path.is_file() and path.suffix.lower() == ".pdf":
            collected.append(path)
        elif path.is_dir():
            glob_pattern = f"**/{pattern}" if recursive else pattern
            collected.extend(sorted(path.glob(glob_pattern)))
        else:
            print(f"Advertencia: {path} no es un archivo PDF ni carpeta; se omite.")
    # Elimina duplicados preservando orden
    seen = set()
    unique: List[Path] = []
    for p in collected:
        if p not in seen:
            unique.append(p)
            seen.add(p)
    return unique


def convert_single(pdf_path: Path, output_dir: Path, overwrite: bool) -> Result:
    output_dir.mkdir(parents=True, exist_ok=True)
    docx_path = output_dir / f"{pdf_path.stem}.docx"
    if docx_path.exists() and not overwrite:
        return "skipped", pdf_path, "DOCX ya existe"
    try:
        converter = Converter(str(pdf_path))
        converter.convert(str(docx_path), start=0, end=None)
        converter.close()
        return "ok", pdf_path, ""
    except Exception as exc:  # pragma: no cover - conversion depends on external files
        return "error", pdf_path, str(exc)


def process_batch(
    pdf_files: Iterable[Path],
    output_dir: Path,
    workers: int,
    overwrite: bool,
    timeout_secs: Optional[float] = None,
    progress_cb: Optional[Callable[[int, int], None]] = None,
) -> Tuple[Counter, List[Tuple[Path, str]]]:
    counts: Counter = Counter()
    errors: List[Tuple[Path, str]] = []
    files_list = pdf_files if isinstance(pdf_files, list) else list(pdf_files)
    total = len(files_list)
    if total == 0:
        return counts, errors

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        future_map = {
            executor.submit(convert_single, pdf_path, output_dir, overwrite): pdf_path
            for pdf_path in files_list
        }

        if timeout_secs is None:
            for future in tqdm(
                concurrent.futures.as_completed(future_map),
                total=len(future_map),
                desc="Convirtiendo",
                unit="pdf",
            ):
                status, pdf_path_res, info = future.result()
                counts[status] += 1
                if status == "error":
                    errors.append((pdf_path_res, info))
                if progress_cb is not None:
                    progress_cb(sum(counts.values()), total)
            return counts, errors

        start_times = {fut: time.time() for fut in future_map}
        pending = set(future_map.keys())

        while pending:
            done, still_pending = concurrent.futures.wait(
                pending,
                timeout=timeout_secs,
                return_when=concurrent.futures.FIRST_COMPLETED,
            )

            # Marca timeouts
            now = time.time()
            expired = [
                fut
                for fut in still_pending
                if now - start_times.get(fut, now) >= timeout_secs
            ]
            for fut in expired:
                fut.cancel()
                pdf_path_res = future_map[fut]
                counts["error"] += 1
                errors.append((pdf_path_res, f"Timeout > {timeout_secs}s"))
                pending.discard(fut)
                still_pending.discard(fut)
                if progress_cb is not None:
                    progress_cb(sum(counts.values()), total)

            for fut in done:
                pending.discard(fut)
                pdf_path_res = future_map[fut]
                try:
                    status, pdf_path_ret, info = fut.result()
                except Exception as exc:  # pragma: no cover
                    status, pdf_path_ret, info = "error", pdf_path_res, str(exc)
                counts[status] += 1
                if status == "error":
                    errors.append((pdf_path_ret, info))
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
    """API reutilizable para convertir PDFs a DOCX.

    Devuelve (counts, errors) para que otras interfaces (CLI/GUI) puedan usarlo.
    """

    output_dir = Path(output)
    pdf_files = expand_inputs(inputs, pattern, recursive)
    if not pdf_files:
        return Counter(), [(Path(""), "No se encontraron archivos PDF con los parametros dados")]  # sentinel message

    if max_files is not None:
        pdf_files = pdf_files[: max_files]

    counts, errors = process_batch(pdf_files, output_dir, workers, overwrite, timeout_secs)
    return counts, errors


def main() -> None:
    args = parse_args()
    pdf_files = expand_inputs(args.inputs, args.pattern, args.recursive)
    if not pdf_files:
        print("No se encontraron archivos PDF segun los parametros indicados.")
        return

    if args.max_files is not None:
        pdf_files = pdf_files[: args.max_files]

    print(f"Archivos a procesar: {len(pdf_files)}")
    counts, errors = process_batch(
        pdf_files,
        Path(args.output),
        args.workers,
        args.overwrite,
        args.timeout_per_file,
    )

    print("\nResumen:")
    print(f"  OK       : {counts.get('ok', 0)}")
    print(f"  Saltados : {counts.get('skipped', 0)}")
    print(f"  Errores  : {counts.get('error', 0)}")

    if errors:
        print("\nErrores detectados:")
        for path, info in errors:
            print(f"- {path}: {info}")


if __name__ == "__main__":
    main()
