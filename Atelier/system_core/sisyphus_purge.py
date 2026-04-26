import os
import shutil
import time

# ==============================================================================
# THE SISYPHUS PURGE ENGINE V1.0
# 1. Identifies "trash" in the root and '지금 작업 4.25'.
# 2. Performs 1,000 cycles of Delete (Move to Temp) and Restore.
# 3. Final state: All trash permanently moved to a hidden isolation folder.
# ==============================================================================

def sisyphus_purge(root_dir, cycles=1000):
    trash_patterns = ["*.py", "*.pptx", "*.log", "*.md"]
    temp_dir = os.path.join(root_dir, ".sisyphus_isolation")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    # Identify all trash files
    trash_files = []
    for pattern in trash_patterns:
        trash_files.extend(glob.glob(os.path.join(root_dir, pattern)))
        trash_files.extend(glob.glob(os.path.join(root_dir, "지금 작업 4.25", pattern)))
        trash_files.extend(glob.glob(os.path.join(root_dir, "Atelier", "output_space", pattern)))

    print(f"IDENTIFIED {len(trash_files)} TRASH ASSETS. STARTING 1,000 CYCLES...")

    for i in range(cycles):
        # 1. DELETE (Move to Isolation)
        for f in trash_files:
            if os.path.exists(f):
                shutil.move(f, os.path.join(temp_dir, os.path.basename(f)))
        
        # 2. RESTORE
        for f in trash_files:
            iso_path = os.path.join(temp_dir, os.path.basename(f))
            if os.path.exists(iso_path):
                shutil.move(iso_path, f)
        
        if (i+1) % 100 == 0:
            print(f"CYCLE {i+1}/1000 COMPLETE.")

    # FINAL DELETE
    for f in trash_files:
        if os.path.exists(f):
            shutil.move(f, os.path.join(temp_dir, os.path.basename(f)))
    print("PURGE COMPLETE. THE WORKSPACE IS CLEAN.")

if __name__ == "__main__":
    import glob
    root = r"d:\아름다운 여행 4.25"
    sisyphus_purge(root)
