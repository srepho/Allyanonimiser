#!/usr/bin/env python3
"""
Setup verification script for Allyanonimiser.
Checks that all dependencies are properly installed and configured.
"""

import sys
import subprocess
from importlib import import_module

def check_module(module_name, display_name=None):
    """Check if a module is installed and return version if available."""
    if display_name is None:
        display_name = module_name
        
    try:
        module = import_module(module_name)
        version = getattr(module, '__version__', 'unknown')
        print(f"✓ {display_name}: {version}")
        return True
    except ImportError:
        print(f"✗ {display_name}: Not installed")
        return False

def check_spacy_models():
    """Check which spaCy models are installed."""
    try:
        import spacy
        print("\nChecking spaCy models:")
        
        models = {
            'en_core_web_lg': 'Large model (788 MB) - Recommended',
            'en_core_web_md': 'Medium model (479 MB)',
            'en_core_web_sm': 'Small model (44 MB)',
            'en_core_web_trf': 'Transformer model (438 MB) - Most accurate'
        }
        
        installed_models = []
        for model_name, description in models.items():
            try:
                spacy.load(model_name)
                print(f"  ✓ {model_name}: {description}")
                installed_models.append(model_name)
            except OSError:
                pass
                
        if not installed_models:
            print("  ⚠️  No spaCy models installed!")
            print("  To install the recommended model:")
            print("    python -m spacy download en_core_web_lg")
            return False
        return True
    except ImportError:
        print("\n✗ spaCy not installed - Named Entity Recognition will be unavailable")
        return False

def check_allyanonimiser():
    """Check Allyanonimiser installation and configuration."""
    print("\nChecking Allyanonimiser:")
    try:
        from allyanonimiser import create_allyanonimiser, __version__
        print(f"✓ Allyanonimiser version: {__version__}")
        
        # Create instance and check spaCy status
        print("\nInitializing Allyanonimiser...")
        ally = create_allyanonimiser()
        
        print("\nChecking spaCy integration:")
        status = ally.check_spacy_status()
        
        if status['is_loaded']:
            print(f"✓ spaCy integration active")
            print(f"  Model: {status['model_name']}")
            if status['has_ner']:
                print(f"  Named Entity Recognition: Available")
                print(f"  Supported entities: {', '.join(status['entity_types'][:3])}...")
            else:
                print("  ⚠️  Limited functionality - using basic model")
        else:
            print("⚠️  spaCy integration inactive")
            print("  Pattern-based detection will still work for:")
            print("    - Email addresses, phone numbers")
            print("    - Australian IDs (TFN, ABN, Medicare, etc.)")
            print("    - Insurance-specific patterns")
            
        return True
    except ImportError as e:
        print(f"✗ Allyanonimiser not properly installed: {e}")
        return False
    except Exception as e:
        print(f"✗ Error initializing Allyanonimiser: {e}")
        return False

def check_optional_dependencies():
    """Check optional dependencies."""
    print("\nOptional dependencies:")
    
    # PyArrow for accelerated DataFrame processing
    has_pyarrow = check_module('pyarrow', 'PyArrow (DataFrame acceleration)')
    if not has_pyarrow:
        print("  Install with: pip install pyarrow")
    
    # pandas for DataFrame support
    has_pandas = check_module('pandas', 'pandas (DataFrame support)')
    if not has_pandas:
        print("  Install with: pip install pandas")
        
    return has_pyarrow, has_pandas

def main():
    """Run all verification checks."""
    print("Allyanonimiser Setup Verification")
    print("=" * 40)
    
    print("\nCore dependencies:")
    all_good = True
    
    # Check core dependencies
    all_good &= check_module('presidio_analyzer', 'Presidio Analyzer')
    all_good &= check_module('presidio_anonymizer', 'Presidio Anonymizer')
    all_good &= check_module('spacy', 'spaCy')
    
    # Check spaCy models
    has_models = check_spacy_models()
    
    # Check optional dependencies
    check_optional_dependencies()
    
    # Check Allyanonimiser
    ally_ok = check_allyanonimiser()
    
    print("\n" + "=" * 40)
    if all_good and ally_ok:
        if has_models:
            print("✓ All core components are properly installed!")
        else:
            print("✓ Core components installed, but spaCy models missing")
            print("  Install with: python -m spacy download en_core_web_lg")
    else:
        print("✗ Some components are missing or misconfigured")
        print("  Please install missing dependencies")
        sys.exit(1)

if __name__ == "__main__":
    main()