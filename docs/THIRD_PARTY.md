# Dependency licenses and distribution

Original project code and included demonstration assets are MIT licensed. Dependencies
retain their own terms; MIT does not relicense the bundled interpreter, GUI libraries,
image codecs, browser or packaging machinery.

| Component | License / notice |
|---|---|
| Python | Python Software Foundation license and bundled notices |
| Tcl/Tk | Tcl/Tk license; keep the upstream license files |
| Pillow (AssetFlow) | MIT-CMU in the inspected current wheel; native codecs have additional bundled notices |
| Playwright (GameTest AI) | Apache-2.0, including its copyright and notice files |
| pyee / greenlet | Their installed distribution license files are collected in the build inventory |
| Chromium / bundled Node.js | Their own licenses and third-party component notices, retained in the browser/driver directories |
| PyInstaller | GPL with the distribution exception supplied by upstream; build dependency |
| pytest, Ruff, build, setuptools, wheel | Development/build tooling; see exact installed metadata and notices |
| Ollama / chosen AI model | Optional external installations; no model weights redistributed |

The release contains `licenses/inventory.json` with installed names/versions and copied
license/notice paths. It is a build-environment inventory, not a claim that every listed
package is used at runtime. Python/Tcl/Tk notices are also copied explicitly. The browser
bundle retains upstream component files. `constraints-release.txt` pins build inputs;
update it only with passing tests and fresh dependency review.

A local pip-audit scan on 26 October 2026 reported no known advisories for the inspected
current environment. This database check is not proof of absence of vulnerabilities,
and it does not replace a Chromium security review. It covers the recorded versions,
not arbitrary future versions allowed by dependency ranges.
