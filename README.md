# Winston-Lutz Analysis Web App

A Streamlit web application for performing Winston-Lutz quality assurance analysis on EPID DICOM images, powered by [pylinac](https://github.com/jlleongarcia/pylinac).

## Features

- **Upload DICOM images** directly from the browser (up to 500 MB).
- **Configurable BB size** via the sidebar.
- **Automatic date extraction** from DICOM metadata (`AcquisitionDate`, `StudyDate`, or `ContentDate`).
- **Interactive results** displayed as text summary and Plotly charts.
- **Downloadable PDF report** with analysis date, summary figures, and individual image results.

## Running the app

There are two independent ways to run the app. Both install the same pinned dependency versions.

| | Local with uv | Docker |
|---|---|---|
| Best for | Development, running on a workstation | Deploying on a server |
| Requires | Python ≥ 3.13 and [uv](https://docs.astral.sh/uv/) | [Docker](https://docs.docker.com/get-docker/) with Compose |
| Installs from | `uv.lock` | `requirements.txt` (with pip, no uv) |
| Port | `8505`, configurable | `8505` inside the container, mapped in `docker-compose.yml` |

### Local with uv

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

### Docker

A multi-architecture image (`linux/amd64` and `linux/arm64`) is built by GitHub Actions and published to `ghcr.io/jlleongarcia/winston-lutz` on every push to `master`.

1. **Start the container** using the published image:

   ```bash
   docker compose pull
   docker compose up -d
   ```

   Or build the image locally instead:

   ```bash
   docker compose up -d --build
   ```

   The app will be accessible at `http://localhost:8505`. The container always listens on port `8505`; to serve it on a different host port, change the left side of the `ports` mapping in `docker-compose.yml` (e.g. `"8080:8505"`).

2. **Update to the latest image:**

   ```bash
   docker compose pull
   docker compose up -d
   ```

3. **Stop it:**

   ```bash
   docker compose down
   ```

> **Note:** If the published package is private on GitHub Container Registry, run `docker login ghcr.io` on the server before pulling, or make the package public in its GitHub settings. Building the image needs access to GitHub to fetch the pylinac fork; behind a corporate proxy, pass it with `--build-arg HTTPS_PROXY=...`.

#### How the image is built

- **Base image:** `python:3.13-slim`, with `git` added to fetch the pylinac fork.
- **Dependencies:** installed with `pip install --no-deps -r requirements.txt`. See [Why Docker installs with `--no-deps`](#why-docker-installs-with---no-deps).
- **Process:** Streamlit runs directly as the main process (not through `main.py`), so it receives the stop signal from `docker stop` and shuts down cleanly.
- **Security:** the app runs as a non-root user.
- **Health check:** Docker polls Streamlit's `/_stcore/health` endpoint, so `docker ps` shows whether the app is healthy.
- **Privacy:** Streamlit's usage statistics are disabled, given the clinical setting.

## Usage

1. Open the app in your browser.
2. Upload two or more Winston-Lutz DICOM (`.dcm`) images.
3. Adjust the **BB size** in the sidebar if needed (default: 8 mm).
4. View the analysis results, interactive plots, and download the PDF report.

## Dependencies

| Package | Version | Notes |
|---|---|---|
| Python | ≥ 3.13 | |
| [Streamlit](https://streamlit.io/) | 1.66.1 | |
| [pylinac](https://github.com/jlleongarcia/pylinac) | 3.50.0 | Fork, pinned to commit `0f02c1b` |
| [pydicom](https://pydicom.github.io/) | 3.0.2 | Overrides pylinac's `pydicom<3` cap (see below) |

`uv.lock` is the source of truth. `requirements.txt` is generated from it for the Docker image, so both ways of running the app use exactly the same versions.

### pylinac fork pinned to a commit

pylinac is installed from the [jlleongarcia/pylinac](https://github.com/jlleongarcia/pylinac) fork rather than from PyPI. The dependency in `pyproject.toml` names an exact commit so that relocking never moves to a newer, untested commit of the fork. To update pylinac, change the commit hash in `pyproject.toml` and [regenerate the lock files](#updating-dependencies).

### pydicom 3 override

#### The problem

This app and pylinac disagree about which pydicom versions are acceptable:

- **pylinac** (the fork) requires `pydicom>=2.0,<3`. The fork deliberately keeps the same constraint as upstream pylinac so that it stays aligned with it and can be merged.
- **This app** wants pydicom 3.

Left alone, pylinac's `<3` cap wins, and the app is held on pydicom 2.4.5.

#### Why this app uses pydicom 3

- **pydicom 3 is the maintained release line.** New fixes and features, such as the reworked pixel-data handling, land there. pydicom 2.x is the older line.
- **It keeps the app ready for future images.** Most EPID portal images are uncompressed, but the app should not be stuck on an old pydicom if compressed images appear. See the note on [compressed images](#compressed-images).
- **It has been checked for this app.** The full Winston-Lutz workflow (analysis, Plotly figures and PDF report) was run with pylinac 3.50.0 and pydicom 3.0.2, and the results are identical to those with pydicom 2.4.5. Upstream pylinac does not test against pydicom 3, so this check covers only the Winston-Lutz module, which is the only one this app uses.

#### How the override works

Rather than changing pylinac, this project tells uv to replace pylinac's pydicom requirement with its own, in `pyproject.toml`:

```toml
[tool.uv]
override-dependencies = ["pydicom>=3.0.2"]
```

uv then ignores pylinac's `<3` cap, resolves pydicom 3.0.2, and records it in `uv.lock`. Because `requirements.txt` is exported from `uv.lock`, it pins `pydicom==3.0.2` too. The pylinac fork itself is untouched.

#### Why Docker installs with `--no-deps`

The override is a uv feature. pip, which the Docker image uses, does not know about it.

When pip installs a package, it reads two things:

1. **The list you give it**, here `requirements.txt`, which asks for `pydicom==3.0.2`.
2. **Each package's own declared requirements**, which pip checks for consistency. pylinac declares `pydicom<3`.

These conflict, so a plain `pip install -r requirements.txt` stops with:

```
ERROR: Cannot install -r requirements.txt (line ...) and pydicom==3.0.2 because these package versions have conflicting dependencies.
ERROR: ResolutionImpossible
```

`--no-deps` tells pip to install exactly the packages listed and not to process each package's own requirements. pip then installs pydicom 3.0.2 as `requirements.txt` asks.

This is safe here because `requirements.txt` is not a hand-written list. It is generated from `uv.lock` and contains **every** package the app needs, including indirect ones, each at an exact version. pip has nothing left to work out, so the check that `--no-deps` skips adds nothing except the pydicom conflict. Two safeguards back this up:

- The [requirements sync workflow](#cicd) fails if `requirements.txt` is edited by hand or falls out of step with `uv.lock`, so a package can't silently go missing.
- The Docker build runs on every pull request, so an install problem shows up before it reaches `master`.

#### When to remove the override

Once pylinac allows pydicom 3:

1. Delete the `[tool.uv]` block from `pyproject.toml`.
2. [Regenerate the lock files](#updating-dependencies).
3. Change the Dockerfile back to a plain `pip install -r requirements.txt`.

#### Compressed images

pydicom reads uncompressed pixel data on its own, and most EPID portal images are uncompressed. Compressed formats (for example JPEG, JPEG-LS or JPEG 2000) also need a decoder package, such as `pylibjpeg` with its plugins or `gdcm`, whichever pydicom version is used. pydicom 3 does not remove this need. If you need to analyse compressed images, add the appropriate decoder to `pyproject.toml`.

### Updating dependencies

After changing dependencies in `pyproject.toml`, relock and regenerate `requirements.txt`:

```bash
uv lock
uv export --format requirements-txt --no-hashes --no-dev --no-emit-project --frozen -o requirements.txt
```

`requirements.txt` has no hashes because pip can't verify a hash for a dependency installed directly from a Git repository, such as the pylinac fork. Exact versions and the pinned commit still prevent unexpected upgrades.

## CI/CD

Two GitHub Actions workflows run on this repository:

- **`requirements-sync.yml`** runs on every push and pull request. It fails if `uv.lock` is out of date with `pyproject.toml`, or if `requirements.txt` doesn't match `uv.lock`. This keeps the local and Docker setups on the same versions.
- **`docker-publish.yml`** builds the image for `linux/amd64` and `linux/arm64`.
  - On pull requests to `master`, it only builds the image, to check that the Dockerfile still works.
  - On pushes to `master` (including merges), it also publishes the image to `ghcr.io/jlleongarcia/winston-lutz`, tagged `latest` and with the commit SHA.
  - It can also be started manually from the Actions tab.

## Project structure

```
├── main.py                     # Local entry point – launches Streamlit
├── app.py                      # Streamlit application
├── pyproject.toml              # Project metadata, dependencies and pydicom override
├── uv.lock                     # Locked dependency versions (source of truth)
├── requirements.txt            # Same versions exported for pip (Docker)
├── Dockerfile                  # Container image definition
├── docker-compose.yml          # Deployment configuration
├── .dockerignore               # Files excluded from the Docker build context
├── .github/workflows/
│   ├── requirements-sync.yml   # Checks requirements.txt matches uv.lock
│   └── docker-publish.yml      # Builds and publishes the multi-arch image
└── .streamlit/
    └── config.toml             # Streamlit config (upload limit)
```

## License

This project uses [pylinac](https://github.com/jlleongarcia/pylinac), which is licensed under the MIT License.
