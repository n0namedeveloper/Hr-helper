# HR-Breaker Copilot Instructions

## Project Overview

**HR-Breaker** is a resume optimization tool that transforms resumes into job-specific, ATS-friendly PDFs using LLM agents and multi-filter validation. The system:
1. Parses user resume (any text format) + job posting
2. Generates optimized HTML resume via Pydantic-AI agent
3. Runs resume through 7 pluggable filters (content length, ATS simulation, hallucination detection, keyword matching, etc.)
4. Regenerates with feedback if filters fail; repeats up to 5 iterations
5. Renders final HTML → PDF via WeasyPrint

**Tech Stack:** Python 3.10+, Pydantic-AI (LLM orchestration), Perplexity API, Streamlit (UI), Click (CLI), httpx, WeasyPrint, PyMuPDF

---

## Architecture Patterns

### 1. **Plugin-Based Filter System** (`src/hr_breaker/filters/`)
Filters are auto-registered plugins that evaluate optimized resumes:

```python
@FilterRegistry.register
class MyFilter(BaseFilter):
    name = "my-filter"
    priority = 25  # Lower = runs first (0-99), 100+ = runs last
    
    async def evaluate(self, optimized, job, source) -> FilterResult:
        # Return FilterResult(passed=bool, score=0.0-1.0, issues=[...], suggestions=[...])
```

- **Registry pattern:** `FilterRegistry.register` decorator auto-discovers filters
- **Priority system:** Filters sort by priority; sequential mode early-exits on failure
- **Parallel execution:** Default mode runs all filters concurrently; `--seq` runs sequentially
- **Key filters:** `ContentLengthChecker` (0), `DataValidator` (1), `HallucinationChecker` (3), `KeywordMatcher` (4), `LLMChecker` (5), `VectorSimilarityMatcher` (6), `AIGeneratedChecker` (7)

**Add new filter:** Create class in `filters/`, inherit `BaseFilter`, implement `evaluate()`, add `@FilterRegistry.register` decorator. No need to import elsewhere—registry auto-discovers.

### 2. **Pydantic-AI Agent Pattern** (`src/hr_breaker/agents/`)
All LLM interactions use Pydantic-AI agents with structured outputs via Perplexity API using OpenAI-compatible client:

```python
from pydantic_ai import Agent

# Uses helper function to configure Perplexity API
agent = create_perplexity_agent(
    model="sonar-pro",  # or "sonar" for faster/cheaper tasks
    result_type=OptimizedResume,
    system_prompt=SYSTEM_PROMPT,
)
result = await agent.run(user_prompt=..., context=...)
```

- **How it works:** `create_perplexity_agent()` sets environment variables (`OPENAI_API_KEY`, `OPENAI_BASE_URL`) for OpenAI-compatible Perplexity endpoint
- **Perplexity models:** `sonar-pro` (complex tasks), `sonar` (faster/cheaper tasks)
- **Agent functions:** Tools agents can call (e.g., `check_content_length()`, `parse_requirements()`)
- **Result types:** Return strong Pydantic models, not strings
- **Streaming:** Use `agent.run_stream()` for Streamlit UI feedback
- **Vision:** `combined_reviewer` uses PDF-to-image for visual ATS checking

### 3. **Orchestration Loop** (`src/hr_breaker/orchestration.py`)
Core workflow: `optimize_for_job()` function:

```
Parse job posting → Optimize resume (LLM) → Run filters (parallel/sequential)
  → If failed: collect feedback → Regenerate with feedback
  → Repeat until pass or max iterations (default 5)
  → Render HTML → PDF
```

- **Iteration context:** `IterationContext` tracks feedback across regenerations
- **Feedback format:** Filter suggestions feed into next LLM prompt as constraints
- **Exit conditions:** All filters pass OR max iterations reached OR `no_shame` mode (skips some checks)
- **Async-first:** All I/O is async; use `asyncio.gather()` for parallel tasks

### 4. **Data Models** (`src/hr_breaker/models/`)
Strong typing via Pydantic:
- `Resume` - Source resume data
- `JobPosting` - Structured job data (title, company, requirements, keywords)
- `OptimizedResume` - HTML output with metadata
- `ResumeSource` - Original resume for comparison (hallucination detection)
- `FilterResult`, `ValidationResult` - Filter evaluation results

**Pattern:** Use Pydantic for all data flows; avoid dicts. Models drive agent outputs.

---

## Critical Workflows

### Build & Setup
```bash
# Install dependencies (uses uv package manager)
uv sync

# Create .env from template
cp .env.example .env
# Add GOOGLE_API_KEY=<your-key>

# Run tests
pytest tests/

# Run web UI
uv run streamlit run src/hr_breaker/main.py

# Run CLI
uv run hr-breaker optimize <resume-file> <job-url-or-file> [--seq] [-d] [--no-shame]
```

### Debugging
- **Debug mode (`-d`):** Saves all iteration HTML/feedback to `output/debug_<company>_<role>/`
- **Log levels:** Set `LOG_LEVEL=DEBUG` env var to see agent prompts and filter results
- **Cost control:** Use `GEMINI_FLASH_MODEL=gemini-2.5-flash` + low `GEMINI_THINKING_BUDGET` for testing
- **Sequential mode (`--seq`):** Runs filters one-by-one, early-exits on failure (useful for debugging which filter fails)

