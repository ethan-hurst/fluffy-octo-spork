"""
Enhanced module reloading utilities for development.
"""

import importlib
import sys
from typing import List, Set
import logging

logger = logging.getLogger(__name__)


class ModuleReloader:
    """Enhanced module reloader that handles dependencies."""
    
    @staticmethod
    def get_all_submodules(package: str) -> Set[str]:
        """Get all submodules of a package."""
        submodules = set()
        prefix = package + "."
        
        for module_name in list(sys.modules.keys()):
            if module_name == package or module_name.startswith(prefix):
                submodules.add(module_name)
                
        return submodules
    
    @staticmethod
    def reload_package(package: str) -> int:
        """
        Reload a package and all its submodules.
        
        Args:
            package: Package name to reload
            
        Returns:
            Number of modules reloaded
        """
        # Get all submodules
        modules = ModuleReloader.get_all_submodules(package)
        
        # Sort by depth (reload parent modules first)
        sorted_modules = sorted(modules, key=lambda x: x.count('.'))
        
        reloaded = 0
        for module_name in sorted_modules:
            try:
                if module_name in sys.modules:
                    importlib.reload(sys.modules[module_name])
                    reloaded += 1
                    logger.debug(f"Reloaded: {module_name}")
            except Exception as e:
                logger.warning(f"Failed to reload {module_name}: {e}")
                
        return reloaded
    
    @staticmethod
    def deep_reload(packages: List[str]) -> int:
        """
        Deep reload of multiple packages.
        
        Args:
            packages: List of package names
            
        Returns:
            Total number of modules reloaded
        """
        total_reloaded = 0
        
        for package in packages:
            reloaded = ModuleReloader.reload_package(package)
            total_reloaded += reloaded
            logger.info(f"Reloaded {reloaded} modules from {package}")
            
        return total_reloaded
    
    @staticmethod
    def clear_instance_caches():
        """Clear various caches that might hold old instances."""
        # Clear function caches
        import functools
        import gc
        
        # Clear lru_cache instances
        gc.collect()
        
        # Clear any module-level caches
        cache_modules = [
            'src.utils.cache',
            'src.utils.rate_limiter',
            'src.utils.prediction_tracker'
        ]
        
        for module_name in cache_modules:
            if module_name in sys.modules:
                module = sys.modules[module_name]
                # Look for cache clear methods
                if hasattr(module, 'clear_all'):
                    module.clear_all()
                elif hasattr(module, 'reset'):
                    module.reset()
                    
        logger.info("Cleared instance caches")