# Project Structure

## Root Directory
- `main.py` - Main entry point
- `pyproject.toml` - Project configuration
- `README.md` - Project documentation
- `LICENSE` - License file
- Development docs: `CLAUDE.md`, `PLANNING.md`, `TASK.md`, etc.

## `/src` - Source Code
- `/analyzers` - Market analysis modules
- `/clients` - API clients (Polymarket, News)
- `/config` - Configuration and settings
- `/console` - CLI interface and display
- `/utils` - Utility modules

## `/tests` - Test Suite
- Unit tests for all modules
- Integration tests

## `/scripts` - Utility Scripts
- `/debug` - Debugging scripts
- `/analysis` - Market analysis scripts
- `/examples` - Demo and example scripts
- Other utility scripts

## `/data` - Data Files
- `market_patterns.json` - Pattern definitions
- `predictions.jsonl` - Prediction tracking
- `/backtests` - Backtest results
- Response files and caches

## `/docs` - Documentation
- `/guides` - How-to guides and fixes
- Analysis reports and summaries

## `/PRPs` - Project Reference Points
- `/templates` - PRP templates
- Example PRPs

## Quick Commands

```bash
# Run the analyzer
python main.py

# Analyze more markets
python main.py --markets 1000

# Research a specific market
python main.py research <url>

# Run tests
pytest tests/

# Debug scripts
python scripts/debug/<script_name>.py
```