### Testing
- Tests use `pytest` + `pytest-asyncio`
- Mocking: Mock `Agent.run()` to avoid LLM calls
- Fixtures in `conftest.py` provide sample resumes, jobs, models
- Filter tests: Test `evaluate()` with sample `OptimizedResume`, `JobPosting`, `ResumeSource`

---

## Project Conventions

### Naming & File Structure
- **Modules:** snake_case (e.g., `job_parser.py`)
- **Classes:** PascalCase (e.g., `JobPosting`, `HTMLRenderer`)
- **Constants:** UPPER_SNAKE_CASE (e.g., `TEMPLATE_DIR`)
- **Agents live in:** `agents/` - one file per agent function
- **Services live in:** `services/` - stateless utilities (rendering, scraping, caching)
- **Filters live in:** `filters/` - plugin system, auto-registered

### Async/Await
- **All I/O is async:** Network (httpx), LLM (Pydantic-AI), file parsing
- **Sync code only:** Config loading, logging, model validation
- **Nest asyncio:** Streamlit uses `nest_asyncio.apply()` to run async in sync context
- **Run loop:** CLI uses `asyncio.run()`, Streamlit uses `run_async()` helper

### Environment Variables
Core settings in [config.py](src/hr_breaker/config.py):
- `PERPLEXITY_API_KEY` - Required; Perplexity API key
- `PERPLEXITY_PRO_MODEL`, `PERPLEXITY_FLASH_MODEL` - LLM model IDs (defaults: sonar-pro, sonar)
- `LOG_LEVEL` - Debug logging for project code
- Filter thresholds: `FILTER_HALLUCINATION_THRESHOLD`, `FILTER_KEYWORD_THRESHOLD`, etc.
- Resume limits: `RESUME_MAX_CHARS`, `RESUME_MAX_WORDS` (enforce one-page fit)

### Resume Length Estimation
- `length_estimator.py` estimates content length **before rendering** to fail fast
- Used by optimizer agent to trim content
- Authoritative check: render PDF and count pages (`WeasyPrint` → page count)
- Target: ~500 words, ~4000 characters to fit one page (with formatting overhead)

---

## Key Integration Points

### Job Scraping Pipeline
[`services/job_scraper.py`](src/hr_breaker/services/job_scraper.py) uses multi-strategy scraping:
1. **httpx (fast):** Direct HTTP request
2. **Wayback Machine (reliable):** Fallback if recent pages fail
3. **Playwright (JS-heavy):** Last resort for dynamic content

Returns job text; `job_parser` agent extracts structured data.

### Hallucination Detection
[`HallucinationChecker`](src/hr_breaker/filters/hallucination_checker.py) compares:
- Original resume (source) → What the user actually claimed
- Optimized resume (output) → What optimizer generated

Uses LLM to detect fabricated claims not in source. Threshhold: 0.9 (very high confidence required to flag).

### Keyword Matching
[`KeywordMatcher`](src/hr_breaker/filters/keyword_matcher.py) uses TF-IDF:
- Extract keywords from job posting
- Score optimized resume against keywords
- Suggest missing keywords in feedback
- Threshold: 0.25 (25% keyword coverage min)

### ATS Simulation
[`LLMChecker`](src/hr_breaker/filters/llm_checker.py) uses vision + text:
- Render resume as image
- Feed to vision LLM ("act as ATS parser")
- Score likelihood of passing ATS parsing
- Provides concrete feedback (e.g., "dates not detected", "no contact info")

---

## Common Tasks & Patterns

**Adding a new filter:**
1. Create `filters/my_filter.py` with class inheriting `BaseFilter`
2. Implement `async def evaluate(...)` returning `FilterResult`
3. Add `@FilterRegistry.register` decorator
4. Test in `tests/test_filters.py` with sample data

**Modifying LLM prompts:**
1. Agent system prompts live in agent files (e.g., `OPTIMIZER_BASE` in `agents/optimizer.py`)
2. Use f-string templates to inject dynamic content
3. Test with low budget: `GEMINI_THINKING_BUDGET=1024`

**Handling rendering errors:**
- `HTMLRenderer.render()` raises `RenderError` on WeasyPrint failure
- Check `RenderError.details` for WeasyPrint error message
- Common issues: invalid CSS, unsupported fonts, broken HTML structure

**Resume caching:**
- Cache stores parsed resumes by hash
- Useful for applying same resume to multiple jobs
- Located at `cache_dir` (default `.cache/resumes/`)

---

## Testing Tips

- Use `conftest.py` fixtures: `sample_resume`, `sample_job`, `sample_optimized_resume`
- Mock `Agent.run()` to avoid LLM costs: `mocker.patch("pydantic_ai.Agent.run")`
- For integration tests: use real Gemini but with cheap models (`gemini-2.5-flash`)
- Async tests: mark with `@pytest.mark.asyncio`

---

## References

- [Pydantic-AI docs](https://ai.pydantic.dev/)
- [Google Gemini API](https://ai.google.dev/)
- [WeasyPrint docs](https://weasyprint.org/)
- [Streamlit docs](https://docs.streamlit.io/)
