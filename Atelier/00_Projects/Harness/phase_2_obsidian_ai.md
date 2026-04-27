# [SPEC] Phase 2: Obsidian AI & Dashboard Setup (Corrected)

## Phase 1: Dashboard Creation
- [x] Create main Dashboard.md (Done: 2026-04-24 19:18:00)
    <details><summary>Output</summary>

    ```
    Manual confirmation required/assumed.
    ```
    </details>
```python
bt = "```"
content = f"""# 🚀 Grand Atelier 관제탑

## 📅 진행 중인 작업 (Projects)
{bt}dataview
TABLE status as "상태", priority as "우선순위"
FROM "00_Projects"
WHERE status != "Completed"
SORT file.mtime desc
{bt}

## 🎭 최신 스토리 자산 (Recent Assets)
{bt}dataview
LIST FROM "20_Resources/Story_Assets"
LIMIT 10
SORT file.mtime desc
{bt}

## 🧠 핵심 시스템 규칙
- [[10_Areas/AGENT_RULES|에이전트 규칙]]
- [[10_Areas/Design/Obsidian_Master_Report|마스터 리서치 보고서]]
"""
with open("Dashboard.md", "w", encoding="utf-8") as f:
    f.write(content)
print("Created Dashboard.md")
```

## Phase 2: Standardized Templates
- [x] Create Scene and Character templates (Done: 2026-04-24 19:18:00)
    <details><summary>Output</summary>

    ```
    Manual confirmation required/assumed.
    ```
    </details>
```python
scene_tmp = """---
type: scene
status: draft
lead: 
location: 
time: 
---
# Scene: {{title}}

## 📝 Summary
- 

## 🎭 Characters
- 

## 🎬 Narrative
- 
"""

char_tmp = """---
type: character
role: 
goal: 
conflict: 
---
# Character: {{title}}

## 👤 Profile
- **Age**: 
- **Personality**: 

## 🕸️ Relationships
- [[Lead Character]]: 
"""

import os
os.makedirs("Templates", exist_ok=True)
with open("Templates/Scene_Template.md", "w", encoding="utf-8") as f:
    f.write(scene_tmp)
with open("Templates/Character_Template.md", "w", encoding="utf-8") as f:
    f.write(char_tmp)
print("Created Templates")
```

## Phase 3: AI Optimization Guide
- [x] Create AI Plugin Guide (Done: 2026-04-24 19:18:00)
    <details><summary>Output</summary>

    ```
    Created AI Guide
    ```
    </details>
```python
content = """# 🤖 AI Plugin Optimization Guide

## 1. Copilot for Obsidian
- **Index Range**: `00_Projects`, `10_Areas`, `20_Resources` 모두 인덱싱하세요.
- **System Prompt**: "당신은 Grand Atelier의 전문 스토리 어시스턴트입니다. 10_Areas/AGENT_RULES의 규칙을 준수하며 답변하세요."

## 2. Always respond and explain code in Korean. Please print out the progress and status in Korean as well.

## 3. Smart Connections
- **Folder Exclusion**: `30_Archives`, `.git`, `scripts`는 제외하여 임베딩 품질을 높이세요.
- **Link Usage**: 캐릭터나 장소를 언급할 때 반드시 `[[ ]]`를 사용하면 AI가 연결 고리를 더 잘 찾습니다.
"""
with open("10_Areas/Design/AI_Plugin_Guide.md", "w", encoding="utf-8") as f:
    f.write(content)
print("Created AI Guide")
```
