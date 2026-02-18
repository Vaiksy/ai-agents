#!/usr/bin/env python3
"""
Research Engine Checker and Fixer

This script checks if research_engine.py has any llama3/phi3 references
and offers to fix them automatically.

Since research_engine.py wasn't uploaded, this helps verify it's correct.
"""

import os
import sys
import re


def check_file(filepath):
    """Check if file has problematic model references."""
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        print(f"\nExpected location:")
        print(f"  C:\\Users\\vaiks\\Desktop\\content_intelligence_engine\\core\\research_engine.py")
        return None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    issues = []
    
    # Check for model references
    patterns = [
        (r'["\']llama3["\']', 'llama3 model reference'),
        (r'["\']phi3:mini["\']', 'phi3:mini model reference'),
        (r'["\']phi3["\']', 'phi3 model reference'),
        (r'["\']nomic-embed-text["\']', 'nomic-embed-text reference'),
        (r'MODEL_\w+\s*=\s*["\']llama', 'MODEL variable with llama'),
        (r'MODEL_\w+\s*=\s*["\']phi', 'MODEL variable with phi'),
        (r'model\s*=\s*["\']llama', 'model parameter with llama'),
        (r'model\s*=\s*["\']phi', 'model parameter with phi'),
    ]
    
    for pattern, description in patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            # Find line number
            line_num = content[:match.start()].count('\n') + 1
            line_start = content.rfind('\n', 0, match.start()) + 1
            line_end = content.find('\n', match.start())
            if line_end == -1:
                line_end = len(content)
            line_content = content[line_start:line_end].strip()
            
            issues.append({
                'line': line_num,
                'description': description,
                'content': line_content,
                'match': match.group()
            })
    
    return issues


def fix_file(filepath, backup=True):
    """Fix model references in the file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if backup:
        backup_path = filepath + '.backup'
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Backup saved to: {backup_path}")
    
    # Apply fixes
    replacements = [
        (r'"llama3"', '"qwen2.5-coder:7b"'),
        (r"'llama3'", "'qwen2.5-coder:7b'"),
        (r'"phi3:mini"', '"qwen2.5-coder:7b"'),
        (r"'phi3:mini'", "'qwen2.5-coder:7b'"),
        (r'"phi3"', '"qwen2.5-coder:7b"'),
        (r"'phi3'", "'qwen2.5-coder:7b'"),
    ]
    
    fixed_content = content
    changes = 0
    
    for old, new in replacements:
        count = len(re.findall(old, fixed_content))
        if count > 0:
            fixed_content = re.sub(old, new, fixed_content)
            changes += count
            print(f"  ✓ Replaced {count}x: {old} → {new}")
    
    if changes > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        print(f"\n✓ Fixed {changes} references in {filepath}")
        return True
    else:
        print(f"\n✓ No fixes needed in {filepath}")
        return False


def main():
    print("="*70)
    print("RESEARCH ENGINE CHECKER v5.1")
    print("="*70)
    print("\nThis script checks research_engine.py for problematic model references")
    print("and can fix them automatically.\n")
    
    # Try to find the file
    possible_paths = [
        "core/research_engine.py",
        "../core/research_engine.py",
        "C:/Users/vaiks/Desktop/content_intelligence_engine/core/research_engine.py",
    ]
    
    filepath = None
    for path in possible_paths:
        if os.path.exists(path):
            filepath = path
            break
    
    if not filepath:
        print("📁 Enter the path to research_engine.py:")
        print("   (or press Enter to skip)")
        user_path = input("> ").strip()
        if user_path:
            filepath = user_path
    
    if not filepath or not os.path.exists(filepath):
        print("\n⚠ Could not find research_engine.py")
        print("\nIf you're sure the file exists, you can:")
        print("1. Manually search for 'llama3' or 'phi3' in the file")
        print("2. Replace all occurrences with 'qwen2.5-coder:7b'")
        print("3. Make sure no embedding model references exist")
        return 1
    
    print(f"\n✓ Found file: {filepath}\n")
    print("Checking for issues...")
    
    issues = check_file(filepath)
    
    if issues is None:
        return 1
    
    if not issues:
        print("\n🎉 No issues found!")
        print("✓ research_engine.py looks good")
        return 0
    
    print(f"\n⚠ Found {len(issues)} issue(s):\n")
    
    for i, issue in enumerate(issues, 1):
        print(f"{i}. Line {issue['line']}: {issue['description']}")
        print(f"   {issue['content'][:80]}")
        print()
    
    print("Would you like to automatically fix these issues? (y/n)")
    response = input("> ").strip().lower()
    
    if response == 'y':
        print("\nApplying fixes...")
        fixed = fix_file(filepath, backup=True)
        if fixed:
            print("\n🎉 All issues fixed!")
            print("\nNext steps:")
            print("1. Restart your API server")
            print("2. Run test_agent.py to verify")
        return 0
    else:
        print("\nNo changes made. Manual fixes needed:")
        print("1. Open research_engine.py")
        print("2. Replace 'llama3' with 'qwen2.5-coder:7b'")
        print("3. Replace 'phi3:mini' with 'qwen2.5-coder:7b'")
        print("4. Replace 'phi3' with 'qwen2.5-coder:7b'")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
