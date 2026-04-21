import unittest
import os
import board_io
from board import Direction

class TestBoardMechanics(unittest.TestCase):
    def test_box_vanish(self):
        # Load the test-box level
        file_path = os.path.join(os.path.dirname(__file__), "questions/test-box.txt")
        with open(file_path, "r") as f:
            content = f.read()
        
        state = board_io.parse_board(content)
        
        # Initial state: 1 droplet, 2 boxes, 1 pearl
        self.assertEqual(len(state.droplets), 1)
        self.assertEqual(len(state.boxes), 2)
        
        # Move droplet RIGHT (at index 0)
        # Sequence expected:
        # Droplet at (1,1) moves right.
        # Hits Box1 at (1,3) -> Pushes it.
        # Box1 (moving) hits Box2 (stationary) at (1,5) -> Both vanish.
        # Droplet continues and collects pearl at (1,6)
        
        result = state.get_next_state(0, Direction.RIGHT)
        self.assertIsNotNone(result, "Move should not result in destruction of all droplets")
        
        final_state, intermediates = result
        
        # Verify boxes are gone
        self.assertEqual(len(final_state.boxes), 0, f"Boxes should have vanished. Remaining: {len(final_state.boxes)}")
        # Droplet should still exist
        self.assertEqual(len(final_state.droplets), 1)
        
        # In test-box.txt, the pearl is at x=6, and the board ends at x=7 (wall).
        # The droplet will collect the pearl and stop at the wall.
        self.assertEqual(len(final_state.pearls), 0, "Pearl should have been collected after boxes vanished")

if __name__ == "__main__":
    unittest.main()
