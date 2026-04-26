# [SPEC] Setup Obsidian PARA Structure

## Phase 1: Directory Setup
- [!] Create PARA folders and sub-folders (FAILED: 2026-04-24 18:49:12)
    <details open><summary>Error Output</summary>

    ```
    Directory ready: 00_Projects/Harness
    Traceback (most recent call last):
      File "E:\myhub\writing\temp_step.py", line 10, in <module>
        os.makedirs(d, exist_ok=True)
        ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
      File "<frozen os>", line 236, in makedirs
    FileExistsError: [WinError 183] 파일이 이미 있으므로 만들 수 없습니다: '10_Areas/Design'
    ```
    </details>
```python
import os
dirs = [
    "00_Projects/Harness",
    "10_Areas/Design",
    "20_Resources/Story_Assets",
    "30_Archives",
    "templates"
]
for d in dirs:
    os.makedirs(d, exist_ok=True)
    print(f"Directory ready: {d}")
```

## Phase 2: File Migration
- [x] Move core rules to 10_Areas (Done: 2026-04-24 18:50:04)
    <details><summary>Output</summary>

    ```
    Moved: AGENT_RULES.md -> 10_Areas/AGENT_RULES.md
    Moved: RULES.md -> 10_Areas/RULES.md
    ```
    </details>
```python
import os
import shutil
moves = [
    ("AGENT_RULES.md", "10_Areas/AGENT_RULES.md"),
    ("RULES.md", "10_Areas/RULES.md")
]
for src, dst in moves:
    if os.path.exists(src):
        if os.path.exists(dst): os.remove(dst)
        shutil.move(src, dst)
        print(f"Moved: {src} -> {dst}")
```

- [x] Move specs to 10_Areas/Design (Done: 2026-04-24 18:50:04)
    <details><summary>Output</summary>

    ```
    Moved: v2_specs\brain_transfer.md -> 10_Areas\Design\brain_transfer.md
    Moved: v2_specs\current_stage.md -> 10_Areas\Design\current_stage.md
    Moved: v2_specs\handover_antigravity.md -> 10_Areas\Design\handover_antigravity.md
    Moved: v2_specs\project_constitution.md -> 10_Areas\Design\project_constitution.md
    Moved: v2_specs\story_engine.md -> 10_Areas\Design\story_engine.md
    ```
    </details>
```python
import os
import shutil
import glob
files = glob.glob("v2_specs/*")
for f in files:
    if os.path.isfile(f):
        target = os.path.join("10_Areas", "Design", os.path.basename(f))
        if os.path.exists(target): os.remove(target)
        shutil.move(f, target)
        print(f"Moved: {f} -> {target}")
```

- [x] Move harness specs to 00_Projects/Harness (Done: 2026-04-24 19:03:03)
```python
import os
import shutil
import glob
files = glob.glob("harness/*")
for f in files:
    if os.path.isfile(f):
        target = os.path.join("00_Projects", "Harness", os.path.basename(f))
        if os.path.exists(target): os.remove(target)
        shutil.move(f, target)
        print(f"Moved: {f} -> {target}")
```

## Phase 3: Hub Creation
- [x] Create Brain Index.md (Done: 2026-04-24 19:03:03)
    <details><summary>Output</summary>

    ```
    Manual confirmation required/assumed.
    ```
    </details>
```python
content = """# 🧠 Brain Index

## Core Rules
- [[10_Areas/AGENT_RULES|Agent Rules]]
- [[10_Areas/RULES|General Rules]]

## Design & Specs
- [[10_Areas/Design/project_constitution|Project Constitution]]
- [[10_Areas/Design/current_stage|Current Stage]]

## Decision Records
- [[10_Areas/Design/ADR-001-harness-system|ADR-001: Harness System]]
- [[10_Areas/Design/ADR-002-obsidian-integration|ADR-002: Obsidian Integration]]
"""
with open("00_Brain_Index.md", "w", encoding="utf-8") as f:
    f.write(content)
print("Created Brain Index.md")
```

## Phase 4: Documentation
- [x] Create ADR-002: Obsidian Integration (Done: 2026-04-24 19:03:03)
    <details><summary>Output</summary>

    ```
    Manual confirmation required/assumed.
    ```
    </details>
```python
content = """# ADR-002: Obsidian Integration (PARA/LYT)

## Status
Accepted

## Context
As the project grows, we need a better way to visualize and navigate the "Story Engine" data and "Harness" documentation. Obsidian provides a markdown-based knowledge base that fits our workflow.

## Decision
We implement a PARA-based structure:
- **00_Projects**: Active harness specs.
- **10_Areas**: System rules and long-term design docs.
- **20_Resources**: Story assets (characters, scenes).
- **30_Archives**: Completed tasks.

We will use **LYT (Linking Your Thinking)** principles to create MOCs (Maps of Content).

## Consequences
- **Positive**: Visual graph of story elements, easier navigation, structured memory.
- **Negative**: Requires maintaining the vault structure.
"""
with open("10_Areas/Design/ADR-002-obsidian-integration.md", "w", encoding="utf-8") as f:
    f.write(content)
print("Created ADR-002")
```
