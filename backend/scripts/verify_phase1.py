#!/usr/bin/env python
"""
Verify Phase 1 backend structure and imports.

Checks that all modules are properly structured and importable.

Usage:
    python backend/scripts/verify_phase1.py [--verbose]
"""
import argparse
import importlib
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def verify_module(module_path: str, verbose: bool = False) -> bool:
    """
    Verify that a module can be imported.
    
    Args:
        module_path: Module import path (e.g., "backend.src.adapters")
        verbose: If True, print detailed info
    
    Returns:
        True if module imports successfully
    """
    try:
        module = importlib.import_module(module_path)
        if verbose:
            print(f"✓ {module_path}")
            if hasattr(module, "__all__"):
                exports = module.__all__
                for export in exports:
                    if hasattr(module, export):
                        obj = getattr(module, export)
                        obj_type = type(obj).__name__
                        print(f"  ├─ {export} ({obj_type})")
                    else:
                        print(f"  ├─ {export} (ERROR: not found)")
                        return False
        return True
    except Exception as e:
        print(f"✗ {module_path}: {e}")
        return False


def verify_file_structure(verbose: bool = False) -> bool:
    """
    Verify that all Phase 1 files exist.
    
    Args:
        verbose: If True, print detailed info
    
    Returns:
        True if all files exist
    """
    required_files = [
        "backend/src/__init__.py",
        "backend/src/adapters/__init__.py",
        "backend/src/adapters/google_places_adapter.py",
        "backend/src/adapters/simulated_social_adapter.py",
        "backend/src/services/__init__.py",
        "backend/src/services/geospatial_service.py",
        "backend/src/database/__init__.py",
        "backend/src/database/connection.py",
        "backend/src/database/models.py",
        "backend/src/utils/__init__.py",
        "backend/src/utils/logger.py",
        "backend/tests/__init__.py",
        "backend/tests/adapters/__init__.py",
        "backend/tests/services/__init__.py",
        "backend/scripts/fetch_google_places.py",
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = project_root / file_path
        exists = full_path.exists()
        status = "✓" if exists else "✗"
        if verbose or not exists:
            print(f"{status} {file_path}")
        if not exists:
            all_exist = False
    
    return all_exist


def verify_imports(verbose: bool = False) -> bool:
    """
    Verify that all Phase 1 modules can be imported.
    
    Args:
        verbose: If True, print detailed info
    
    Returns:
        True if all modules import successfully
    """
    modules = [
        "backend.src",
        "backend.src.adapters",
        "backend.src.services",
        "backend.src.database",
        "backend.src.utils",
        "backend.tests",
    ]
    
    all_imports_ok = True
    for module in modules:
        if not verify_module(module, verbose=verbose):
            all_imports_ok = False
    
    return all_imports_ok


def verify_contracts(verbose: bool = False) -> bool:
    """
    Verify that Phase 0 contracts are available.
    
    Args:
        verbose: If True, print detailed info
    
    Returns:
        True if contracts can be imported
    """
    contracts_modules = [
        "contracts.models",
        "contracts.base_adapter",
    ]
    
    all_ok = True
    for module in contracts_modules:
        if not verify_module(module, verbose=verbose):
            all_ok = False
    
    return all_ok


def main():
    """Main verification entry point."""
    parser = argparse.ArgumentParser(
        description="Verify Phase 1 backend structure",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print detailed verification output"
    )
    
    args = parser.parse_args()
    
    print("Phase 1 Backend Verification")
    print("=" * 50)
    
    # Check file structure
    print("\n1. File Structure:")
    files_ok = verify_file_structure(verbose=args.verbose)
    
    # Check Phase 0 contracts
    print("\n2. Phase 0 Contracts:")
    contracts_ok = verify_contracts(verbose=args.verbose)
    
    # Check imports
    print("\n3. Module Imports:")
    imports_ok = verify_imports(verbose=args.verbose)
    
    # Summary
    print("\n" + "=" * 50)
    all_ok = files_ok and contracts_ok and imports_ok
    
    if all_ok:
        print("✓ All Phase 1 checks passed!")
        return 0
    else:
        print("✗ Some Phase 1 checks failed")
        if not files_ok:
            print("  - Check file structure")
        if not contracts_ok:
            print("  - Check Phase 0 contracts")
        if not imports_ok:
            print("  - Check module imports")
        return 1


if __name__ == "__main__":
    sys.exit(main())
