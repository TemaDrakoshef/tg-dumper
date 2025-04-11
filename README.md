# Telegram Dumper

Software for parsing dialogs and their contents from telegram accounts in TDATA format

## Technology Stack

- Python 3.10+
- uv
- Telethon
- Click
- Loguru
- Nuitka
- Ruff

## How To Use It

By default, the dependencies are managed with [uv](https://docs.astral.sh/uv/), go there and install it.

```console
uv sync
```

Then you can activate the virtual environment with:

```console
source .venv/bin/activate
```

Make sure your editor is using the correct Python virtual environment, with the interpreter at `.venv/bin/python`.

Run the project

```console
uv run ./main.py
```

## Compiling a project

To compile the project into a standalone executable, use Nuitka:

```console
nuitka --standalone --follow-imports --include-package=opentele --mingw64 --show-progress --onefile --output-dir=build main.py
```
