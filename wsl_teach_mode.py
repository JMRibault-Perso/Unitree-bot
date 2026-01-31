#!/usr/bin/env python3
"""WSL teach-mode helper (LocalSTA): start/stop/save recording.

SAFETY: Only uses teach-mode recording APIs 7109-7112 (no FSM changes).
"""

import argparse
import asyncio
import sys

# Ensure repo root is on path
from pathlib import Path
repo_root = Path(__file__).resolve().parent
sys.path.insert(0, str(repo_root))

from g1_app.core.robot_controller import RobotController


async def run(ip: str, serial: str, action_name: str, delete_action: str | None, list_only: bool):
    robot = RobotController(ip, serial)
    await robot.connect()

    if list_only:
        result = await robot.get_custom_action_list()
        print(result)
        await robot.disconnect()
        return

    if delete_action:
        result = await robot.send_api_command(7112, {"action_name": delete_action})
        print(result)
        await robot.disconnect()
        return

    print("Starting teach-mode recording (API 7109)...")
    print(await robot.send_api_command(7109, {}))

    input("Move the arms, then press Enter to stop recording...")

    print("Stopping recording (API 7110)...")
    print(await robot.send_api_command(7110, {}))

    print(f"Saving action '{action_name}' (API 7111)...")
    print(await robot.send_api_command(7111, {"action_name": action_name}))

    print("Done.")
    await robot.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WSL teach-mode recorder")
    parser.add_argument("--ip", default="192.168.86.3")
    parser.add_argument("--serial", default="E21D1000PAHBMB06")
    parser.add_argument("--name", default="teach_action")
    parser.add_argument("--delete", default=None, help="Delete action by name (API 7112)")
    parser.add_argument("--list", action="store_true", help="List actions only (API 7107)")
    args = parser.parse_args()

    asyncio.run(run(args.ip, args.serial, args.name, args.delete, args.list))
