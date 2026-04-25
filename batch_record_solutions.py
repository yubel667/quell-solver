import os
import subprocess
import argparse

def batch_record():
    parser = argparse.ArgumentParser(description="Batch Quell Solver")
    parser.add_argument("--max-visited", type=int, default=100000, help="Max visited states before aborting")
    args = parser.parse_args()

    questions_dir = "questions"
    solutions_dir = "solutions"
    
    if not os.path.exists(questions_dir):
        print(f"Error: {questions_dir} directory not found.")
        return

    os.makedirs(solutions_dir, exist_ok=True)
    
    levels = [f.replace(".txt", "") for f in os.listdir(questions_dir) if f.endswith(".txt")]
    levels.sort()

    print(f"Found {len(levels)} levels in {questions_dir}.")

    for level in levels:
        solution_path = os.path.join(solutions_dir, f"{level}.json")
        
        if os.path.exists(solution_path):
            # print(f"Skipping {level}, solution already exists.")
            continue
            
        print(f"Solving and recording {level}...")
        try:
            # We call the solver script as a subprocess to handle each level one by one
            # using the existing main() logic which includes --record support.
            cmd = ["python3", "solver.py", level, "--record", "--max-visited", str(args.max_visited)]
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error solving {level}: {e}")

if __name__ == "__main__":
    batch_record()
