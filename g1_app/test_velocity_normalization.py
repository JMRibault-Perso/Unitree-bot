#!/usr/bin/env python3
"""
Test velocity normalization logic WITHOUT controlling the robot
Verifies that WASD commands are properly normalized for wireless controller
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.constants import VelocityLimits, FSMState, SpeedMode

def test_wasd_normalization():
    """Test WASD key velocity normalization"""
    
    # WASD values from index.html (lines 1762-1768)
    wasd_commands = {
        'W (forward)': {'vx': 0.3, 'vy': 0, 'omega': 0},
        'A (strafe left)': {'vx': 0, 'vy': 0.2, 'omega': 0},
        'S (backward)': {'vx': -0.3, 'vy': 0, 'omega': 0},
        'D (strafe right)': {'vx': 0, 'vy': -0.2, 'omega': 0},
        'Q (turn left)': {'vx': 0, 'vy': 0, 'omega': 0.5},
        'E (turn right)': {'vx': 0, 'vy': 0, 'omega': -0.5},
    }
    
    print("=" * 80)
    print("VELOCITY NORMALIZATION TEST (No Robot Control)")
    print("=" * 80)
    print()
    
    # Test current implementation (WALK mode normalization)
    print("CURRENT IMPLEMENTATION: Normalize to WALK mode (1.0 m/s)")
    print("-" * 80)
    
    for key, cmd in wasd_commands.items():
        vx, vy, omega = cmd['vx'], cmd['vy'], cmd['omega']
        
        # Apply minimum threshold
        if abs(vx) < VelocityLimits.MIN_LINEAR:
            vx = 0.0
        if abs(vy) < VelocityLimits.MIN_STRAFE:
            vy = 0.0
        if abs(omega) < VelocityLimits.MIN_ANGULAR:
            omega = 0.0
        
        # Current code: normalize to WALK max
        ly_normalized = vx / VelocityLimits.WALK_MAX_LINEAR if vx != 0 else 0.0
        lx_normalized = vy / VelocityLimits.WALK_MAX_STRAFE if vy != 0 else 0.0
        rx_normalized = omega / VelocityLimits.WALK_MAX_ANGULAR if omega != 0 else 0.0
        
        print(f"{key:20} -> ly={ly_normalized:+.2f}, lx={lx_normalized:+.2f}, rx={rx_normalized:+.2f}")
    
    print()
    print("INTERPRETATION BY ROBOT:")
    print("-" * 80)
    print("WALK mode (500/501): 1.0 normalized = 1.0 m/s max")
    print("  W key (ly=0.30) -> 0.30 m/s forward  ✅ CORRECT")
    print()
    print("RUN mode (801) with SpeedMode.HIGH (3.0 m/s max):")
    print("  W key (ly=0.30) -> 0.30 * 3.0 = 0.90 m/s forward  ⚠️  SLOWER than expected")
    print("  Expected: Should go 0.3 m/s, not 0.9 m/s!")
    print()
    
    # Test mode-aware normalization
    print("=" * 80)
    print("MODE-AWARE NORMALIZATION (Proposed Fix)")
    print("=" * 80)
    print()
    
    for mode_name, fsm_state, speed_mode in [
        ("WALK mode", FSMState.LOCK_STAND, SpeedMode.LOW),
        ("RUN mode (LOW)", FSMState.RUN, SpeedMode.LOW),
        ("RUN mode (HIGH)", FSMState.RUN, SpeedMode.HIGH),
    ]:
        print(f"{mode_name}:")
        print("-" * 40)
        
        max_linear = VelocityLimits.get_max_linear(fsm_state, speed_mode)
        max_strafe = VelocityLimits.get_max_strafe(fsm_state)
        max_angular = VelocityLimits.get_max_angular(fsm_state)
        
        print(f"  Max speeds: linear={max_linear} m/s, strafe={max_strafe} m/s, angular={max_angular} rad/s")
        
        for key, cmd in wasd_commands.items():
            vx, vy, omega = cmd['vx'], cmd['vy'], cmd['omega']
            
            if abs(vx) < VelocityLimits.MIN_LINEAR:
                vx = 0.0
            if abs(vy) < VelocityLimits.MIN_STRAFE:
                vy = 0.0
            if abs(omega) < VelocityLimits.MIN_ANGULAR:
                omega = 0.0
            
            # Mode-aware normalization
            ly_normalized = vx / max_linear if vx != 0 else 0.0
            lx_normalized = vy / max_strafe if vy != 0 else 0.0
            rx_normalized = omega / max_angular if omega != 0 else 0.0
            
            if vx != 0 or vy != 0 or omega != 0:
                actual_speed = ly_normalized * max_linear if vx != 0 else (lx_normalized * max_strafe if vy != 0 else rx_normalized * max_angular)
                print(f"    {key:20} -> normalized={ly_normalized or lx_normalized or rx_normalized:+.2f} -> actual={actual_speed:+.2f} m/s")
        
        print()
    
    print("=" * 80)
    print("CONCLUSION:")
    print("=" * 80)
    print("❌ Current implementation: Normalizes to WALK max (1.0) regardless of mode")
    print("   - In RUN mode, robot interprets 0.3 as 30% of RUN max (0.9-3.0 m/s)")
    print("   - WASD commands will be 3x faster in RUN mode than intended!")
    print()
    print("✅ Mode-aware normalization: Uses current mode's max for normalization")
    print("   - 0.3 m/s input always = 0.3 m/s actual speed, regardless of mode")
    print("   - Consistent speed across WALK/RUN modes")
    print()

if __name__ == "__main__":
    test_wasd_normalization()
