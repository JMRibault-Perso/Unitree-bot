# ⚠️ DEPRECATION NOTICE

**Date**: February 5, 2026

The following documentation files contain **OUTDATED** robot discovery information:

- ❌ `ENHANCED_DISCOVERY_SUMMARY.md` - Old multi-method cascade approach
- ❌ `ENHANCED_DISCOVERY_QUICK_REF.md` - Old API reference
- ❌ `ROBOT_DISCOVERY_UPDATE.md` - Intermediate update docs
- ❌ `DISCOVERY_BEFORE_AFTER.md` - Comparison of old methods
- ❌ `DISCOVERY_HYBRID_FIX.md` - Old ARP parsing fixes

## Current Documentation

**✅ USE THIS**: [ROBOT_DISCOVERY_README.md](ROBOT_DISCOVERY_README.md)

This is the **SINGLE SOURCE OF TRUTH** for robot discovery.

## What Changed?

**Before** (Complex, Multiple Methods):
- Multicast → AP check → ARP cache → Broadcast → nmap
- Different scripts used different subsets
- Stale ARP cache issues
- Slow offline detection (5-10 seconds)

**After** (Simple, Unified):
- Multicast → ARP with ping verification
- All scripts use same `discover_robot()` function
- Ping verification prevents stale cache
- Fast detection (2-second scans)

## Migration

Replace all old discovery code with:

```python
from g1_app.utils.robot_discovery import discover_robot

robot = discover_robot()
if robot and robot['online']:
    use robot['ip']
```

## Files Safe to Delete

These files are kept only for historical reference and can be deleted:
- `ENHANCED_DISCOVERY_*.md`
- `ROBOT_DISCOVERY_UPDATE.md`
- `DISCOVERY_*.md`
- `test_enhanced_discovery.py` (old test suite)

The new system is tested via `test_discovery_monitor.py` and proven in production via the web server.
