import logging
import queue
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from typing import Optional

from converter import expand_inputs, process_batch

# Configure logging for GUI
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConverterGUI:
    """
    GUI application for converting PDF files to DOCX format.
    Provides a user-friendly interface for batch PDF conversion.
    """
    
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Conversor PDF → DOCX")
        self.root.geometry("900x700")
        self.input_paths: list[str] = []
        self.progress_queue: queue.Queue[int] = queue.Queue()
        self.worker_thread: Optional[threading.Thread] = None
        self.counts = None
        self.errors = None
        self.is_converting = False
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the user interface components."""
        main = ttk.Frame(self.root, padding=10)
        main.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Title
        title = ttk.Label(main, text="📄 Conversor Masivo PDF → DOCX", font=("Arial", 16, "bold"))
        title.grid(row=0, column=0, columnspan=3, pady=(0, 10))

        # Inputs list
        ttk.Label(main, text="📂 Entradas (archivos/carpetas PDF)", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w")
        
        # Frame for listbox and scrollbar
        list_frame = ttk.Frame(main)
        list_frame.grid(row=2, column=0, columnspan=3, sticky="nsew", pady=(0, 6))
        main.rowconfigure(2, weight=1)
        main.columnconfigure(1, weight=1)
        
        self.listbox = tk.Listbox(list_frame, height=8, selectmode=tk.EXTENDED)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        self.listbox.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        # Buttons for managing inputs
        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=3, column=0, columnspan=3, sticky="w", pady=(0, 8))
        ttk.Button(btn_frame, text="➕ Agregar archivos", command=self.add_files).grid(row=0, column=0, padx=(0, 6))
        ttk.Button(btn_frame, text="📁 Agregar carpeta", command=self.add_folder).grid(row=0, column=1, padx=(0, 6))
        ttk.Button(btn_frame, text="❌ Quitar selección", command=self.remove_selected).grid(row=0, column=2, padx=(0, 6))
        ttk.Button(btn_frame, text="🗑️ Limpiar todo", command=self.clear_all).grid(row=0, column=3)

        # Output directory selection
        ttk.Label(main, text="💾 Carpeta destino DOCX", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky="w", pady=(6, 0))
        out_frame = ttk.Frame(main)
        out_frame.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(0, 6))
        out_frame.columnconfigure(0, weight=1)
        self.output_var = tk.StringVar()
        ttk.Entry(out_frame, textvariable=self.output_var).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(out_frame, text="📂 Elegir", command=self.choose_output).grid(row=0, column=1)

        # Options section
        ttk.Label(main, text="⚙️ Opciones de conversión", font=("Arial", 10, "bold")).grid(row=6, column=0, sticky="w", pady=(6, 0))
        
        options = ttk.Frame(main)
        options.grid(row=7, column=0, columnspan=3, sticky="ew", pady=(6, 6))
        
        # Row 1 of options
        row1 = ttk.Frame(options)
        row1.pack(fill="x", pady=2)
        
        ttk.Label(row1, text="Patrón:").pack(side="left", padx=(0, 4))
        self.pattern_var = tk.StringVar(value="*.pdf")
        ttk.Entry(row1, width=12, textvariable=self.pattern_var).pack(side="left", padx=(0, 12))

        self.recursive_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(row1, text="Búsqueda recursiva", variable=self.recursive_var).pack(side="left", padx=(0, 12))

        ttk.Label(row1, text="Workers:").pack(side="left", padx=(0, 4))
        self.workers_var = tk.IntVar(value=4)
        ttk.Spinbox(row1, from_=1, to=32, width=5, textvariable=self.workers_var).pack(side="left", padx=(0, 12))

        self.overwrite_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(row1, text="Sobrescribir existentes", variable=self.overwrite_var).pack(side="left")
        
        # Row 2 of options
        row2 = ttk.Frame(options)
        row2.pack(fill="x", pady=2)
        
        ttk.Label(row2, text="Máx. archivos (dejar vacío = todos):").pack(side="left", padx=(0, 4))
        self.max_files_var = tk.StringVar()
        ttk.Entry(row2, width=10, textvariable=self.max_files_var).pack(side="left", padx=(0, 12))

        ttk.Label(row2, text="Timeout por archivo (segundos):").pack(side="left", padx=(0, 4))
        self.timeout_var = tk.StringVar()
        ttk.Entry(row2, width=10, textvariable=self.timeout_var).pack(side="left")

        # Progress section
        ttk.Label(main, text="📊 Progreso", font=("Arial", 10, "bold")).grid(row=8, column=0, sticky="w", pady=(6, 0))
        
        self.progress_var = tk.IntVar(value=0)
        self.progress_total = 0
        self.progress_bar = ttk.Progressbar(main, maximum=1, variable=self.progress_var)
        self.progress_bar.grid(row=9, column=0, columnspan=3, sticky="ew", pady=(6, 2))
        
        self.status_var = tk.StringVar(value="✅ Listo para convertir")
        status_label = ttk.Label(main, textvariable=self.status_var, font=("Arial", 9))
        status_label.grid(row=10, column=0, columnspan=3, sticky="w")

        # Log output area
        ttk.Label(main, text="📝 Registro de actividad", font=("Arial", 10, "bold")).grid(row=11, column=0, sticky="w", pady=(6, 0))
        
        self.log_text = scrolledtext.ScrolledText(main, height=8, width=80, state="disabled")
        self.log_text.grid(row=12, column=0, columnspan=3, sticky="nsew", pady=(6, 6))
        main.rowconfigure(12, weight=1)

        # Start button
        self.start_button = ttk.Button(main, text="🚀 Iniciar conversión", command=self.start_conversion)
        self.start_button.grid(row=13, column=0, columnspan=3, pady=(10, 0), ipadx=20, ipady=5)

    def log_message(self, message: str) -> None:
        """Add a message to the log text area."""
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")

    def clear_all(self) -> None:
        """Clear all input paths."""
        self.input_paths.clear()
        self.refresh_list()
        self.log_message("🗑️ Lista de entradas limpiada")

    def add_files(self) -> None:
        """Add individual PDF files to the conversion list."""
        filenames = filedialog.askopenfilenames(
            title="Seleccionar archivos PDF",
            filetypes=[("PDF", "*.pdf"), ("Todos", "*.*")]
        )
        if filenames:
            for name in filenames:
                self.input_paths.append(name)
            self.refresh_list()
            self.log_message(f"➕ Agregados {len(filenames)} archivo(s)")

    def add_folder(self) -> None:
        """Add a folder to search for PDF files."""
        folder = filedialog.askdirectory(title="Seleccionar carpeta con PDFs")
        if folder:
            self.input_paths.append(folder)
            self.refresh_list()
            self.log_message(f"📁 Carpeta agregada: {folder}")

    def remove_selected(self) -> None:
        """Remove selected items from the input list."""
        selected = list(self.listbox.curselection())
        if not selected:
            messagebox.showwarning("Sin selección", "Por favor selecciona al menos un elemento para eliminar.")
            return
        for index in reversed(selected):
            del self.input_paths[index]
        self.refresh_list()
        self.log_message(f"❌ Eliminados {len(selected)} elemento(s)")

    def choose_output(self) -> None:
        """Choose the output directory for DOCX files."""
        folder = filedialog.askdirectory(title="Seleccionar carpeta de salida")
        if folder:
            self.output_var.set(folder)
            self.log_message(f"💾 Carpeta de salida: {folder}")

    def refresh_list(self) -> None:
        """Refresh the listbox with current input paths."""
        self.listbox.delete(0, tk.END)
        for p in self.input_paths:
            self.listbox.insert(tk.END, p)

    def start_conversion(self) -> None:
        """Start the PDF to DOCX conversion process."""
        if self.is_converting:
            messagebox.showwarning("En progreso", "Ya hay una conversión en curso. Por favor espera a que termine.")
            return
            
        # Validate inputs
        if not self.input_paths:
            messagebox.showwarning("Faltan datos", "Por favor agrega al menos un archivo o carpeta PDF.")
            return
            
        output = self.output_var.get().strip()
        if not output:
            messagebox.showwarning("Faltan datos", "Por favor selecciona la carpeta de salida.")
            return

        # Get configuration
        pattern = self.pattern_var.get().strip() or "*.pdf"
        recursive = self.recursive_var.get()
        workers = max(1, self.workers_var.get())
        
        max_files_val = self.max_files_var.get().strip()
        max_files = None
        if max_files_val:
            try:
                max_files = int(max_files_val)
                if max_files <= 0:
                    messagebox.showerror("Valor inválido", "El máximo de archivos debe ser mayor a 0.")
                    return
            except ValueError:
                messagebox.showerror("Valor inválido", "El máximo de archivos debe ser un número entero.")
                return
        
        timeout_val = self.timeout_var.get().strip()
        timeout_secs = None
        if timeout_val:
            try:
                timeout_secs = float(timeout_val)
                if timeout_secs <= 0:
                    messagebox.showerror("Valor inválido", "El timeout debe ser mayor a 0.")
                    return
            except ValueError:
                messagebox.showerror("Valor inválido", "El timeout debe ser un número válido.")
                return
        
        overwrite = self.overwrite_var.get()

        # Expand files to get actual count
        try:
            files = expand_inputs(self.input_paths, pattern, recursive)
            if max_files is not None:
                files = files[:max_files]

            if not files:
                messagebox.showinfo("Sin archivos", "No se encontraron archivos PDF con los parámetros indicados.")
                return
        except Exception as e:
            messagebox.showerror("Error", f"Error al buscar archivos: {str(e)}")
            logger.error(f"Error al expandir entradas: {e}")
            return

        # Setup progress tracking
        self.progress_total = len(files)
        self.progress_bar.configure(maximum=self.progress_total)
        self.progress_var.set(0)
        self.status_var.set(f"🔄 Iniciando conversión de {self.progress_total} archivo(s)...")
        self.log_message(f"\n{'=' * 60}")
        self.log_message(f"🚀 Iniciando conversión de {self.progress_total} archivo(s)")
        self.log_message(f"⚙️  Workers: {workers}")
        self.log_message(f"📁 Carpeta salida: {output}")
        self.log_message(f"{'=' * 60}\n")

        self.progress_queue = queue.Queue()
        self.counts = None
        self.errors = None
        self.is_converting = True
        self.start_button.configure(state="disabled")

        def work() -> None:
            """Worker thread function to process batch conversion."""
            try:
                counts, errors = process_batch(
                    files,
                    Path(output),
                    workers,
                    overwrite,
                    timeout_secs,
                    progress_cb=lambda done, total: self.progress_queue.put(("progress", done)),
                )
                self.counts = counts
                self.errors = errors
                self.progress_queue.put(("done", None))
            except Exception as e:
                logger.error(f"Error en worker thread: {e}")
                self.progress_queue.put(("error", str(e)))

        self.worker_thread = threading.Thread(target=work, daemon=True)
        self.worker_thread.start()
        self.root.after(200, self._drain_progress)

    def _drain_progress(self) -> None:
        """Process progress updates from the worker thread."""
        while not self.progress_queue.empty():
            item_type, item_data = self.progress_queue.get()
            
            if item_type == "done":
                self.progress_var.set(self.progress_total)
                self.status_var.set("✅ Conversión terminada")
                self.is_converting = False
                self.start_button.configure(state="normal")
                self.log_message(f"\n{'=' * 60}")
                self.log_message("✅ Proceso de conversión completado")
                self.log_message(f"{'=' * 60}\n")
                self._show_summary()
                return
                
            elif item_type == "error":
                self.status_var.set("❌ Error en la conversión")
                self.is_converting = False
                self.start_button.configure(state="normal")
                self.log_message(f"❌ Error crítico: {item_data}")
                messagebox.showerror("Error", f"Error durante la conversión:\n{item_data}")
                return
                
            elif item_type == "progress":
                done = item_data
                self.progress_var.set(done)
                self.status_var.set(f"🔄 Procesando ({done}/{self.progress_total})")
                
        self.root.after(200, self._drain_progress)

    def _show_summary(self) -> None:
        """Display conversion summary in a message box and log."""
        if self.counts is None:
            return
            
        ok = self.counts.get("ok", 0)
        skipped = self.counts.get("skipped", 0)
        errors_n = self.counts.get("error", 0)
        
        # Log summary
        self.log_message(f"✅ Exitosos: {ok}")
        self.log_message(f"⏭️  Saltados: {skipped}")
        self.log_message(f"❌ Errores: {errors_n}")
        
        summary = f"Conversión completada:\n\n"
        summary += f"✅ Exitosos: {ok}\n"
        summary += f"⏭️  Saltados: {skipped}\n"
        summary += f"❌ Errores: {errors_n}"
        
        if self.errors:
            self.log_message(f"\n⚠️  Detalles de errores:")
            error_count = min(len(self.errors), 10)  # Show max 10 errors in popup
            summary += f"\n\nPrimeros {error_count} errores:"
            for i, (p, info) in enumerate(self.errors[:error_count]):
                error_line = f"\n  • {p.name if p != Path('') else 'General'}: {info}"
                summary += error_line
                self.log_message(f"  ❌ {p.name if p != Path('') else 'General'}: {info}")
            
            if len(self.errors) > error_count:
                summary += f"\n\n... y {len(self.errors) - error_count} error(es) más (ver log)"
                
        messagebox.showinfo("Resumen de conversión", summary)


def main() -> None:
    """Main entry point for the GUI application."""
    root = tk.Tk()
    try:
        ConverterGUI(root)
        root.mainloop()
    except Exception as e:
        logger.error(f"Error fatal en la GUI: {e}")
        messagebox.showerror("Error Fatal", f"Error al iniciar la aplicación:\n{str(e)}")


if __name__ == "__main__":
    main()
