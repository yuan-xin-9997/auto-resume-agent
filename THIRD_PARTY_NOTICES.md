# Third-party notices

Auto Resume Agent code and vector icon: MIT, copyright 2026 Yuan Xin.

Native GUI distributions include dynamically loaded PySide6, Shiboken6 and Qt libraries from the unmodified upstream wheels. These components are licensed under LGPLv3/GPLv3/commercial terms; this distribution uses the LGPLv3 option. Their license texts and upstream source links are distributed in `licenses/` beside each native archive's applications. You may replace the shared libraries with compatible modified versions and reverse engineer the application for debugging those modifications, as permitted by the LGPL. No additional restriction is imposed on those rights. Build the application from this repository with your replacement compatible wheels to relink.

- [Qt for Python licensing](https://doc.qt.io/qtforpython-6/licenses.html)
- [PySide/Shiboken source, v6.8.3](https://code.qt.io/cgit/pyside/pyside-setup.git/tree/?h=v6.8.3)
- [Qt source, v6.8.3](https://code.qt.io/cgit/qt/qtbase.git/tree/?h=v6.8.3)
- [PyInstaller](https://pyinstaller.org/en/stable/license.html): GPLv2 with bootloader distribution exception; frozen application remains MIT.
- Python: PSF License. Other included wheel and standard library notices are copied into `licenses/` during packaging.

Codex is an external prerequisite and is not bundled. Inspiration: [codex-auto-resume-windows](https://github.com/songyb111-gachon/codex-auto-resume-windows), MIT. No reference-project source files are vendored.
