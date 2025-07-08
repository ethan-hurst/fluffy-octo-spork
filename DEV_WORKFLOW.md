# Development Workflow with Graceful Restart

## 🔄 No More App Restarts!

Instead of exiting and restarting the entire application every time you make code changes, you can now use these commands:

## Commands Available

### **`restart`** - Full Application Restart
```bash
> restart
```
**What it does:**
- ✅ Reloads ALL modules (picks up code changes)
- ✅ Clears API cache (fresh data)
- ✅ Resets application state 
- ✅ Clears screen and shows fresh banner
- ✅ Resets all filters to default

**Use when:** You've made significant changes and want a completely fresh start.

### **`reload`** - Module Reload Only  
```bash
> reload
```
**What it does:**
- ✅ Reloads ALL modules (picks up code changes)
- ✅ Reinitializes analyzers and components
- ❌ Keeps cache (faster)
- ❌ Keeps current analysis results
- ❌ Keeps current filters

**Use when:** You've made code changes but want to keep your current session state.

### **`watch`** - Auto-Reload on File Changes (Development Mode)
```bash
> watch                    # Enable auto-reload
> watch                    # Disable auto-reload
```
**What it does:**
- 🔍 Monitors all `.py` files in `src/` directory
- 🔄 Automatically runs `reload` when files change
- ⚠️ Development feature only - disable for production

**Use when:** You're actively developing and want instant code updates.

## 🚀 Example Development Workflow

### **Scenario 1: Fixing Expected Return Bug**
```bash
# Start app
> python main.py

# Run analysis, see negative returns
> start
> predictions 1           # See -49% returns

# Fix code in market_analyzer.py (outside app)
# Then reload the changes:
> reload                  # Picks up your fixes instantly!

# Test the fix
> start                   # Run analysis with updated code
> predictions 1           # See positive returns now!
```

### **Scenario 2: Adding New Features**
```bash
# Enable auto-reload during development
> watch
Info: Auto-reload enabled
Warning: This is a development feature - disable for production

# Now edit any .py file and changes are automatically loaded!
# Edit src/analyzers/market_analyzer.py
# (App automatically reloads modules when you save)

# Test your changes immediately
> start                   # Uses updated code automatically
```

### **Scenario 3: Testing Filter Changes**
```bash
# Make changes to market_filters.py
# Reload to pick up changes
> reload

# Test new filter logic
> filter keywords bitcoin
> start
```

## ⚡ Benefits

### **Before (Manual Restart Required):**
```bash
# Make code change
# Ctrl+C to exit app
$ python main.py          # Restart entire app
> start                   # Re-run analysis
```

### **After (Graceful Restart):**
```bash
# Make code change
> reload                  # Instant module reload!
> start                   # Test with updated code
```

## 🛠️ Technical Details

**What gets reloaded:**
- `src.analyzers.*` - Market analysis logic
- `src.clients.*` - API clients  
- `src.config.*` - Settings and configuration
- `src.console.*` - Display and chat interface
- `src.utils.*` - Utilities and filters

**What persists:**
- Your terminal session
- Environment variables
- API keys
- Prediction tracking data
- Log files

This dramatically speeds up development and testing cycles!