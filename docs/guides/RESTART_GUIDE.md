# Restart Function Guide

## Overview
The `restart` command in the Polymarket Analyzer reloads all modules to pick up code changes without exiting the application.

## What the Restart Function Does

### 1. **Module Reloading**
- Uses the enhanced `ModuleReloader` for deep package reloading
- Reloads all modules in these packages:
  - `src.analyzers` (including market_researcher, flexible_analyzer, etc.)
  - `src.clients` (API clients)
  - `src.config` (settings)
  - `src.console` (display, chat)
  - `src.utils` (utilities)

### 2. **Cache Clearing**
- Clears API response cache
- Clears rate limiter states
- Resets any module-level caches

### 3. **Component Reinitialization**
- Creates new instances of:
  - `MarketAnalyzer`
  - `NewsCorrelator`
  - `MarketResearcher`
  - `DisplayManager`
- Reloads configuration settings

### 4. **State Reset**
- Clears last analysis results
- Maintains current filters (can be cleared separately)
- Resets the display

## How to Use

```bash
# In the interactive console
> restart
```

## What Gets Reloaded

### ✅ Successfully Reloaded:
- Python code changes in `.py` files
- Configuration changes in settings
- New methods added to existing classes
- Modified analyzer logic
- Updated patterns and thresholds
- New imports

### ⚠️ May Require Full Restart:
- Changes to class structure
- New dependencies/packages
- Environment variable changes
- Major architectural changes

## Testing Restart

### Example Test:
1. Edit `src/analyzers/flexible_analyzer.py`:
   ```python
   # Change from:
   self.min_edge = 0.05
   # To:
   self.min_edge = 0.10
   ```

2. Save the file

3. In the console, run:
   ```
   > restart
   ```

4. Run analysis:
   ```
   > start
   ```

5. You should see fewer opportunities due to the higher edge requirement

## Troubleshooting

### If Changes Don't Appear:

1. **Make sure files are saved** - Unsaved changes won't be reloaded

2. **Try restart twice** - Sometimes module dependencies need double reload

3. **Check for import errors** - Look for error messages during restart

4. **For major changes** - Exit (`quit`) and restart the application

### Common Issues:

- **Singleton objects**: Some objects might maintain old state
- **Circular imports**: Can cause reload failures
- **Cached imports**: Python's import cache can be persistent

## Enhanced Features

The restart function now includes:

1. **Deep Reload**: Reloads entire packages, not just specific modules
2. **Dependency Ordering**: Reloads parent modules before children
3. **Cache Clearing**: Explicitly clears known caches
4. **Error Recovery**: Falls back to basic reload if enhanced reload fails

## Development Workflow

For active development:

1. Make your code changes
2. Save all files
3. Run `restart` in the console
4. Test your changes
5. Repeat as needed

For major refactoring:
- Exit and restart the application for a clean state

## Technical Details

The restart function uses:
- `importlib.reload()` for module reloading
- Custom `ModuleReloader` class for deep package reloading
- Explicit reinitialization of all major components
- Cache clearing for stateful objects

This ensures that most code changes are picked up without needing to exit the application.