#!/usr/bin/env python3
"""
Simple test for themes and patterns functionality.
Tests the core logic without requiring pygame/display.
"""

import sys
import os
from pathlib import Path

# Test theme and pattern loading
def test_config_loading():
    """Test that config loads properly."""
    try:
        import yaml
    except ImportError:
        print("⚠ YAML not available, skipping config test")
        return True
    
    config_file = Path(__file__).parent / "bambam_config.yaml"
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    # Test themes
    themes = config.get('themes', {}).get('definitions', {})
    assert len(themes) == 6, f"Expected 6 themes, got {len(themes)}"
    assert 'rainbow' in themes, "Rainbow theme not found"
    assert 'ocean' in themes, "Ocean theme not found"
    
    # Test patterns
    patterns = config.get('patterns', {})
    assert patterns.get('enabled') is True, "Patterns should be enabled"
    sequences = patterns.get('sequences', [])
    assert len(sequences) == 3, f"Expected 3 patterns, got {len(sequences)}"
    
    # Check pattern structure
    pattern_dict = {p['pattern']: p['action'] for p in sequences}
    assert 'abcd' in pattern_dict, "Pattern 'abcd' not found"
    assert pattern_dict['abcd'] == 'clear_screen', "Pattern 'abcd' has wrong action"
    
    print("✓ Config loading test passed")
    return True


def test_theme_structure():
    """Test that theme definitions have correct structure."""
    try:
        import yaml
    except ImportError:
        print("⚠ YAML not available, skipping theme structure test")
        return True
    
    config_file = Path(__file__).parent / "bambam_config.yaml"
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    themes = config.get('themes', {}).get('definitions', {})
    
    for name, theme in themes.items():
        assert 'name' in theme, f"Theme {name} missing 'name' field"
        assert 'description' in theme, f"Theme {name} missing 'description' field"
        assert 'background_color' in theme, f"Theme {name} missing 'background_color' field"
        
        # Check background_color is valid RGB
        bg = theme['background_color']
        assert isinstance(bg, list), f"Theme {name} background_color not a list"
        assert len(bg) == 3, f"Theme {name} background_color not RGB (len={len(bg)})"
        
        # If theme has color_palette, validate it
        if 'color_palette' in theme:
            palette = theme['color_palette']
            assert isinstance(palette, list), f"Theme {name} color_palette not a list"
            for i, color in enumerate(palette):
                assert len(color) == 3, f"Theme {name} palette color {i} not RGB"
    
    print("✓ Theme structure test passed")
    return True


def test_pattern_actions():
    """Test that all pattern actions are valid."""
    try:
        import yaml
    except ImportError:
        print("⚠ YAML not available, skipping pattern actions test")
        return True
    
    config_file = Path(__file__).parent / "bambam_config.yaml"
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    valid_actions = {'clear_screen', 'change_theme', 'rainbow_mode', 'random_theme'}
    patterns = config.get('patterns', {}).get('sequences', [])
    
    for pattern in patterns:
        action = pattern.get('action')
        assert action in valid_actions, f"Invalid action '{action}' in pattern '{pattern.get('pattern')}'"
    
    print("✓ Pattern actions test passed")
    return True


def main():
    """Run all tests."""
    print("Testing themes and patterns functionality...\n")
    
    tests = [
        test_config_loading,
        test_theme_structure,
        test_pattern_actions,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'='*50}")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
