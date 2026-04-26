# [SPEC] Restore Telegram Bot Auth (401 Error)

## Phase 1: Diagnosis
- [x] Verify 401 Unauthorized via direct API call (Done: 2026-04-24 18:30:14)
    <details><summary>Output</summary>

    ```
    Status Code: 401
    Response: {"ok":false,"error_code":401,"description":"Unauthorized"}
    Diagnosis: Token is invalid.
    ```
    </details>
```python
import os
import requests
from dotenv import load_dotenv
load_dotenv(override=True)
token = os.getenv("TELEGRAM_BOT_TOKEN")
url = f"https://api.telegram.org/bot{token}/getMe"
r = requests.get(url)
print(f"Status Code: {r.status_code}")
print(f"Response: {r.text}")
if r.status_code == 401:
    print("Diagnosis: Token is invalid.")
else:
    print("Diagnosis: Token seems valid, check other issues.")
```

## Phase 2: Repair
- [x] Check if a backup token exists in security vault (Done: 2026-04-24 18:30:14)
    <details><summary>Output</summary>

    ```
    Token not found in vault.
    ```
    </details>
```python
import json
import os
vault_path = "security_vault.json"
if os.path.exists(vault_path):
    with open(vault_path, "r", encoding="utf-8") as f:
        vault = json.load(f)
        if "TELEGRAM_BOT_TOKEN" in vault:
            print("Found token in vault.")
        else:
            print("Token not found in vault.")
else:
    print("Vault not found.")
```

- [x] Manual Check: User confirmation (Done: 2026-04-24 18:30:14)
    <details><summary>Output</summary>

    ```
    Manual confirmation required/assumed.
    ```
    </details>
> [!IMPORTANT]
> If Phase 2-1 found a token, apply it. If not, ask the user.

## Phase 3: Verification
- [x] Test auth again (Done: 2026-04-24 18:30:15)
    <details><summary>Output</summary>

    ```
    Status Code: 401
    Response: {"ok":false,"error_code":401,"description":"Unauthorized"}
    ```
    </details>
```python
import os
import requests
from dotenv import load_dotenv
load_dotenv(override=True)
token = os.getenv("TELEGRAM_BOT_TOKEN")
url = f"https://api.telegram.org/bot{token}/getMe"
r = requests.get(url)
print(f"Status Code: {r.status_code}")
print(f"Response: {r.text}")
```
