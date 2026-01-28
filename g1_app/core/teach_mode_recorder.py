"""
Teach Mode Recording System

Records arm joint positions while in teach mode (FSM 501 + arms released),
stores them as custom action trajectories, and enables playback.
"""

import json
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


# Arm joint indices from g1_dual_arm_example.cpp
ARM_JOINT_INDICES = {
    # Left arm (7 DOF)
    "left_shoulder_pitch": 15,
    "left_shoulder_roll": 16,
    "left_shoulder_yaw": 17,
    "left_elbow": 18,
    "left_wrist_roll": 19,
    "left_wrist_pitch": 20,
    "left_wrist_yaw": 21,
    # Right arm (7 DOF)
    "right_shoulder_pitch": 22,
    "right_shoulder_roll": 23,
    "right_shoulder_yaw": 24,
    "right_elbow": 25,
    "right_wrist_roll": 26,
    "right_wrist_pitch": 27,
    "right_wrist_yaw": 28
}


@dataclass
class JointSnapshot:
    """Single snapshot of arm joint positions"""
    timestamp: float  # Time since recording started (seconds)
    positions: Dict[str, float]  # Joint name → position (radians)


@dataclass
class CustomActionRecording:
    """Complete custom action recording"""
    name: str
    created_at: float  # Unix timestamp
    duration: float  # Total duration in seconds
    sample_rate: float  # Samples per second
    snapshots: List[JointSnapshot]
    
    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict"""
        return {
            "name": self.name,
            "created_at": self.created_at,
            "duration": self.duration,
            "sample_rate": self.sample_rate,
            "snapshots": [
                {
                    "timestamp": s.timestamp,
                    "positions": s.positions
                }
                for s in self.snapshots
            ]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CustomActionRecording':
        """Load from dict"""
        return cls(
            name=data["name"],
            created_at=data["created_at"],
            duration=data["duration"],
            sample_rate=data["sample_rate"],
            snapshots=[
                JointSnapshot(
                    timestamp=s["timestamp"],
                    positions=s["positions"]
                )
                for s in data["snapshots"]
            ]
        )


class TeachModeRecorder:
    """
    Records and manages custom action recordings from teach mode.
    
    Recordings are stored as JSON files in g1_app/data/custom_actions/
    """
    
    def __init__(self, storage_dir: Optional[Path] = None):
        if storage_dir is None:
            storage_dir = Path(__file__).parent.parent / "data" / "custom_actions"
        
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Recording state
        self.is_recording = False
        self.current_recording: Optional[CustomActionRecording] = None
        self.record_start_time: float = 0
        self.snapshots: List[JointSnapshot] = []
        self.sample_rate = 50.0  # Hz (matches sportmodestate frequency)
        
    def start_recording(self, action_name: str) -> bool:
        """
        Start recording a new custom action
        
        Args:
            action_name: Name for the custom action
            
        Returns:
            True if recording started successfully
        """
        if self.is_recording:
            logger.warning("Already recording, stop current recording first")
            return False
        
        if not action_name or not action_name.strip():
            logger.error("Action name cannot be empty")
            return False
        
        # Check if name already exists
        if (self.storage_dir / f"{action_name}.json").exists():
            logger.warning(f"Action '{action_name}' already exists")
            return False
        
        self.is_recording = True
        self.record_start_time = time.time()
        self.snapshots = []
        logger.info(f"Started recording custom action: {action_name}")
        return True
    
    def record_snapshot(self, motor_positions: List[float]) -> bool:
        """
        Record a snapshot of current arm joint positions
        
        Args:
            motor_positions: Array of all 29 motor positions from LowState
            
        Returns:
            True if snapshot recorded successfully
        """
        if not self.is_recording:
            return False
        
        if len(motor_positions) < 29:
            logger.error(f"Invalid motor positions array length: {len(motor_positions)}")
            return False
        
        # Extract arm joint positions
        positions = {}
        for joint_name, index in ARM_JOINT_INDICES.items():
            positions[joint_name] = motor_positions[index]
        
        # Calculate timestamp
        timestamp = time.time() - self.record_start_time
        
        snapshot = JointSnapshot(timestamp=timestamp, positions=positions)
        self.snapshots.append(snapshot)
        
        return True
    
    def stop_recording(self, action_name: str) -> Optional[CustomActionRecording]:
        """
        Stop recording and save the custom action
        
        Args:
            action_name: Name to save the action under
            
        Returns:
            The saved CustomActionRecording, or None if failed
        """
        if not self.is_recording:
            logger.warning("Not currently recording")
            return None
        
        if len(self.snapshots) < 2:
            logger.error("Recording too short (need at least 2 snapshots)")
            self.is_recording = False
            self.snapshots = []
            return None
        
        # Create recording object
        duration = self.snapshots[-1].timestamp
        recording = CustomActionRecording(
            name=action_name,
            created_at=self.record_start_time,
            duration=duration,
            sample_rate=len(self.snapshots) / duration if duration > 0 else 0,
            snapshots=self.snapshots
        )
        
        # Save to file
        filepath = self.storage_dir / f"{action_name}.json"
        try:
            with open(filepath, 'w') as f:
                json.dump(recording.to_dict(), f, indent=2)
            logger.info(f"Saved recording '{action_name}': {len(self.snapshots)} snapshots, {duration:.2f}s")
        except Exception as e:
            logger.error(f"Failed to save recording: {e}")
            self.is_recording = False
            self.snapshots = []
            return None
        
        # Reset state
        self.is_recording = False
        self.snapshots = []
        
        return recording
    
    def cancel_recording(self):
        """Cancel current recording without saving"""
        if self.is_recording:
            logger.info("Recording cancelled")
            self.is_recording = False
            self.snapshots = []
    
    def list_recordings(self) -> List[str]:
        """List all saved custom action names"""
        return [f.stem for f in self.storage_dir.glob("*.json")]
    
    def load_recording(self, action_name: str) -> Optional[CustomActionRecording]:
        """Load a saved custom action recording"""
        filepath = self.storage_dir / f"{action_name}.json"
        if not filepath.exists():
            logger.warning(f"Recording '{action_name}' not found")
            return None
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            return CustomActionRecording.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load recording '{action_name}': {e}")
            return None
    
    def delete_recording(self, action_name: str) -> bool:
        """Delete a saved custom action"""
        filepath = self.storage_dir / f"{action_name}.json"
        if not filepath.exists():
            return False
        
        try:
            filepath.unlink()
            logger.info(f"Deleted recording '{action_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to delete recording '{action_name}': {e}")
            return False
    
    def rename_recording(self, old_name: str, new_name: str) -> bool:
        """Rename a saved custom action"""
        old_path = self.storage_dir / f"{old_name}.json"
        new_path = self.storage_dir / f"{new_name}.json"
        
        if not old_path.exists():
            logger.warning(f"Recording '{old_name}' not found")
            return False
        
        if new_path.exists():
            logger.warning(f"Recording '{new_name}' already exists")
            return False
        
        try:
            # Load, update name, and save to new file
            recording = self.load_recording(old_name)
            if recording:
                recording.name = new_name
                with open(new_path, 'w') as f:
                    json.dump(recording.to_dict(), f, indent=2)
                old_path.unlink()
                logger.info(f"Renamed '{old_name}' to '{new_name}'")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to rename recording: {e}")
            return False
