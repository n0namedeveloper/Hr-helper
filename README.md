# HR-Breaker

Инструмент для оптимизации резюме под конкретную вакансию с проверками на ATS-совместимость и правдоподобность.

![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)

## Что делает проект

- принимает резюме (txt/md/tex/html/pdf)
- принимает описание вакансии (URL, файл или текст)
- генерирует адаптированное резюме
- прогоняет его через набор фильтров (длина, ключевые слова, анти-халлюцинации, ATS-check)
- при провале фильтров пересобирает резюме с учётом фидбэка
- сохраняет финальный PDF

## Технологии

- Python 3.10+
- Pydantic-AI + Perplexity API
- Streamlit (Web UI)
- Click (CLI)
- WeasyPrint (HTML → PDF)
- PyMuPDF

## Быстрый старт

### 1) Установка зависимостей

```bash
uv sync
```

### 2) Настройка переменных окружения

```bash
cp .env.example .env
```

Заполните в .env:

```dotenv
PERPLEXITY_API_KEY=your_key_here
```

### 3) Запуск Web UI

```bash
uv run streamlit run src/hr_breaker/main.py
```

## Использование CLI

```bash
# URL вакансии
uv run hr-breaker optimize resume.txt https://example.com/job

# Вакансия из файла
uv run hr-breaker optimize resume.txt job.txt

# Debug-режим (сохраняет итерации)
uv run hr-breaker optimize resume.txt job.txt -d

# Последовательный режим фильтров
uv run hr-breaker optimize resume.txt job.txt --seq

# Lenient-режим
uv run hr-breaker optimize resume.txt job.txt --no-shame

# История сгенерированных PDF
uv run hr-breaker list
```

## Куда сохраняются результаты

- Финальные PDF: output/
- Debug-артефакты: output/debug_<company>_<role>/
- Индекс метаданных: output/index.json

## Конфигурация

Все основные параметры находятся в .env.example:

- PERPLEXITY_API_KEY — обязательный
- PERPLEXITY_PRO_MODEL / PERPLEXITY_FLASH_MODEL
- пороги фильтров FILTER_*
- ограничения длины RESUME_*
- настройки скрейпера SCRAPER_*

## Архитектура (кратко)

src/hr_breaker/

- agents/ — LLM-агенты
- filters/ — плагинные проверки качества
- services/ — скрейпинг, рендер, кеш
- models/ — Pydantic-модели
- orchestration.py — основной цикл оптимизации
- main.py — Streamlit UI
- cli.py — CLI-команды

## Разработка и тесты

```bash
# Все тесты (без live API)
uv run pytest tests/ -q

# Live API тесты (опционально)
RUN_LIVE_API_TESTS=1 uv run pytest tests/test_utils.py
```

PowerShell:

```powershell
$env:RUN_LIVE_API_TESTS='1'; uv run pytest tests/test_utils.py
```

## Частые проблемы

- Ошибка `PERPLEXITY_API_KEY not set`
	- проверьте .env и перезапустите процесс

- Пустой/неполный текст вакансии по URL
	- сайт может быть под Cloudflare; вставьте текст вакансии вручную

- WeasyPrint не генерирует PDF
	- проверьте корректность HTML/CSS шаблонов в templates/

## Лицензия

MIT, см. файл LICENSE.
