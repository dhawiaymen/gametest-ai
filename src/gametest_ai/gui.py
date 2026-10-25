import json
from importlib.resources import files
import tempfile
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import webbrowser
from .schema import validate_plan, fuzz_plan, load_plan


class TestApp(ttk.Frame):
    def __init__(self, root):
        super().__init__(root, padding=18)
        self.pack(fill="both", expand=True)
        root.title("GameTest AI · Browser test workbench")
        root.geometry("1000x820")
        root.minsize(800, 650)
        self.events = queue.Queue()
        self.cancel = threading.Event()
        self.busy = False
        self.report_path = None
        self.demo_directory = None
        ttk.Label(self, text="GameTest AI", font=("Segoe UI", 24, "bold")).pack(anchor="w")
        ttk.Label(
            self, text="Replay scenarios, find browser errors, and explore games with seeded input."
        ).pack(anchor="w", pady=(0, 14))
        form = ttk.Frame(self)
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)
        self.target = tk.StringVar()
        self.output = tk.StringVar()
        self.model = tk.StringVar(value="qwen2.5-coder:7b")
        for row, (label, var, fn) in enumerate(
            [
                ("HTML file or URL", self.target, self.choose_target),
                ("New report folder", self.output, self.choose_output),
            ]
        ):
            ttk.Label(form, text=label).grid(row=row, column=0, sticky="w", pady=6)
            ttk.Entry(form, textvariable=var).grid(row=row, column=1, sticky="ew", padx=8)
            ttk.Button(form, text="Browse", command=fn).grid(row=row, column=2)
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=12)
        for label, fn in [
            ("Load demo", self.load_demo),
            ("Open plan", self.open_plan),
            ("Save plan", self.save_plan),
            ("Seeded plan", self.seeded),
            ("Run tests", self.run),
            ("Cancel", self.stop),
            ("Open report", self.open_report),
        ]:
            ttk.Button(toolbar, text=label, command=fn).pack(side="left", padx=3)
        tabs = ttk.Notebook(self)
        tabs.pack(fill="both", expand=True)
        plan_tab = ttk.Frame(tabs, padding=8)
        tabs.add(plan_tab, text="Scenario JSON")
        self.editor = tk.Text(plan_tab, wrap="none", font=("Consolas", 10))
        self.editor.pack(fill="both", expand=True)
        scrollbar = ttk.Scrollbar(plan_tab, command=self.editor.yview)
        scrollbar.pack(side="right", fill="y")
        self.editor.configure(yscrollcommand=scrollbar.set)
        self.editor.insert("1.0", json.dumps(fuzz_plan(42, 100), indent=2))
        ai = ttk.Frame(tabs, padding=12)
        tabs.add(ai, text="Local AI planner (optional)")
        ttk.Label(
            ai,
            text="Describe the game, controls, expected behavior, and whether it has a GameTest adapter.",
        ).pack(anchor="w")
        self.description = tk.Text(ai, height=9, wrap="word")
        self.description.pack(fill="both", expand=True, pady=10)
        modelrow = ttk.Frame(ai)
        modelrow.pack(fill="x")
        ttk.Label(modelrow, text="Installed Ollama model").pack(side="left")
        ttk.Entry(modelrow, textvariable=self.model, width=30).pack(side="left", padx=10)
        ttk.Button(modelrow, text="Generate a draft plan", command=self.generate).pack(side="left")
        ttk.Label(
            ai,
            text="Requires Ollama running locally on port 11434. Generated plans are validated and require your review before running.",
            wraplength=800,
        ).pack(anchor="w", pady=12)
        self.status = tk.StringVar(
            value="Ready. Tests need Chromium: python -m playwright install chromium"
        )
        ttk.Label(self, textvariable=self.status).pack(anchor="w", pady=10)
        self.log = tk.Text(self, height=6, wrap="word", font=("Consolas", 10))
        self.log.pack(fill="x")
        self._poll_id = self.after(100, self.poll)
        root.protocol("WM_DELETE_WINDOW", self.close)

    def close(self):
        if self.busy:
            messagebox.showinfo(
                "Task running", "Cancel the test and wait for it to finish before closing."
            )
        else:
            self.winfo_toplevel().destroy()

    def destroy(self):
        self.after_cancel(self._poll_id)
        if self.demo_directory:
            self.demo_directory.cleanup()
        for name, value in list(vars(self).items()):
            if isinstance(value, tk.Variable):
                setattr(self, name, None)
        del value
        super().destroy()

    def load_demo(self):
        if self.busy:
            return
        if self.demo_directory is None:
            self.demo_directory = tempfile.TemporaryDirectory(prefix="gametest-demo-")
        directory = Path(self.demo_directory.name)
        resource = files("gametest_ai").joinpath("templates")
        for name in ("index.html", "game.js", "project.json", "LICENSE"):
            (directory / name).write_bytes(resource.joinpath(name).read_bytes())
        self.target.set(str(directory / "index.html"))
        self.set_plan(json.loads(resource.joinpath("tap-win.json").read_text(encoding="utf-8")))
        self.status.set("Demo loaded. Choose a new report folder, then Run tests.")

    def choose_target(self):
        p = filedialog.askopenfilename(filetypes=[("HTML games", "*.html *.htm")])
        if p:
            self.target.set(p)

    def choose_output(self):
        p = filedialog.asksaveasfilename(title="New report folder", initialfile="test-report")
        if p:
            self.output.set(p)

    def open_plan(self):
        p = filedialog.askopenfilename(filetypes=[("Test plans", "*.json")])
        if p:
            try:
                self.set_plan(load_plan(p))
            except (OSError, ValueError) as exc:
                messagebox.showerror("Invalid plan", str(exc))

    def set_plan(self, plan):
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", json.dumps(plan, indent=2))

    def get_plan(self):
        return validate_plan(json.loads(self.editor.get("1.0", "end")))

    def save_plan(self):
        try:
            plan = self.get_plan()
            p = filedialog.asksaveasfilename(defaultextension=".json")
            if p:
                Path(p).write_text(json.dumps(plan, indent=2), encoding="utf-8")
        except (OSError, ValueError) as exc:
            messagebox.showerror("Save failed", str(exc))

    def seeded(self):
        if messagebox.askyesno(
            "Replace plan", "Replace the editor with a seeded 480-pixel-wide exploration plan?"
        ):
            self.set_plan(fuzz_plan(42, 300))

    def start(self, fn):
        if self.busy:
            messagebox.showinfo("Busy", "Wait for the current task or cancel it.")
            return
        self.busy = True
        self.cancel.clear()
        self.status.set("Working…")
        self.log.delete("1.0", "end")

        def work():
            try:
                fn()
            except Exception as exc:
                self.events.put(("error", str(exc)))
            finally:
                self.events.put(("idle", None))

        threading.Thread(target=work, daemon=True).start()

    def run(self):
        try:
            plan = self.get_plan()
            target = self.target.get()
            output = self.output.get()
            if not target or not output:
                raise ValueError("Choose a target and a new report folder.")
        except ValueError as exc:
            messagebox.showerror("Invalid test", str(exc))
            return

        def work():
            from .runner import run_plan

            result = run_plan(
                target,
                plan,
                output,
                progress=lambda i, n, name, status: self.events.put(
                    ("log", f"{i}/{n} {name}: {status}")
                ),
                cancel=self.cancel,
            )
            self.events.put(("result", (result, str(Path(output).resolve() / "report.html"))))

        self.start(work)

    def generate(self):
        description = self.description.get("1.0", "end")
        model = self.model.get()

        def work():
            from .ai import generate_plan

            self.events.put(("plan", generate_plan(description, model)))

        self.start(work)

    def stop(self):
        self.cancel.set()
        self.status.set(
            "Cancellation requested. Browser steps finish within their timeout; local model requests may take up to 120 seconds."
        )

    def open_report(self):
        if self.report_path:
            webbrowser.open(Path(self.report_path).as_uri())

    def poll(self):
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == "idle":
                    self.busy = False
                elif kind == "plan":
                    self.set_plan(value)
                    self.status.set("Draft generated. Review the Scenario JSON before running.")
                elif kind == "error":
                    self.status.set("Task failed")
                    self.log.insert("end", value + "\n")
                elif kind == "result":
                    report, self.report_path = value
                    self.status.set(
                        f"{report['passed']} passed / {report['failed']} failed — report saved"
                    )
                else:
                    self.log.insert("end", str(value) + "\n")
        except queue.Empty:
            pass
        self._poll_id = self.after(100, self.poll)


def main():
    root = tk.Tk()
    ttk.Style().theme_use("clam")
    TestApp(root)
    root.mainloop()
