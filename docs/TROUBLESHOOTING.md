# Troubleshooting

| Symptom | What to do |
|---|---|
| EXE does not start | Extract the entire ZIP to a writable folder. Check its SHA-256, retain `_internal`, and report OS/version plus any error. Do not disable security tools. |
| Python launcher missing | Install Python 3.11–3.13 with the launcher and Tcl/Tk, or use the portable release. |
| `No module named tkinter` | Repair Python with Tcl/Tk enabled; on Linux install the OS Tk package and use a display. |
| Output already exists | Choose a new output directory. Tools protect previous results. |
| Permission denied | Use a directory you own; close programs holding the relevant files. |
| GUI appears clipped | Try maximizing the window. Report display resolution and scaling; high-DPI manual coverage remains limited. |
| Test says skipped | Read the reason. GUI checks need a display and Studio runtime tests need Node.js. |
| Browser executable missing | Source users must install Chromium from the same Playwright environment. Portable users should re-extract the complete official archive. |
| Scenario fails | Open report.json and the scenario screenshot; inspect the first error and the saved plan. A failed assertion is a test result, not a runner crash. |
| AI planner unavailable | Start local Ollama and install the exact model name, or use handwritten/seeded plans without AI. |
| Image becomes larger | Lossless re-encoding can increase size. Inspect the real byte totals; choose WebP or lossy quality when appropriate. |
| Atlas will not fit | Increase the limit or split the input. Shelf packing does not guarantee an optimal layout. |

Before filing an issue, reproduce with the included example and a new output folder.
Attach a minimal non-sensitive input, expected/actual behavior, version and environment.
Never attach private assets, credentials, or a full home directory.
