# AI Research

AI Research is a local-first Streamlit dashboard for internet research and
executive briefings. It uses Ollama for model execution and keeps uploaded
session knowledge isolated from the shared project files.

## Requirements

- Python `>=3.10,<3.13` (Python 3.12 is recommended)
- [UV](https://docs.astral.sh/uv/)
- A reachable Ollama server and at least one available model

## Setup

From the repository root:

```bash
uv venv --python 3.12 .venv
uv sync --system-certs
```

Configure the Ollama connection in `.env` or the environment:

```dotenv
MODEL=ollama/llama3.1:latest
API_BASE=http://192.168.1.153:11434
```

Start Ollama and make the configured model available before launching the
dashboard.

## Dashboard

```bash
streamlit run src/my_research_crew/dashboard.py
```

The dashboard loads the available Ollama models and prefers
`gpt-oss:120b-cloud` when it is available. Otherwise, it uses the configured
`MODEL` value or the first available model.

### Research workspace

The Research workspace supports two mutually exclusive sources:

- **Internet** searches public web sources and does not read session knowledge.
- **Local knowledge** reads only the current session's uploaded knowledge and
  does not access the internet.

### Executive Briefing workspace

The Executive Briefing workspace accepts an executive question and optional
business context. It produces a CEO-led briefing with specialist CFO, COO, and
CIO assessments. Its Local knowledge mode uses the same current-session
knowledge collection as Research.

## Session Knowledge

Upload supported `.txt`, `.md`, `.csv`, `.json`, `.yaml`, `.yml`, or ZIP files
from either workspace. The collection is shared between Research and Executive
Briefing for the current browser session, but it is not shared with other
sessions or the project knowledge directory.

Individual files are limited to 2 MB and ZIP uploads to 50 MB. ZIP archives
are checked for unsafe paths, links, encryption, corruption, excessive file
counts, and excessive uncompressed size. Uploaded session knowledge is deleted
when the 10-minute session expires.

## Reports

Completed reports are stored as `report.md` under a unique directory in
`reports/`.

After a successful run, the dashboard provides:

- Markdown download containing the report's UTF-8 source
- On-demand PDF generation and download

PDF generation occurs only when requested. PDF output is generated in memory
and is not stored as a second permanent report artifact.

## Active Runs

Research and Executive Briefing runs execute in the background. While a run is
active, conflicting controls are disabled and a **Stop** action is available.

Stopping is cooperative: the request is handled at safe execution boundaries,
and a result received after cancellation is not published as a completed report.

## Workspace Names

The two workspace names can be customized independently from the sidebar:

- Research default: `Research Crew`
- Executive default: `Executive Briefing`

Leave either field blank to restore its default. Names are session-scoped and
do not rename the underlying Python classes, report directories, or source
identifiers.
