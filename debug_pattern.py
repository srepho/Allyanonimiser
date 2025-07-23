#!/usr/bin/env python3
"""Debug NAME_CONSULTANT patterns."""

import re

# Test patterns
patterns = [
    r"(?:Assigned\s+To|Assigned)\s*:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})(?=\s+(?:Subject|Re|Regarding|For|About|Issue|Matter|Case|Claim|Policy|Date|Time|Status|Type|Category|$))",
    r"(?:Assigned\s+To|Assigned)\s*:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})$",
]

test_text = "Diary Assigned To : Bruno Aloi Subject : Await Credit Op to place funds"

print(f"Testing text: {test_text}")
print("=" * 70)

for i, pattern in enumerate(patterns):
    print(f"\nPattern {i+1}:")
    print(f"  {pattern[:80]}...")
    
    matches = list(re.finditer(pattern, test_text))
    if matches:
        for match in matches:
            print(f"  Match: '{match.group()}'")
            if match.groups():
                print(f"    Captured: '{match.group(1)}'")
    else:
        print("  No match")

# Try simpler pattern
print("\n" + "=" * 70)
print("Testing simpler pattern:")

simple_pattern = r"Assigned\s+To\s*:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)"
print(f"Pattern: {simple_pattern}")

matches = list(re.finditer(simple_pattern, test_text))
if matches:
    for match in matches:
        print(f"Match: '{match.group()}'")
        print(f"Captured: '{match.group(1)}'")
else:
    print("No match")