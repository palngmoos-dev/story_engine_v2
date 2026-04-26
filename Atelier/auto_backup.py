import os
import shutil
import logging
import subprocess
from datetime import datetime
from pathlib import Path

# --- Configuration ---
SOURCE_DIR = "E:\\myhub\\writing"
DEST_A_WIN = "E:\\myhub_backups"
DEST_B_WIN = "G:\\My Drive\\GrandAtelier_Cloud_Backup"
MAX_BACKUPS = 5

LOG_FILE = os.path.join(SOURCE_DIR, "backup_log.txt")

# Exclusion patterns (for reference, though make_archive is broad)
IGNORE_PATTERNS = [".git", "__pycache__", "venv", ".venv", "logs", "backups", "backup_log.txt", ".zip"]

# --- Setup Logging ---
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

def backup_to_path_shutil(zip_file, path_name, path_destination):
    """Standard backup using shutil (for E: drive)."""
    try:
        dest_path = Path(path_destination)
        if not dest_path.exists():
            dest_path.mkdir(parents=True, exist_ok=True)
        
        target_file = dest_path / os.path.basename(zip_file)
        shutil.copy2(zip_file, target_file)
        
        msg = f"SUCCESS: {path_name} ({path_destination})"
        print(msg)
        logging.info(msg)
        return True
    except Exception as e:
        msg = f"FAILED: {path_name} ({path_destination}) - Reason: {e}"
        print(msg)
        logging.error(msg)
        return False

def backup_to_g_drive_via_powershell(zip_filename, path_name, win_destination):
    """Backup to G: drive via Windows PowerShell to bypass WSL permission issues."""
    try:
        # The zip is already on E: drive
        win_source_file = os.path.join(DEST_A_WIN, zip_filename)
        
        # PowerShell command: Copy-Item
        # We ensure the destination directory exists first
        ps_command = f"if (!(Test-Path '{win_destination}')) {{ New-Item -ItemType Directory -Force -Path '{win_destination}' }}; Copy-Item -Path '{win_source_file}' -Destination '{win_destination}' -Force"
        
        result = subprocess.run(
            ["powershell.exe", "-Command", ps_command],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            msg = f"SUCCESS: {path_name} ({win_destination} via PowerShell)"
            print(msg)
            logging.info(msg)
            return True
        else:
            raise Exception(result.stderr.strip())
            
    except Exception as e:
        msg = f"FAILED: {path_name} ({win_destination}) - Reason: {e}"
        print(msg)
        logging.error(msg)
        return False

def get_rotation_candidates(directory_path, max_count):
    """Identifies backup files that exceed the rotation limit."""
    try:
        p = Path(directory_path)
        if not p.exists():
            return []
            
        # List all backup zips
        backups = sorted(
            [f for f in p.glob("grand_atelier_backup_*.zip")],
            key=os.path.getmtime
        )
        
        if len(backups) > max_count:
            return backups[:-max_count] # All except the newest 'max_count'
        return []
    except Exception as e:
        print(f"[ERROR] Failed to scan for rotation candidates: {e}")
        return []

def delete_backups(file_list):
    """Deletes the specified list of files."""
    for f in file_list:
        try:
            f.unlink()
            msg = f"DELETED: {f.name} (Rotation Cleanup)"
            print(msg)
            logging.info(msg)
        except Exception as e:
            print(f"[ERROR] Failed to delete {f.name}: {e}")

def main(cleanup=False):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename_base = f"grand_atelier_backup_{timestamp}"
    
    # We create the zip directly on the E: drive to save space on D:
    temp_zip_dir = Path(DEST_A_WIN)
    if not temp_zip_dir.exists():
        temp_zip_dir.mkdir(parents=True, exist_ok=True)
    
    temp_zip_base = temp_zip_dir / zip_filename_base
    
    msg_start = f"--- [START] Backup ({timestamp}) ---"
    print(msg_start)
    logging.info(msg_start)
    
    if not cleanup:
        try:
            # 1. Create Archive (E: 드라이브에 직접 생성, IGNORE_PATTERNS 준수)
            print(f"[INFO] Archiving project to {temp_zip_dir} (Respecting ignore patterns)...")
            actual_zip_path = str(temp_zip_base) + ".zip"
            
            import zipfile
            
            with zipfile.ZipFile(actual_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(SOURCE_DIR):
                    # Apply ignore patterns to directories
                    dirs[:] = [d for d in dirs if d not in IGNORE_PATTERNS]
                    
                    for file in files:
                        if file in IGNORE_PATTERNS or file.endswith('.zip'):
                            continue
                        
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, SOURCE_DIR)
                        zipf.write(file_path, arcname)
            
            actual_zip_filename = os.path.basename(actual_zip_path)
            
            msg_archived = f"SUCCESS: Archived to {actual_zip_path}"
            print(msg_archived)
            logging.info(msg_archived)
            
            # 2. Backup to Destinations
            # Path B: Google Drive (via PowerShell)
            backup_to_g_drive_via_powershell(actual_zip_filename, "구글 드라이브", DEST_B_WIN)
            
            # Note: No need to copy to DEST_A because it's already there!

            # 3. Check for rotation candidates
            candidates = get_rotation_candidates(DEST_A_WIN, MAX_BACKUPS)
            if candidates:
                print("\n[ROTATION] 삭제 대상 후보 발견 (5회 초과):")
                for c in candidates:
                    print(f"  - {c.name}")
                print("[ACTION_REQUIRED] 위 파일들을 삭제하시겠습니까? (AI가 사용자에게 질문 예정)")
                
        except Exception as e:
            msg_err = f"[ERROR] Critical error during backup: {e}"
            print(msg_err)
            logging.error(msg_err)
    else:
        # Explicit cleanup mode
        candidates = get_rotation_candidates(DEST_A_WIN, MAX_BACKUPS)
        if candidates:
            print(f"[CLEANUP] {len(candidates)}개의 오래된 백업 삭제 시작...")
            delete_backups(candidates)
        else:
            print("[CLEANUP] 삭제할 오래된 백업이 없습니다.")
    
    msg_end = "--- 백업 프로세스 완료 ---"
    print(msg_end)
    logging.info(msg_end)

if __name__ == "__main__":
    import sys
    do_cleanup = "--cleanup" in sys.argv
    main(cleanup=do_cleanup)
