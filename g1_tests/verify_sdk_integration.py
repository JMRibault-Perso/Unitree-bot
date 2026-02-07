#!/usr/bin/env python3
"""
Verification script to check SDK integration and teach mode readiness
Usage: python3 verify_sdk_integration.py
"""

import os
import json
from pathlib import Path

class SDKVerifier:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
        self.checks = []
        
    def verify(self):
        """Run all verification checks"""
        print("=" * 70)
        print("SDK Integration Verification")
        print("=" * 70)
        
        self.check_python_sdk()
        self.check_android_app()
        self.check_documentation()
        self.check_web_controller()
        self.check_teach_mode_readiness()
        
        self.print_summary()
        
    def check_python_sdk(self):
        """Check Python SDK structure"""
        print("\n📦 Python SDK Check...")
        
        sdk_path = self.project_root / "examples" / "sdk2_python"
        checks = {
            "SDK Directory": sdk_path.exists(),
            "unitree_sdk2py module": (sdk_path / "unitree_sdk2py").exists(),
            "G1 Loco Client": (sdk_path / "unitree_sdk2py/g1/loco/g1_loco_client.py").exists(),
            "G1 Arm Action Client": (sdk_path / "unitree_sdk2py/g1/arm/g1_arm_action_client.py").exists(),
            "G1 Audio Client": (sdk_path / "unitree_sdk2py/g1/audio/g1_audio_client.py").exists(),
            "Examples directory": (sdk_path / "example").exists(),
            "SDK README": (sdk_path / "README.md").exists(),
        }
        
        for check, result in checks.items():
            self.print_check(check, result)
            self.checks.append((f"Python SDK: {check}", result))
    
    def check_android_app(self):
        """Check Android app decompilation"""
        print("\n📱 Android App Check...")
        
        app_path = self.project_root / "android_app_decompiled"
        checks = {
            "Decompiled directory": app_path.exists(),
            "Unitree_Explore source": (app_path / "Unitree_Explore").exists(),
            "Apktool available": (app_path / "apktool.jar").exists(),
            "README present": (app_path / "README.md").exists(),
        }
        
        for check, result in checks.items():
            self.print_check(check, result)
            self.checks.append((f"Android App: {check}", result))
    
    def check_documentation(self):
        """Check documentation files"""
        print("\n📚 Documentation Check...")
        
        docs = {
            "TEACH_MODE_REFERENCE.md": self.project_root / "TEACH_MODE_REFERENCE.md",
            "AP_MODE_IMPLEMENTATION.md": self.project_root / "AP_MODE_IMPLEMENTATION.md",
            "SDK_INTEGRATION_SUMMARY.md": self.project_root / "SDK_INTEGRATION_SUMMARY.md",
            "unitree_docs/arm-control-routine.md": self.project_root / "unitree_docs/arm-control-routine.md",
        }
        
        for name, path in docs.items():
            result = path.exists()
            self.print_check(name, result)
            self.checks.append((f"Docs: {name}", result))
    
    def check_web_controller(self):
        """Check web controller components"""
        print("\n🌐 Web Controller Check...")
        
        checks = {
            "robot_controller.py": (self.project_root / "g1_app/core/robot_controller.py").exists(),
            "web_server.py": (self.project_root / "g1_app/ui/web_server.py").exists(),
            "index.html": (self.project_root / "g1_app/ui/index.html").exists(),
        }
        
        for check, result in checks.items():
            self.print_check(check, result)
            self.checks.append((f"Web Controller: {check}", result))
        
        # Check for teach mode endpoints in web_server.py
        if checks["web_server.py"]:
            with open(self.project_root / "g1_app/ui/web_server.py", encoding='utf-8') as f:
                content = f.read()
                has_teach_endpoints = "teach" in content.lower()
                self.print_check("Teach mode endpoints", has_teach_endpoints)
                self.checks.append(("Web Controller: Teach endpoints", has_teach_endpoints))
    
    def check_teach_mode_readiness(self):
        """Check teach mode implementation readiness"""
        print("\n🎓 Teach Mode Readiness Check...")
        
        sdk_path = self.project_root / "examples" / "sdk2_python"
        
        # Check for API IDs in Python SDK
        if (sdk_path / "unitree_sdk2py/g1/arm/g1_arm_action_api.py").exists():
            with open(sdk_path / "unitree_sdk2py/g1/arm/g1_arm_action_api.py", encoding='utf-8') as f:
                content = f.read()
                has_7108 = "7108" in content
                has_7113 = "7113" in content
                
                self.print_check("API ID 7108 (ExecuteCustom)", has_7108)
                self.print_check("API ID 7113 (StopCustom)", has_7113)
                self.checks.append(("Teach Mode: API 7108", has_7108))
                self.checks.append(("Teach Mode: API 7113", has_7113))
        
        # Check for methods in Python SDK
        if (sdk_path / "unitree_sdk2py/g1/arm/g1_arm_action_client.py").exists():
            with open(sdk_path / "unitree_sdk2py/g1/arm/g1_arm_action_client.py", encoding='utf-8') as f:
                content = f.read()
                has_execute_custom = "ExecuteCustomAction" in content
                has_stop_custom = "StopCustomAction" in content
                
                self.print_check("Method ExecuteCustomAction", has_execute_custom)
                self.print_check("Method StopCustomAction", has_stop_custom)
                self.checks.append(("Teach Mode: ExecuteCustomAction", has_execute_custom))
                self.checks.append(("Teach Mode: StopCustomAction", has_stop_custom))
        
        # Check for teach reference guide
        teach_guide_exists = (self.project_root / "TEACH_MODE_REFERENCE.md").exists()
        self.print_check("Teach Mode Reference Guide", teach_guide_exists)
        self.checks.append(("Teach Mode: Reference Guide", teach_guide_exists))
    
    def print_check(self, name, result):
        """Print a check result"""
        status = "✅" if result else "❌"
        print(f"  {status} {name}")
    
    def print_summary(self):
        """Print verification summary"""
        print("\n" + "=" * 70)
        print("Summary")
        print("=" * 70)
        
        passed = sum(1 for _, result in self.checks if result)
        total = len(self.checks)
        
        print(f"\nPassed: {passed}/{total}")
        
        if passed == total:
            print("\n✅ All checks passed! SDK is fully integrated.")
        else:
            print(f"\n⚠️  {total - passed} checks failed. See details above.")
        
        print("\nNext Steps:")
        print("1. Review TEACH_MODE_REFERENCE.md for implementation guide")
        print("2. Enhance Python SDK with missing teach mode methods")
        print("3. Test web controller teach mode with physical robot")
        print("4. Analyze Android app protocol (see android_app_decompiled/README.md)")
        
        print("\nKey Resources:")
        print(f"  📖 Documentation: {self.project_root}/SDK_INTEGRATION_SUMMARY.md")
        print(f"  🎓 Teach Mode: {self.project_root}/TEACH_MODE_REFERENCE.md")
        print(f"  📱 Android App: {self.project_root}/android_app_decompiled/README.md")
        print(f"  🐍 Python SDK: {self.project_root}/examples/sdk2_python/README.md")

if __name__ == "__main__":
    verifier = SDKVerifier()
    verifier.verify()
