import unittest
import os
import board_io
from board import Direction

class TestButtonMechanics(unittest.TestCase):
    def test_button_and_rotatable_spike(self):
        # Load the test-button level
        file_path = os.path.join(os.path.dirname(__file__), "questions/test-button.txt")
        with open(file_path, "r") as f:
            content = f.read()
        
        state = board_io.parse_board(content)
        
        # Initial state: global_direction is LEFT.
        # Rotatable spike at (1,4) acts as SPIKE_LEFT.
        self.assertEqual(state.global_direction, Direction.LEFT)
        
        # Move droplet RIGHT from (1,1).
        # It will pass through (1,2) [BUTTON].
        # Upon entering (1,2), global_direction should become RIGHT.
        # Rotatable spike at (1,4) should now act as SPIKE_RIGHT.
        # Move RIGHT into SPIKE_RIGHT hits the wall side (LEFT side).
        # So it should STOP at (1,3).
        
        result = state.get_next_state(0, Direction.RIGHT)
        self.assertIsNotNone(result)
        
        final_state, _ = result
        
        # Verify global direction changed
        self.assertEqual(final_state.global_direction, Direction.RIGHT)
        
        # Verify droplet stopped at (1,3)
        self.assertEqual(final_state.droplets[0].loc.x, 3)
        self.assertEqual(final_state.droplets[0].loc.y, 1)
        
        # Now move LEFT from (1,3).
        # global_direction is still RIGHT.
        # Rotatable spike at (1,4) is still SPIKE_RIGHT.
        # Move LEFT into (1,4) [SPIKE_RIGHT] hits the SPIKE side (RIGHT side).
        # Droplet should be destroyed!
        
        result2 = final_state.get_next_state(0, Direction.RIGHT) # Move RIGHT again to hit it
        # Wait, if I move RIGHT from (1,3), I hit (1,4).
        # (1,4) is SPIKE_RIGHT. Moving RIGHT hits the LEFT side (wall side).
        # Wait, I just said that's why it stopped at (1,3).
        
        # If I want to die, I should be on the OTHER side of the spike or move the other way.
        # If I am at (1,5) [PEARL] and move LEFT towards (1,4).
        # global_direction is RIGHT. Spike at (1,4) is SPIKE_RIGHT.
        # Move LEFT into SPIKE_RIGHT hits the spike side. DEATH.
        
        # Let's adjust the test to verify death.
        # First, we need to get to (1,5). But there's no button on that side.
        # Let's just manually set up a state.
        
    def test_rotatable_spike_lethality(self):
        file_path = os.path.join(os.path.dirname(__file__), "questions/test-button.txt")
        with open(file_path, "r") as f:
            content = f.read()
        state = board_io.parse_board(content)
        
        # Manually set state: Droplet at (1,5), global_direction is RIGHT.
        state.droplets[0].loc.x = 5
        state.global_direction = Direction.RIGHT
        
        # Move LEFT into (1,4) [ROTATABLE_SPIKE which is currently SPIKE_RIGHT]
        # This hits the spike side.
        result = state.get_next_state(0, Direction.LEFT)
        self.assertIsNone(result, "Droplet should be destroyed")

if __name__ == "__main__":
    unittest.main()
