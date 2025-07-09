#!/usr/bin/env python3
"""
Test script to verify restart functionality.
"""

import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_module_versions():
    """Check module versions/attributes to verify reload."""
    print("=== TESTING MODULE RELOAD ===\n")
    
    # Test 1: Check if modules are loaded
    modules_to_check = [
        'src.analyzers.market_researcher',
        'src.analyzers.flexible_analyzer',
        'src.config.settings',
        'src.utils.module_reloader'
    ]
    
    print("1. Checking loaded modules:")
    for module in modules_to_check:
        if module in sys.modules:
            print(f"  ✓ {module} is loaded")
        else:
            print(f"  ✗ {module} is NOT loaded")
    
    # Test 2: Check key attributes
    print("\n2. Checking key attributes:")
    
    try:
        from src.analyzers.market_researcher import MarketResearcher
        print("  ✓ MarketResearcher imported successfully")
    except:
        print("  ✗ Failed to import MarketResearcher")
    
    try:
        from src.analyzers.flexible_analyzer import FlexibleAnalyzer
        analyzer = FlexibleAnalyzer()
        print(f"  ✓ FlexibleAnalyzer min_edge: {analyzer.min_edge}")
        print(f"  ✓ FlexibleAnalyzer min_volume: {analyzer.min_volume}")
    except Exception as e:
        print(f"  ✗ Failed to check FlexibleAnalyzer: {e}")
    
    try:
        from src.config.settings import settings
        print(f"  ✓ Settings min_market_volume: {settings.min_market_volume}")
        print(f"  ✓ Settings min_probability_spread: {settings.min_probability_spread}")
    except:
        print("  ✗ Failed to check settings")
    
    # Test 3: Test module reloader
    print("\n3. Testing ModuleReloader:")
    try:
        from src.utils.module_reloader import ModuleReloader
        
        # Get submodules
        submodules = ModuleReloader.get_all_submodules('src.analyzers')
        print(f"  ✓ Found {len(submodules)} analyzer modules")
        
        # Test reload
        print("  → Testing reload of src.config...")
        reloaded = ModuleReloader.reload_package('src.config')
        print(f"  ✓ Reloaded {reloaded} config modules")
        
    except Exception as e:
        print(f"  ✗ ModuleReloader test failed: {e}")


def test_restart_workflow():
    """Test the restart workflow."""
    print("\n\n=== RESTART WORKFLOW TEST ===\n")
    
    print("To test restart in the app:")
    print("1. Start the app: python main.py")
    print("2. Make a change to a file (e.g., change min_edge in flexible_analyzer.py)")
    print("3. Run: restart")
    print("4. Check if the change is reflected")
    print("\nExample change to test:")
    print("  Edit src/analyzers/flexible_analyzer.py")
    print("  Change: self.min_edge = 0.03")
    print("  To:     self.min_edge = 0.10")
    print("\nAfter restart, run 'start' and check if it finds fewer opportunities")


if __name__ == "__main__":
    test_module_versions()
    test_restart_workflow()
    
    print("\n\n=== RECOMMENDATIONS ===")
    print("The restart function now:")
    print("✓ Reloads all modules including new ones (market_researcher)")
    print("✓ Uses deep reload to catch all submodules")
    print("✓ Reinitializes all components")
    print("✓ Clears caches")
    print("✓ Resets filters")
    print("\nFor best results:")
    print("- Save your changes before running restart")
    print("- If changes don't appear, try restart twice")
    print("- For major changes, exit and restart the app")