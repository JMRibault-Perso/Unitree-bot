"""
State Machine - Tracks FSM state and validates transitions
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
    Based on official state diagram
    """
    
    # Valid state transitions (from → {to, to, ...})
    # Based on official Unitree documentation: https://support.unitree.com/home/en/G1_developer/sport_services_interface
    # Only includes FSM states that actually exist in robot firmware
    TRANSITIONS = {
        # Zero Torque Mode (0) - All motors passive, no damping
        FSMState.ZERO_TORQUE: {
            FSMState.DAMP,            # Only allow DAMP mode
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
            FSMState.LOCK_STANDING,   # Stand up from sitting
        },
        
        # Stand up from sitting (4) - No balance control  
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
            FSMState.RUN,             # Enter run mode
        },
        
        # Walk Mode (500) - Main operation with balance control
        FSMState.LOCK_STAND: {
            FSMState.DAMP,            # Emergency stop
            FSMState.RUN,             # Speed up to run mode
            FSMState.SIT,             # Sit down
            FSMState.SQUAT_TO_STAND,  # Squat toggle
        },
        
        # Balance Squat, Squat Stand (706) - Bidirectional squat toggle
        FSMState.SQUAT_TO_STAND: {
            FSMState.DAMP,            # Emergency stop (often auto-transitions here)
            FSMState.LOCK_STAND,      # Enter walk mode
            FSMState.RUN,             # Enter run mode
        },
        
        # Lie Down, Stand Up (702) - Recovery from lying position
        FSMState.STAND_UP: {
            FSMState.DAMP,            # Emergency stop
            FSMState.START,           # Return to ready
            FSMState.LOCK_STAND,      # Enter walk mode
            FSMState.RUN,             # Enter run mode
        },
        
        # Run Mode (801) - Fast motion with balance control
        FSMState.RUN: {
            FSMState.DAMP,            # Emergency stop
            FSMState.LOCK_STAND,      # Slow down to walk mode
            FSMState.SIT,             # Sit down
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
        
        # Always allow transition to same state
        if from_state == to_state:
            return True
        
        # Always allow transition to DAMP or ZERO_TORQUE (emergency stop)
        if to_state in [FSMState.DAMP, FSMState.ZERO_TORQUE]:
            return True
        
        # Check transition table
        valid_targets = self.TRANSITIONS.get(from_state, set())
        return to_state in valid_targets
    
    def update_state(self, fsm_state: FSMState, fsm_mode: Optional[int] = None, 
                     task_id: Optional[int] = None) -> RobotState:
        """
        Update robot state
        
        Args:
            fsm_state: New FSM state
            fsm_mode: FSM mode from robot
            task_id: Current task ID
            
        Returns:
            Updated state
        """
        old_state = self._current_state.fsm_state
        
        # Get LED color for this state
        led_color = FSM_TO_LED.get(fsm_state, LEDColor.BLUE)
        
        # Update state
        self._current_state = RobotState(
            fsm_state=fsm_state,
            led_color=led_color,
            fsm_mode=fsm_mode,
            task_id=task_id
        )
        
        # Emit state change event
        if old_state != fsm_state:
            logger.info(f"State transition: {old_state.name} → {fsm_state.name}")
            EventBus.emit(Events.STATE_CHANGED, self._current_state)
            EventBus.emit(Events.LED_CHANGED, led_color)
        
        return self._current_state
    
    def set_error(self, error: str) -> None:
        """Set error state"""
        self._current_state.error = error
        self._current_state.led_color = LEDColor.RED
        logger.error(f"Robot error: {error}")
        EventBus.emit(Events.ERROR, error)
        EventBus.emit(Events.LED_CHANGED, LEDColor.RED)
    
    def clear_error(self) -> None:
        """Clear error state"""
        if self._current_state.error:
            self._current_state.error = None
            self._current_state.led_color = FSM_TO_LED.get(
                self._current_state.fsm_state, 
                LEDColor.BLUE
            )
            EventBus.emit(Events.LED_CHANGED, self._current_state.led_color)
    
    def is_ready_for_motion(self) -> bool:
        """Check if robot is in a state that allows motion commands"""
        return self._current_state.fsm_state in [
            FSMState.LOCK_STAND,      # Walk mode (500)
            FSMState.LOCK_STAND_ADV,  # Walk mode with 3DOF waist (501)
            FSMState.RUN,             # Run mode (801)
        ]
    
    def is_in_error(self) -> bool:
        """Check if robot is in error state"""
        return self._current_state.error is not None
    
    def get_allowed_transitions(self) -> Set[FSMState]:
        """Get all valid transitions from current state"""
        current = self._current_state.fsm_state
        
        # Get transitions from table
        allowed = set(self.TRANSITIONS.get(current, set()))
        
        # Debug logging
        logger.debug(f"🔍 get_allowed_transitions() called for state: {current.name} ({current.value})")
        logger.debug(f"🔍 From TRANSITIONS dict: {[s.name for s in allowed]}")
        
        # Always allow emergency stops (unless already there)
        allowed.add(FSMState.DAMP)
        allowed.add(FSMState.ZERO_TORQUE)
        
        logger.debug(f"🔍 After adding emergency stops: {[s.name for s in sorted(allowed, key=lambda x: x.value)]}")
        logger.info(f"✓ Returning {len(allowed)} allowed transitions from {current.name}")
        
        return allowed
