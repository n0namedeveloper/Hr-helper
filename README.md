# HR-helper

A resume optimization tool that tailors resumes to specific job postings with ATS and credibility checks.

![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)

## What the project does

- accepts resume input (txt/md/tex/html/pdf)
- accepts job description input (URL, file, or raw text)
- generates a job-tailored resume
- validates it through multiple filters (length, keywords, anti-hallucination, ATS check)
- regenerates with feedback if filters fail
- saves the final PDF

## Tech stack

- Python 3.10+
- Pydantic-AI + Perplexity API
- Streamlit (web UI)
- Click (CLI)
- WeasyPrint (HTML → PDF)
- PyMuPDF

## Quick start

### 1) Install dependencies

```bash
uv sync
```

### 2) Configure environment variables

```bash
cp .env.example .env
```

Set this in .env:

```dotenv
PERPLEXITY_API_KEY=your_key_here
```

### 3) Run the web UI

```bash
uv run streamlit run src/hr_breaker/main.py
```

## CLI usage

```bash
# Job URL
uv run hr-breaker optimize resume.txt https://example.com/job

# Job description from a file
uv run hr-breaker optimize resume.txt job.txt

# Debug mode (saves iterations)
uv run hr-breaker optimize resume.txt job.txt -d

# Sequential filter mode
uv run hr-breaker optimize resume.txt job.txt --seq

# Lenient mode
uv run hr-breaker optimize resume.txt job.txt --no-shame

# List generated PDFs
uv run hr-breaker list
```

## Output locations

- Final PDFs: output/
- Debug artifacts: output/debug_<company>_<role>/
- Metadata index: output/index.json

## Configuration

Main settings are in .env.example:

- PERPLEXITY_API_KEY — required
- PERPLEXITY_PRO_MODEL / PERPLEXITY_FLASH_MODEL
- filter thresholds FILTER_*
- resume length limits RESUME_*
- scraper settings SCRAPER_*

## Architecture (short)

src/hr_breaker/

- agents/ — LLM agents
- filters/ — pluggable quality checks
- services/ — scraping, rendering, cache
- models/ — Pydantic models
- orchestration.py — core optimization loop
- main.py — Streamlit UI
- cli.py — CLI commands

## Development and tests

```bash
# All tests (without live API)
uv run pytest tests/ -q

# Live API tests (optional)
RUN_LIVE_API_TESTS=1 uv run pytest tests/test_utils.py
```

PowerShell:

```powershell
$env:RUN_LIVE_API_TESTS='1'; uv run pytest tests/test_utils.py
```

## Common issues

- Error `PERPLEXITY_API_KEY not set`
	- check .env and restart the process

- Empty/incomplete job text from URL
	- the site may be behind Cloudflare; paste the job description manually

- WeasyPrint fails to generate PDF
	- verify HTML/CSS templates in templates/

## License

MIT, see LICENSE.
