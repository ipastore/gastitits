# gastitits
Automatización de gastos en casa

## Installation

This project uses **[uv](https://docs.astral.sh/uv/)** for Python and dependency management.  
It reads dependencies from `pyproject.toml` and creates an isolated virtual environment for the project.

### 1. Install `uv` (one-time)

Follow the official instructions for your OS. On macOS / Linux, a typical install looks like:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

After installation, make sure uv is on your PATH (restart your terminal if needed):
```bash
uv --version
```

### 2. Clone the repository
git clone https://github.com/ipastore/gastitits.git
cd gastitis

### 3. Create the environment and install dependencies

```bash
uv sync
```

### 4. Verify the installation

```bash
uv run python -c "import pandas, yaml, dateutil, pyarrow, typer; print('OK: all core dependencies imported')"
```