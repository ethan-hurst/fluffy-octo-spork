# Polymarket Analyzer - Project Planning

## Project Overview
A console application that analyzes Polymarket prediction markets to identify high-value betting opportunities by combining market data with current news events.

## Architecture

### Core Components
1. **Data Collection Layer**
   - Polymarket CLOB API client for market data
   - NewsAPI client for current events
   - Rate limiting and caching

2. **Analysis Engine**
   - Market analyzer for identifying mispriced markets
   - News correlator for matching events to markets
   - Probability calculator for fair odds estimation

3. **Console Interface**
   - Display high-value opportunities
   - Show market analysis with reasoning
   - Interactive commands for filtering/sorting

### Technology Stack
- Python 3.11+
- FastAPI (for future API expansion)
- Pydantic for data validation
- aiohttp for async API calls
- python-dotenv for environment management
- pytest for testing
- black for formatting
- ruff for linting

## Project Structure
```
polymarket_analyzer/
├── src/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── clients/
│   │   ├── __init__.py
│   │   ├── polymarket/
│   │   │   ├── __init__.py
│   │   │   ├── client.py
│   │   │   └── models.py
│   │   └── news/
│   │       ├── __init__.py
│   │       ├── client.py
│   │       └── models.py
│   ├── analyzers/
│   │   ├── __init__.py
│   │   ├── market_analyzer.py
│   │   ├── news_correlator.py
│   │   └── models.py
│   ├── console/
│   │   ├── __init__.py
│   │   ├── app.py
│   │   └── display.py
│   └── utils/
│       ├── __init__.py
│       ├── rate_limiter.py
│       └── cache.py
├── tests/
│   ├── __init__.py
│   ├── test_polymarket_client.py
│   ├── test_news_client.py
│   ├── test_market_analyzer.py
│   └── test_news_correlator.py
├── .env.example
├── requirements.txt
├── pyproject.toml
├── README.md
├── PLANNING.md
└── TASK.md
```

## Naming Conventions
- Classes: PascalCase (e.g., MarketAnalyzer)
- Functions/variables: snake_case (e.g., get_markets)
- Constants: UPPER_SNAKE_CASE (e.g., API_BASE_URL)
- Modules: snake_case (e.g., market_analyzer.py)

## Key Design Decisions
1. **Async First**: Use async/await for all API calls
2. **Type Safety**: Pydantic models for all data structures
3. **Modular Design**: Clear separation between data collection, analysis, and presentation
4. **Testability**: Dependency injection and mocking for unit tests
5. **Error Handling**: Graceful degradation with informative error messages

## Security Considerations
- API keys stored in environment variables
- No sensitive data logged
- Rate limiting to prevent API abuse
- Input validation on all external data