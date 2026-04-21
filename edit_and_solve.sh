#!/bin/bash

# Check if level id is provided
if [ -z "$1" ]; then
    echo "Usage: ./edit_and_solve.sh <level_id>"
    exit 1
fi

# Run the editor, and if it exits successfully (e.g. via SAVE), run the solver with autoplay
python3 level_editor.py "$1" && python3 solver_ui.py "$1"
