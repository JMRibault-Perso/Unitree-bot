#!/usr/bin/env python3
"""
Analyze the JavaScript button logic to identify issues
"""

import re

def analyze_javascript():
    """Read and analyze the JavaScript code"""
    
    with open('/root/G1/unitree_sdk2/g1_app/ui/index.html', 'r') as f:
        content = f.read()
    
    print("=" * 60)
    print("🔍 ANALYZING BUTTON LOGIC IN index.html")
    print("=" * 60)
    
    # Find updateStateButtons function
    match = re.search(r'function updateStateButtons\(\).*?\n        \}', content, re.DOTALL)
    if match:
        print("\n📍 Found updateStateButtons() function:\n")
        print(match.group(0))
    else:
        print("\n❌ updateStateButtons() function NOT FOUND!")
    
    # Find where buttons are created
    print("\n" + "=" * 60)
    print("📍 Searching for button creation code...")
    print("=" * 60)
    
    button_matches = re.findall(r'<button.*?class="state-button".*?>', content, re.DOTALL)
    print(f"\nFound {len(button_matches)} state buttons in HTML")
    
    # Check for isConnected checks
    print("\n" + "=" * 60)
    print("📍 Checking for isConnected guard conditions...")
    print("=" * 60)
    
    connected_checks = re.findall(r'if.*?isConnected.*?\{', content)
    print(f"\nFound {len(connected_checks)} isConnected checks:")
    for i, check in enumerate(connected_checks[:5], 1):
        print(f"  {i}. {check.strip()}")
    
    # Check setState function
    print("\n" + "=" * 60)
    print("📍 Analyzing setState() function...")
    print("=" * 60)
    
    setstate_match = re.search(r'async function setState\(stateName\).*?\n        \}', content, re.DOTALL)
    if setstate_match:
        print("\nFound setState() function:")
        print(setstate_match.group(0)[:500] + "...")
    
    # Check for button disable logic
    print("\n" + "=" * 60)
    print("📍 Searching for button.disabled assignments...")
    print("=" * 60)
    
    disable_matches = re.findall(r'\.disabled\s*=.*?;', content)
    print(f"\nFound {len(disable_matches)} button.disabled assignments:")
    for i, match in enumerate(set(disable_matches), 1):
        print(f"  {i}. {match}")
    
    print("\n" + "=" * 60)
    print("✅ Analysis Complete")
    print("=" * 60)

if __name__ == "__main__":
    analyze_javascript()
