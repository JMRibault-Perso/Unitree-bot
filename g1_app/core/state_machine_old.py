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
    # Based on official state diagram with L2/R1 transitions
    TRANSITIONS = {
        # Power On → Zero Torque
        FSMState.ZERO_TORQUE: {
            FSMState.DAMP,            # L2+Y
            FSMState.SQUAT_TO_STAND,  # 706 - Squat up in emergency
            FSMState.STAND_UP,        # 702 - Stand up in emergency
        },
        
        # Damping mode - recovery and transition point
        FSMState.DAMP: {
            FSMState.ZERO_TORQUE,     # L2+Y or L2+R2
            FSMState.START,           # L2+UP to Position Mode (Get Ready)
            FSMState.SIT,             # L2+LEFT to Position Mode (Take one's seat)
            FSMState.SQUAT,           # L2+DOWN to Position Mode (Squat)
            FSMState.SQUAT_TO_STAND,  # 706 - Emergency recovery: squat up/down
            FSMState.STAND_UP,        # 702 - Emergency recovery: stand up from lying
        },
        
        # Position Mode - Get Ready (center state)
        FSMState.START: {
            FSMState.DAMP,            # Back to damping
            FSMState.SIT,             # Sit down
            FSMState.STAND_TO_SQUAT,  # Squat down
            # Can enter any main operation control state:
            FSMState.LOCK_STAND,      # Enter walk mode
            FSMState.LOCK_STAND_ADV,  # Enter walk with 3DOF waist
            FSMState.RUN,             # Enter run mode
            FSMState.SQUAT_TO_STAND,  # Transition state (balance control)
            FSMState.LYING_STAND,     # Transition state (balance control)
        },
        
        # MAIN OPERATION CONTROL STATES (All have Balance Control = Yes)
        # These states can freely transition between each other
        
        # Walk Mode (500) - Main operation, slower speed
        FSMState.LOCK_STAND: {
            FSMState.DAMP,            # Emergency stop
            FSMState.START,           # Back to ready position
            FSMState.SIT,             # Sit down
            FSMState.STAND_TO_SQUAT,  # Squat down
            # Transitions to other main operation control states:
            FSMState.LOCK_STAND_ADV,  # Switch to walk with 3DOF waist
            FSMState.RUN,             # Speed up to run mode
            FSMState.SQUAT_TO_STAND,  # Transition state (balance control)
            FSMState.LYING_STAND,     # Transition state (balance control)
        },
        
        # Walk Mode with 3DOF Waist (501) - Main operation with waist articulation
        FSMState.LOCK_STAND_ADV: {
            FSMState.DAMP,            # Emergency stop
            FSMState.START,           # Back to ready position
            FSMState.SIT,             # Sit down
            FSMState.STAND_TO_SQUAT,  # Squat down
            # Transitions to other main operation control states:
            FSMState.LOCK_STAND,      # Switch to basic walk mode
            FSMState.RUN,             # Speed up to run mode
            FSMState.SQUAT_TO_STAND,  # Transition state (balance control)
            FSMState.LYING_STAND,     # Transition state (balance control)
        },
        
        # Run Mode (801) - Main operation, faster speed
        # Supports arm actions when fsm_mode ∈ {0, 3}
        FSMState.RUN: {
            FSMState.DAMP,            # Emergency stop
            FSMState.START,           # Back to ready position
            FSMState.SIT,             # Sit down
            FSMState.STAND_TO_SQUAT,  # Squat down
            # Transitions to other main operation control states:
            FSMState.LOCK_STAND,      # Slow down to walk mode
            FSMState.LOCK_STAND_ADV,  # Slow down to walk with 3DOF waist
            FSMState.SQUAT_TO_STAND,  # Transition state (balance control)
            FSMState.LYING_STAND,     # Transition state (balance control)
        },
        
        # TRANSITION STATES (Also have Balance Control = Yes, part of main operation)
        
        # Squat Toggle (706) - SQUAT_TO_STAND acts as bidirectional squat/stand toggle
        # When standing: robot squats down
        # When squatting: robot stands up
        # Often auto-transitions to DAMP after completing the motion
        FSMState.SQUAT_TO_STAND: {
            FSMState.DAMP,            # Emergency stop (or auto-transition after motion)
            # Can transition to any main operation control state:
            FSMState.LOCK_STAND,      # Go to walk mode
            FSMState.LOCK_STAND_ADV,  # Go to walk with 3DOF waist
            FSMState.RUN,             # Go to run mode
            FSMState.SQUAT_TO_STAND,  # Toggle again (squat ↔ stand)
            FSMState.STAND_TO_SQUAT,  # Alternative squat transition
            FSMState.LYING_STAND,     # Switch to other transition state
        },
        
        # Stand up from lying (708) - Balance control transition
        FSMState.LYING_STAND: {
            FSMState.DAMP,            # Emergency stop
            # Can transition to any main operation control state:
            FSMState.LOCK_STAND,      # Go to walk mode
            FSMState.LOCK_STAND_ADV,  # Go to walk with 3DOF waist
            FSMState.RUN,             # Go to run mode
            FSMState.SQUAT_TO_STAND,  # Switch to other transition state
            FSMState.LYING_STAND,     # Stay in transition (for balance)
        },
        
        # POSITIONAL STATES (No Balance Control - preparatory states)
        
        # Take one's seat
        FSMState.SIT: {
            FSMState.START,    # L2+UP back to Get Ready
            FSMState.STAND_UP, # Stand up from sitting
        },
        
        # Squat position (from Position Mode)
        FSMState.SQUAT: {
            FSMState.START,           # L2+UP to Get Ready
            FSMState.SQUAT_TO_STAND,  # Stand up from squat
        },
        
        # Stand up from sitting
        FSMState.STAND_UP: {
            FSMState.START,           # Return to Get Ready
            FSMState.LOCK_STAND,      # Go to walk mode
            FSMState.LOCK_STAND_ADV,  # Go to walk with 3DOF waist
            FSMState.RUN,             # Go to run mode
        },
        
        # Stand to Squat (707) - Appears to be no-op in standing states
        # Robot firmware rejects this transition when already standing
        # Immediately returns to previous state (e.g., LOCK_STAND)
        FSMState.STAND_TO_SQUAT: {
            FSMState.SQUAT,           # Theoretical destination (may not work in practice)
            FSMState.START,           # Can return to Get Ready
            FSMState.SQUAT_TO_STAND,  # Use this instead for squat toggle
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
            FSMState.START,
            FSMState.LOCK_STAND,
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
