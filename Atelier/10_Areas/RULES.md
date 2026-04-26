# AI Development Rules (Safety First)

## 1. Directory Structure & Isolation
- **🔒 Production (Original)**: `E:\myhub\writing` -> **NEVER MODIFY DIRECTLY**.
- **🧪 AI Workspace (Dev)**: `E:\myhub\writing_dev` -> **All coding and testing happens here**.
- **💾 Local Backup**: Backups must be stored in `E:\myhub\backups`.
- **🌐 GitHub**: Approved changes must be pushed to the GitHub repository.
- **Strategy**: AI acts as a "Proposal Generator". The User acts as the "Final Approver".

## 2. Forbidden Actions
- **NO DIRECT WRITES** to `E:\myhub\writing`.
- **NO DELETION/OVERWRITE** of critical files in production.
- **NO MODIFICATION** of security files:
  - `.env`
  - `security_vault.json`
- **NO AUTOMATIC RESTART** of production servers.

## 3. Deployment Workflow
- All changes must be summarized in a `changes.patch` file created in `writing_dev`.
- **Apply Workflow**:
  ```bash
  cd /mnt/e/myhub/writing
  git apply ../writing_dev/changes.patch
  ```

## 4. Development & Testing
- **Dev Server Port**: Always use **8001**.
- **Production Server Port**: **8000** (Never touch).
- **Test Command**: `python -m uvicorn v2_core.api.api_server:app --port 8001`

## 5. Excluded from Tracking/Patching
- `backups/`
- `archive_v1/`, `archive_v2/`
- `__pycache__/`
- `.git/`

## 6. Closing Report Requirements
Every task completion must report:
1. **수정 파일 목록** (List of modified files)
2. **changes.patch 생성 여부** (Patch creation status)
3. **적용 명령어 한 줄** (One-liner apply command)
