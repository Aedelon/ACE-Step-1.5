"""Cross-platform native OS folder picker.

Shells out to the host platform's built-in folder chooser so the Gradio
client can grab a path without needing to install extra dialogs. Only
useful when the Gradio server runs on the SAME machine as the browser
(the typical localhost dev setup).

- **macOS**: ``osascript`` (AppleScript ``choose folder``)
- **Linux**: ``zenity --file-selection --directory`` (GNOME default), with
  fallbacks to ``kdialog`` (KDE) if present
- **Windows**: PowerShell ``FolderBrowserDialog``

All commands time out after 5 minutes and return an empty string when
the user cancels, the picker is unavailable, or the command fails.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

_PICKER_TIMEOUT_SECONDS = 300


def _run(cmd: list[str], *, input_text: str | None = None) -> str:
    """Run *cmd*, return the stripped stdout, or "" on any failure."""
    try:
        result = subprocess.run(
            cmd,
            input=input_text,
            capture_output=True,
            text=True,
            timeout=_PICKER_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if result.returncode != 0:
        return ""
    return (result.stdout or "").strip()


def _pick_folder_macos(title: str) -> str:
    """Open the macOS native folder picker via AppleScript."""
    script = f'POSIX path of (choose folder with prompt "{title}")'
    return _run(["osascript", "-e", script])


def _pick_folder_linux(title: str) -> str:
    """Open a Linux native folder picker, trying zenity then kdialog."""
    if shutil.which("zenity"):
        return _run(
            [
                "zenity",
                "--file-selection",
                "--directory",
                f"--title={title}",
            ]
        )
    if shutil.which("kdialog"):
        return _run(
            ["kdialog", "--getexistingdirectory", os.getcwd(), "--title", title]
        )
    return ""


def _pick_folder_windows(title: str) -> str:
    """Open the Windows native folder picker via PowerShell."""
    escaped_title = title.replace("'", "''")
    script = (
        "Add-Type -AssemblyName System.Windows.Forms; "
        "$dialog = New-Object System.Windows.Forms.FolderBrowserDialog; "
        f"$dialog.Description = '{escaped_title}'; "
        "$dialog.ShowNewFolderButton = $false; "
        "if ($dialog.ShowDialog() -eq 'OK') { Write-Output $dialog.SelectedPath }"
    )
    return _run(
        [
            "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            script,
        ]
    )


def pick_folder(title: str = "Select a folder") -> str:
    """Open the native OS folder picker and return the chosen path.

    Args:
        title: Window title shown on the folder dialog.

    Returns:
        The absolute path of the chosen folder, or an empty string if
        the user cancelled or no native picker is available.
    """
    platform = sys.platform
    if platform == "darwin":
        return _pick_folder_macos(title)
    if platform == "win32":
        return _pick_folder_windows(title)
    # Treat everything else (Linux, BSD, etc.) as Linux-like.
    return _pick_folder_linux(title)


# --- Single-file picker ------------------------------------------------


#: Map of file extensions to their macOS Uniform Type Identifiers.
#: AppleScript's ``choose file of type {…}`` requires UTIs (not raw
#: extensions like "json") on modern macOS — passing ``"json"`` grays
#: out every JSON file in the dialog so the user cannot pick one.
#:
#: Reference: Apple's Uniform Type Identifier Reference
#: (https://developer.apple.com/library/archive/documentation/Miscellaneous/Reference/UTIRef/Articles/System-DeclaredUniformTypeIdentifiers.html).
#: Extensions without a well-known system UTI fall back to no filter
#: (user can still navigate to any file) — safer than a silent
#: empty dialog.
_MACOS_EXT_TO_UTI: dict[str, str] = {
    "json": "public.json",
    "txt": "public.plain-text",
    "csv": "public.comma-separated-values-text",
    "yaml": "public.yaml",
    "yml": "public.yaml",
    "xml": "public.xml",
    "html": "public.html",
    "py": "public.python-script",
    "sh": "public.shell-script",
    "md": "net.daringfireball.markdown",
    "pdf": "com.adobe.pdf",
    "wav": "com.microsoft.waveform-audio",
    "mp3": "public.mp3",
    "flac": "org.xiph.flac",
    "png": "public.png",
    "jpg": "public.jpeg",
    "jpeg": "public.jpeg",
}


def _pick_file_macos(title: str, extensions: tuple[str, ...]) -> str:
    """Open the macOS native file picker, optionally filtering by extension.

    The ``extensions`` tuple is translated to Uniform Type Identifiers
    via ``_MACOS_EXT_TO_UTI`` because ``choose file of type`` expects
    UTIs, not raw extensions. Extensions without a known UTI are
    dropped from the filter so the user can still pick them.
    """
    utis: list[str] = []
    for ext in extensions:
        clean = ext.lstrip(".").lower()
        uti = _MACOS_EXT_TO_UTI.get(clean)
        if uti:
            utis.append(uti)
    if utis:
        of_type = "of type {" + ", ".join(f'"{uti}"' for uti in utis) + "}"
    else:
        of_type = ""
    script = (
        f'POSIX path of (choose file with prompt "{title}"'
        f"{' ' + of_type if of_type else ''})"
    )
    return _run(["osascript", "-e", script])


def _pick_file_linux(title: str, extensions: tuple[str, ...]) -> str:
    """Open a Linux native file picker, trying zenity then kdialog."""
    if shutil.which("zenity"):
        cmd = ["zenity", "--file-selection", f"--title={title}"]
        if extensions:
            pattern = " ".join(f"*.{ext.lstrip('.')}" for ext in extensions)
            cmd.append(f"--file-filter={pattern}")
        return _run(cmd)
    if shutil.which("kdialog"):
        filter_arg = (
            ("*.{" + ",".join(ext.lstrip(".") for ext in extensions) + "}")
            if extensions
            else "*"
        )
        return _run(
            ["kdialog", "--getopenfilename", os.getcwd(), filter_arg, "--title", title]
        )
    return ""


def _pick_file_windows(title: str, extensions: tuple[str, ...]) -> str:
    """Open the Windows native file picker via PowerShell."""
    escaped_title = title.replace("'", "''")
    if extensions:
        exts = ";".join(f"*.{ext.lstrip('.')}" for ext in extensions)
        filter_line = f"Files ({exts})|{exts}|All files (*.*)|*.*"
    else:
        filter_line = "All files (*.*)|*.*"
    script = (
        "Add-Type -AssemblyName System.Windows.Forms; "
        "$dialog = New-Object System.Windows.Forms.OpenFileDialog; "
        f"$dialog.Title = '{escaped_title}'; "
        f"$dialog.Filter = '{filter_line}'; "
        "if ($dialog.ShowDialog() -eq 'OK') { Write-Output $dialog.FileName }"
    )
    return _run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script])


def pick_file(
    title: str = "Select a file",
    extensions: tuple[str, ...] = (),
) -> str:
    """Open the native OS file picker and return the chosen file path.

    Args:
        title: Window title shown on the file dialog.
        extensions: Optional allow-list of extensions (e.g. ``("json",)``).
            Pass an empty tuple to accept any file type.

    Returns:
        The absolute path of the chosen file, or an empty string if
        the user cancelled or no native picker is available.
    """
    platform = sys.platform
    if platform == "darwin":
        return _pick_file_macos(title, extensions)
    if platform == "win32":
        return _pick_file_windows(title, extensions)
    return _pick_file_linux(title, extensions)
