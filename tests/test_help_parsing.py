#!/usr/bin/env python3
"""
Test script to verify help dialog parsing works correctly.
"""

import sys
from pathlib import Path

# Add root dir to path
root_path = Path(__file__).parent.parent
sys.path.insert(0, str(root_path))

from src.gui.help_dialog import HelpParser

def test_parsing():
    """Test the help parsing functionality."""
    parser = HelpParser()
    
    # Test with our user guide
    guide_path = Path("src/assets/USER_GUIDE.md")
    if guide_path.exists():
        sections, title = parser.parse_file(guide_path)
        
        print(f"Document Title: {title}")
        print(f"Number of sections: {len(sections)}")
        print("\nSections:")
        
        for i, section in enumerate(sections, 1):
            print(f"{i}. {section.title}")
            content_preview = section.content[:100].replace('\n', ' ')
            if len(section.content) > 100:
                content_preview += "..."
            print(f"   Content preview: {content_preview}")
            print()
    else:
        print("USER_GUIDE.md not found")

if __name__ == "__main__":
    test_parsing()
