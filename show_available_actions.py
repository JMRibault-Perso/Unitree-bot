#!/usr/bin/env python3
"""
Show available actions - both from local storage and pre-programmed gestures
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Pre-programmed gestures from SDK
PRESET_GESTURES = {
    99: "release arm",
    11: "two-hand kiss",
    12: "left kiss / right kiss",
    15: "hands up",
    17: "clap",
    18: "high five",
    19: "hug",
    20: "heart",
    21: "right heart",
    22: "reject",
    23: "right hand up",
    24: "x-ray",
    25: "face wave",
    26: "high wave",
    27: "shake hand"
}

def main():
    print("="*70)
    print("📋 AVAILABLE ACTIONS ON G1 AIR")
    print("="*70)
    
    # 1. Pre-programmed gestures (always available)
    print("\n🎯 PRE-PROGRAMMED GESTURES (API 7106):")
    print("─"*70)
    for id, name in sorted(PRESET_GESTURES.items()):
        print(f"  {id:3d}: {name}")
    
    # 2. Custom teach mode actions (saved locally)
    print("\n💾 CUSTOM TEACH MODE ACTIONS (API 7108):")
    print("─"*70)
    
    try:
        from g1_app.ui.web_server import load_custom_actions
        custom_actions = load_custom_actions()
        
        if custom_actions:
            for i, action in enumerate(custom_actions, 1):
                print(f"  {i:3d}: {action}")
        else:
            print("  (none saved)")
            print("\n  💡 To record custom actions:")
            print("     1. Enter teaching mode (robot becomes compliant)")
            print("     2. Move arms to desired position")
            print("     3. Save with a name")
            print("     4. Play back with API 7108")
    except Exception as e:
        print(f"  ❌ Error loading custom actions: {e}")
    
    print("\n" + "="*70)
    print("📖 USAGE:")
    print("="*70)
    print("  • Execute pre-programmed gesture:")
    print("    await robot.executor.execute_gesture(ArmGesture.HIGH_FIVE)")
    print()
    print("  • Execute custom teach action:")
    print("    await robot.executor.execute_custom_action('my_action_name')")
    print()
    print("  • Stop current action:")
    print("    await robot.executor.stop_custom_action()")
    print("="*70)

if __name__ == "__main__":
    main()
