import threading
import queue
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from typing import Optional

from converter import expand_inputs, process_batch


class ConverterGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("PDF → DOCX (GUI)")
        self.input_paths: list[str] = []
        self.progress_queue: queue.Queue[int] = queue.Queue()
        self.worker_thread: Optional[threading.Thread] = None
        self.counts = None
        self.errors = None
        self._build_ui()

    def _build_ui(self) -> None:
        main = ttk.Frame(self.root, padding=10)
        main.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Inputs list
        ttk.Label(main, text="Entradas (archivos/carpetas PDF)").grid(row=0, column=0, sticky="w")
        self.listbox = tk.Listbox(main, height=6, selectmode=tk.EXTENDED)
        self.listbox.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=(0, 6))
        main.rowconfigure(1, weight=1)
        main.columnconfigure(1, weight=1)

        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=2, column=0, columnspan=3, sticky="w", pady=(0, 8))
        ttk.Button(btn_frame, text="Agregar archivos", command=self.add_files).grid(row=0, column=0, padx=(0, 6))
        ttk.Button(btn_frame, text="Agregar carpeta", command=self.add_folder).grid(row=0, column=1, padx=(0, 6))
        ttk.Button(btn_frame, text="Quitar seleccion", command=self.remove_selected).grid(row=0, column=2)

        # Output and options
        ttk.Label(main, text="Carpeta destino DOCX").grid(row=3, column=0, sticky="w")
        out_frame = ttk.Frame(main)
        out_frame.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(0, 6))
        out_frame.columnconfigure(0, weight=1)
        self.output_var = tk.StringVar()
        ttk.Entry(out_frame, textvariable=self.output_var).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(out_frame, text="Elegir", command=self.choose_output).grid(row=0, column=1)

        options = ttk.Frame(main)
        options.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(0, 6))
        ttk.Label(options, text="Patron").grid(row=0, column=0, sticky="w")
        self.pattern_var = tk.StringVar(value="*.pdf")
        ttk.Entry(options, width=12, textvariable=self.pattern_var).grid(row=0, column=1, padx=(0, 12))

        self.recursive_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options, text="Recursivo", variable=self.recursive_var).grid(row=0, column=2, padx=(0, 12))

        ttk.Label(options, text="Workers").grid(row=0, column=3, sticky="w")
        self.workers_var = tk.IntVar(value=4)
        ttk.Spinbox(options, from_=1, to=32, width=5, textvariable=self.workers_var).grid(row=0, column=4, padx=(0, 12))

        ttk.Label(options, text="Max archivos").grid(row=0, column=5, sticky="w")
        self.max_files_var = tk.StringVar()
        ttk.Entry(options, width=8, textvariable=self.max_files_var).grid(row=0, column=6, padx=(0, 12))

        ttk.Label(options, text="Timeout (s)").grid(row=0, column=7, sticky="w")
        self.timeout_var = tk.StringVar()
        ttk.Entry(options, width=8, textvariable=self.timeout_var).grid(row=0, column=8, padx=(0, 12))

        self.overwrite_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options, text="Sobrescribir existentes", variable=self.overwrite_var).grid(row=0, column=9)

        # Progress
        self.progress_var = tk.IntVar(value=0)
        self.progress_total = 0
        self.progress_bar = ttk.Progressbar(main, maximum=1, variable=self.progress_var)
        self.progress_bar.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(6, 2))
        self.status_var = tk.StringVar(value="Listo para convertir")
        ttk.Label(main, textvariable=self.status_var).grid(row=7, column=0, columnspan=3, sticky="w")

        # Start button
        ttk.Button(main, text="Iniciar conversion", command=self.start_conversion).grid(row=8, column=0, columnspan=3, pady=(10, 0))

    def add_files(self) -> None:
        filenames = filedialog.askopenfilenames(filetypes=[("PDF", "*.pdf"), ("Todos", "*.*")])
        for name in filenames:
            self.input_paths.append(name)
        self.refresh_list()

    def add_folder(self) -> None:
        folder = filedialog.askdirectory()
        if folder:
            self.input_paths.append(folder)
            self.refresh_list()

    def remove_selected(self) -> None:
        selected = list(self.listbox.curselection())
        if not selected:
            return
        for index in reversed(selected):
            del self.input_paths[index]
        self.refresh_list()

    def choose_output(self) -> None:
        folder = filedialog.askdirectory()
        if folder:
            self.output_var.set(folder)

    def refresh_list(self) -> None:
        self.listbox.delete(0, tk.END)
        for p in self.input_paths:
            self.listbox.insert(tk.END, p)

    def start_conversion(self) -> None:
        if not self.input_paths:
            messagebox.showwarning("Faltan datos", "Agrega al menos un archivo o carpeta.")
            return
        output = self.output_var.get().strip()
        if not output:
            messagebox.showwarning("Faltan datos", "Selecciona carpeta de salida.")
            return

        pattern = self.pattern_var.get().strip() or "*.pdf"
        recursive = self.recursive_var.get()
        workers = max(1, self.workers_var.get())
        max_files_val = self.max_files_var.get().strip()
        max_files = int(max_files_val) if max_files_val.isdigit() else None
        timeout_val = self.timeout_var.get().strip()
        timeout_secs = float(timeout_val) if timeout_val else None
        overwrite = self.overwrite_var.get()

        files = expand_inputs(self.input_paths, pattern, recursive)
        if max_files is not None:
            files = files[:max_files]

        if not files:
            messagebox.showinfo("Sin archivos", "No se encontraron PDFs con los parametros indicados.")
            return

        self.progress_total = len(files)
        self.progress_bar.configure(maximum=self.progress_total)
        self.progress_var.set(0)
        self.status_var.set(f"Procesando {self.progress_total} archivos...")

        self.progress_queue = queue.Queue()
        self.counts = None
        self.errors = None

        def work() -> None:
            counts, errors = process_batch(
                files,
                Path(output),
                workers,
                overwrite,
                timeout_secs,
                progress_cb=lambda done, total: self.progress_queue.put(done),
            )
            self.counts = counts
            self.errors = errors
            self.progress_queue.put("__done__")

        self.worker_thread = threading.Thread(target=work, daemon=True)
        self.worker_thread.start()
        self.root.after(200, self._drain_progress)

    def _drain_progress(self) -> None:
        while not self.progress_queue.empty():
            item = self.progress_queue.get()
            if item == "__done__":
                self.progress_var.set(self.progress_total)
                self.status_var.set("Conversion terminada")
                self._show_summary()
                return
            if isinstance(item, int):
                self.progress_var.set(item)
                self.status_var.set(f"Procesando ({item}/{self.progress_total})")
        self.root.after(200, self._drain_progress)

    def _show_summary(self) -> None:
        if self.counts is None:
            return
        ok = self.counts.get("ok", 0)
        skipped = self.counts.get("skipped", 0)
        errors_n = self.counts.get("error", 0)
        summary = f"OK: {ok}\nSaltados: {skipped}\nErrores: {errors_n}"
        if self.errors:
            summary += "\n\nErrores:\n" + "\n".join(f"- {p}: {info}" for p, info in self.errors)
        messagebox.showinfo("Resumen", summary)


def main() -> None:
    root = tk.Tk()
    ConverterGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
