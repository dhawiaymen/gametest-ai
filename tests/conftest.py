"""Keep Tcl interpreter destruction on the main thread between GUI tests."""
import gc
import os
import pytest


@pytest.fixture
def tk_root():
    import tkinter as tk
    gc.collect()
    try:
        root = tk.Tk()
    except tk.TclError:
        if os.environ.get("CI"):
            raise
        pytest.skip("No graphical display available")
    yield root
    root.destroy()
    del root
    # Tk widgets contain cycles; do not leave an old interpreter for a later
    # browser worker's garbage collection to finalize on the wrong thread.
    gc.collect()
