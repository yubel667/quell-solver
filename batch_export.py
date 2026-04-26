import os
import sys
import subprocess
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

# Try to import tqdm, but don't fail if not present
try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

def export_single(level_id):
    """Worker function to export a single level."""
    try:
        # Run export_webp.py as a subprocess
        result = subprocess.run(
            [sys.executable, "export_webp.py", level_id],
            capture_output=True,
            text=True,
            check=True
        )
        return level_id, True, result.stdout
    except subprocess.CalledProcessError as e:
        return level_id, False, e.stderr

def batch_export():
    parser = argparse.ArgumentParser(description="Batch export Quell solutions to WebP.")
    parser.add_argument("-p", "--parallelism", type=int, default=4, help="Number of parallel exports (default: 4)")
    parser.add_argument("--force", action="store_true", help="Force re-export even if WebP exists")
    args = parser.parse_args()

    questions_dir = "questions"
    solutions_dir = "solutions"
    
    if not os.path.exists(questions_dir):
        print(f"Error: {questions_dir} folder not found.")
        return

    os.makedirs(solutions_dir, exist_ok=True)

    # Get all .txt files from questions directory
    levels = [f[:-4] for f in os.listdir(questions_dir) if f.endswith(".txt")]
    levels.sort()

    # Filter out levels that already have a .webp solution unless --force is used
    if not args.force:
        to_export = []
        for level in levels:
            # We only export if a solution JSON exists (meaning it's solvable)
            json_path = os.path.join(solutions_dir, f"{level}.json")
            webp_path = os.path.join(solutions_dir, f"{level}.webp")
            
            if os.path.exists(json_path):
                # Check if solvable (steps is not null)
                import json
                try:
                    with open(json_path, 'r') as f:
                        data = json.load(f)
                        if data.get("steps") is not None and not os.path.exists(webp_path):
                            to_export.append(level)
                except:
                    pass
    else:
        to_export = []
        for level in levels:
            json_path = os.path.join(solutions_dir, f"{level}.json")
            if os.path.exists(json_path):
                import json
                try:
                    with open(json_path, 'r') as f:
                        data = json.load(f)
                        if data.get("steps") is not None:
                            to_export.append(level)
                except:
                    pass

    if not to_export:
        print("No new solvable solutions to export.")
        return

    print(f"Found {len(to_export)} solvable levels to export. Starting batch export with parallelism={args.parallelism}...")

    # Use ThreadPoolExecutor to manage subprocesses in parallel
    with ThreadPoolExecutor(max_workers=args.parallelism) as executor:
        futures = {executor.submit(export_single, level_id): level_id for level_id in to_export}
        
        if tqdm:
            pbar = tqdm(total=len(futures), desc="Exporting WebPs", unit="file")
        else:
            pbar = None

        for future in as_completed(futures):
            level_id, success, output = future.result()
            if not success:
                print(f"\nError exporting {level_id}:")
                print(output)
            if pbar:
                pbar.update(1)
            else:
                status = "SUCCESS" if success else "FAILED"
                print(f"[{status}] {level_id}")

        if pbar:
            pbar.close()

    print("\nBatch export complete.")

if __name__ == "__main__":
    batch_export()
