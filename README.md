# Winston-Lutz Analysis Web App

A Streamlit web application for performing Winston-Lutz quality assurance analysis on EPID DICOM images, powered by [pylinac](https://github.com/jlleongarcia/pylinac).

## Features

- **Upload DICOM images** directly from the browser (up to 500 MB).
- **Configurable BB size** via the sidebar.
- **Automatic date extraction** from DICOM metadata (`AcquisitionDate`, `StudyDate`, or `ContentDate`).
- **Interactive results** displayed as text summary and Plotly charts.
- **Downloadable PDF report** with analysis date, summary figures, and individual image results.

## Requirements

- **Local:** Python ≥ 3.13 and the [uv](https://docs.astral.sh/uv/) package manager
- **Container:** [Docker](https://docs.docker.com/get-docker/)

## Running locally with uv

1. **Clone the repository:**

   ```bash
   git clone https://github.com/jlleongarcia/winston-lutz.git
   cd winston-lutz
   ```

2. **Install dependencies:**

   ```bash
   uv sync
   ```

3. **Run the app:**

   ```bash
   uv run python main.py
   ```

   The app will be accessible at `http://localhost:8505`. You can pass a custom port as an argument:

   ```bash
   uv run python main.py 8080
   ```

## Running with Docker

The Docker image installs dependencies with `pip` from `requirements.txt` and doesn't use uv.

1. **Build and start the container:**

   ```bash
   docker compose up -d --build
   ```

   The app will be accessible at `http://localhost:8505`. The container always listens on port `8505`; to serve it on a different host port, change the left side of the `ports` mapping in `docker-compose.yml` (e.g. `"8080:8505"`).

2. **Stop it:**

   ```bash
   docker compose down
   ```

## Updating dependencies

`uv.lock` is the source of truth. After changing dependencies in `pyproject.toml`, relock and regenerate `requirements.txt` so the Docker image installs the same versions:

```bash
uv lock
uv export --format requirements-txt --no-hashes --no-dev --no-emit-project --frozen -o requirements.txt
```

## Usage

1. Open the app in your browser.
2. Upload two or more Winston-Lutz DICOM (`.dcm`) images.
3. Adjust the **BB size** in the sidebar if needed (default: 8 mm).
4. View the analysis results, interactive plots, and download the PDF report.

## Project structure

```
├── main.py                 # Entry point – launches Streamlit
├── app.py                  # Streamlit application
├── pyproject.toml          # Project metadata and dependencies
├── uv.lock                 # Locked dependency versions (uv)
├── requirements.txt        # Same versions exported for pip (Docker)
├── Dockerfile              # Container image definition
├── docker-compose.yml      # Deployment configuration
├── .dockerignore           # Files excluded from the Docker build context
└── .streamlit/
    └── config.toml         # Streamlit config (upload limit)
```

## License

This project uses [pylinac](https://github.com/jlleongarcia/pylinac), which is licensed under the MIT License.