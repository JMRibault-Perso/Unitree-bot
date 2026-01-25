"""
State Machine - Tracks FSM state and validates transitions
Clean version with only valid FSM states from official documentation
"""

from typing import Optional, Set
from dataclasses import dataclass
from enum import Enum
import logging

from ..api.constants import FSMState, LEDColor, FSM_TO_LED
from ..core.event_bus import EventBus, Events

logger = logging.getLogger(__name__)


@dataclass
class RobotState:
    """Current robot state"""
    fsm_state: FSMState
    led_color: LEDColor
    fsm_mode: Optional[int] = None  # Additional mode info from robot
    task_id: Optional[int] = None   # Current arm task
    error: Optional[str] = None


class StateMachine:
    """
    Manages robot FSM state and validates transitions
    Based on official Unitree documentation: https://support.unitree.com/home/en/G1_developer/sport_services_interface
    """
    
    # Valid state transitions (from → {to, to, ...})
    # Only includes FSM states that actually exist in robot firmware
    TRANSITIONS = {
        # Zero Torque Mode (0) - All motors passive, no damping
        FSMState.ZERO_TORQUE: {
            FSMState.DAMP,            # L2+Y - Enter damping mode
            FSMState.SQUAT_TO_STAND,  # 706 - Emergency recovery
            FSMState.STAND_UP,        # 702 - Emergency recovery
        },
        
        # Damping Mode (1) - Recovery and transition point, no balance control
        FSMState.DAMP: {
            FSMState.ZERO_TORQUE,     # L2+Y or L2+R2 - Back to zero torque
            FSMState.START,           # L2+UP - Enter ready mode
            FSMState.SIT,             # L2+LEFT - Sit down
            FSMState.SQUAT,           # L2+DOWN - Squat position
            FSMState.SQUAT_TO_STAND,  # 706 - Emergency recovery (squat up/down)
            FSMState.STAND_UP,        # 702 - Emergency recovery (stand from lying)
        },
        
        # Position Control Squat (2) - No balance control
        FSMState.SQUAT: {
            FSMState.START,           # L2+UP - Back to ready
            FSMState.DAMP,            # Emergency stop
            FSMState.SQUAT_TO_STAND,  # Stand up from squat
        },
        
        # Position Control Sit Down (3) - No balance control
        FSMState.SIT: {
            FSMState.START,           # L2+UP - Back to ready
            FSMState.DAMP,            # Emergency stop
        },
        
        # Lock Standing (4) - No balance control
        FSMState.LOCK_STANDING: {
            FSMState.START,           # Back to ready
            FSMState.DAMP,            # Emergency stop
            FSMState.LOCK_STAND,      # Enter walk mode with balance
        },
        
        # Ready/Start Mode (200) - Preparatory posture
        FSMState.START: {
            FSMState.DAMP,            # L2+Y - Emergency stop
            FSMState.SIT,             # Sit down
            FSMState.SQUAT,           # Squat position
            FSMState.LOCK_STAND,      # L2+R1 - Enter walk mode
            FSMState.LOCK_STAND_ADV,  # Enter advanced walk mode
            FSMState.RUN,             # Enter run mode
        },
        
        # Walk Mode (500) - Main operation with balance control
        FSMState.LOCK_STAND: {
            FSMState.DAMP,            # Emergency stop
            FSMState.START,           # Back to ready
            FSMState.LOCK_STAND_ADV,  # Switch to advanced walk
            FSMState.RUN,             # Speed up to run mode
            FSMState.SQUAT_TO_STAND,  # Squat toggle
        },
        
        # Walk Mode-3Dof-waist (501) - Advanced walk with 3DOF waist
        FSMState.LOCK_STAND_ADV: {
            FSMState.DAMP,            # Emergency stop
            FSMState.START,           # Back to ready
            FSMState.LOCK_STAND,      # Switch to basic walk
            FSMState.RUN,             # Speed up to run mode
            FSMState.SQUAT_TO_STAND,  # Squat toggle
        },
        
        # Balance Squat, Squat Stand (706) - Bidirectional squat toggle
        FSMState.SQUAT_TO_STAND: {
            FSMState.DAMP,            # Emergency stop (often auto-transitions here)
            FSMState.LOCK_STAND,      # Enter walk mode
            FSMState.LOCK_STAND_ADV,  # Enter advanced walk mode
            FSMState.RUN,             # Enter run mode
        },
        
        # Lie Down, Stand Up (702) - Recovery from lying position
        FSMState.STAND_UP: {
            FSMState.DAMP,            # Emergency stop
            FSMState.START,           # Return to ready
            FSMState.LOCK_STAND,      # Enter walk mode
            FSMState.LOCK_STAND_ADV,  # Enter advanced walk mode
            FSMState.RUN,             # Enter run mode
        },
        
        # Run Mode (801) - Fast motion with balance control
        FSMState.RUN: {
            FSMState.DAMP,            # Emergency stop
            FSMState.START,           # Back to ready
            FSMState.LOCK_STAND,      # Slow down to walk
            FSMState.LOCK_STAND_ADV,  # Slow down to advanced walk
            FSMState.SQUAT_TO_STAND,  # Squat toggle
        },
    }
    
    def __init__(self):
        self._current_state = RobotState(
            fsm_state=FSMState.ZERO_TORQUE,
            led_color=LEDColor.PURPLE
        )
    
    @property
    def current_state(self) -> RobotState:
        """Get current robot state"""
        return self._current_state
    
    @property
    def fsm_state(self) -> FSMState:
        """Get current FSM state"""
        return self._current_state.fsm_state
    
    @property
    def led_color(self) -> LEDColor:
        """Get current LED color"""
        return self._current_state.led_color
    
    def can_transition(self, to_state: FSMState) -> bool:
        """
        Check if transition is valid
        
        Args:
            to_state: Target FSM state
            
        Returns:
            True if transition is allowed
        """
        from_state = self._current_state.fsm_state
        
        if from_state not in self.TRANSITIONS:
            logger.warning(f"Unknown source state: {from_state}")
            return False
            
        allowed_transitions = self.TRANSITIONS[from_state]
        is_valid = to_state in allowed_transitions
        
        if not is_valid:
            logger.info(f"Invalid transition: {from_state} → {to_state}")
            logger.info(f"Valid transitions from {from_state}: {list(allowed_transitions)}")
        
        return is_valid
    
    def get_available_transitions(self) -> Set[FSMState]:
        """
        Get valid transitions from current state
        
        Returns:
            Set of valid target states
        """
        current = self._current_state.fsm_state
        return self.TRANSITIONS.get(current, set())
    
    def update_state(self, fsm_state: FSMState, fsm_mode: Optional[int] = None, 
                    task_id: Optional[int] = None, error: Optional[str] = None) -> bool:
        """
        Update robot state
        
        Args:
            fsm_state: New FSM state
            fsm_mode: Optional mode info
            task_id: Optional arm task ID
            error: Optional error message
            
        Returns:
            True if state was updated
        """
        try:
            # Determine LED color from FSM state
            led_color = FSM_TO_LED.get(fsm_state, LEDColor.BLUE)
            
            # Create new state
            old_state = self._current_state
            self._current_state = RobotState(
                fsm_state=fsm_state,
                led_color=led_color,
                fsm_mode=fsm_mode,
                task_id=task_id,
                error=error
            )
            
            # Emit state change event
            if old_state.fsm_state != fsm_state:
                EventBus.instance().emit(Events.STATE_CHANGED, {
                    'old_state': old_state.fsm_state,
                    'new_state': fsm_state,
                    'led_color': led_color.value
                })
                logger.info(f"State transition: {old_state.fsm_state.name} → {fsm_state.name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating state: {e}")
            return False
    
    def validate_transition(self, to_state: FSMState) -> tuple[bool, str]:
        """
        Validate transition with detailed reason
        
        Args:
            to_state: Target state
            
        Returns:
            (is_valid, reason)
        """
        from_state = self._current_state.fsm_state
        
        if from_state not in self.TRANSITIONS:
            return False, f"Unknown source state: {from_state}"
        
        if to_state in self.TRANSITIONS[from_state]:
            return True, f"Valid transition: {from_state.name} → {to_state.name}"
        else:
            valid = [s.name for s in self.TRANSITIONS[from_state]]
            return False, f"Invalid transition: {from_state.name} → {to_state.name}. Valid: {valid}"
    
    def reset(self):
        """Reset to initial state"""
        self._current_state = RobotState(
            fsm_state=FSMState.ZERO_TORQUE,
            led_color=LEDColor.PURPLE
        )
        logger.info("State machine reset to ZERO_TORQUE")