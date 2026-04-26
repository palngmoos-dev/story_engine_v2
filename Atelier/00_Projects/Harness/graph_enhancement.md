# [SPEC] Obsidian Graph Enhancement (Linking)

## Phase 1: Hub Refinement
- [x] Update 00_Brain_Index.md with descriptive and functional links (Done: 2026-04-24 19:27:46)
    <details><summary>Output</summary>

    ```
    Manual confirmation required/assumed.
    ```
    </details>
```python
content = """# 🧠 Grand Atelier 지식 신경망 (Brain Index)

## 🏗️ 시스템 근간 (Areas)
- [[10_Areas/AGENT_RULES|🤖 에이전트 운영 규칙]]
- [[10_Areas/RULES|📜 일반 작업 원칙]]
- [[10_Areas/Design/System_Overview|🏛️ 시스템 전체 개요]]

## 🎨 설계 및 의사결정 (Design & ADR)
- [[10_Areas/Design/ADR-001-harness-system|🛠️ ADR-001: 하네스 엔진 도입]]
- [[10_Areas/Design/ADR-002-obsidian-integration|💎 ADR-002: 옵시디언 PARA 연동]]
- [[10_Areas/Design/Obsidian_Master_Report|📊 글로벌 옵시디언 리포트]]
- [[10_Areas/Design/AI_Plugin_Guide|🤖 AI 플러그인 설정 가이드]]
- [[10_Areas/Design/Global_GitHub_Masters|🌐 GitHub 마스터 리서치]]

## 🚀 현재 작업 및 자산 (Projects & Resources)
- [[Dashboard|🎮 통합 대시보드]]
- [[00_Projects/Harness/restore_telegram|🔌 텔레그램 복구 명세서]]
- [[00_Projects/Harness/setup_obsidian|⚙️ 옵시디언 설정 명세서]]
- [[20_Resources/Story_Assets/Scene_000|🎬 최근 생성된 장면]]
"""
with open("00_Brain_Index.md", "w", encoding="utf-8") as f:
    f.write(content)
print("Updated Brain Index")
```

## Phase 2: Cross-Linking
- [x] Add "Back to Hub" links to all Design documents (Done: 2026-04-24 19:27:46)
    <details><summary>Output</summary>

    ```
    Linked: [[ADR-002-obsidian-integration]]
    Linked: [[AI_Plugin_Guide]]
    Linked: [[brain_transfer]]
    Linked: [[current_stage]]
    Linked: [[Global_GitHub_Masters]]
    Linked: [[handover_antigravity]]
    Linked: [[Obsidian_Master_Report]]
    Linked: [[project_constitution]]
    Linked: [[story_engine]]
    Linked: [[System_Overview]]
    Linked: [[Top_10_Obsidian_Resources]]
    ```
    </details>
```python
import os
design_dir = "10_Areas/Design"
if os.path.exists(design_dir):
    for f_name in os.listdir(design_dir):
        if f_name.endswith(".md"):
            path = os.path.join(design_dir, f_name)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            if "[[00_Brain_Index]]" not in content:
                with open(path, "a", encoding="utf-8") as f:
                    f.write("\n\n---\n**Map of Content**: [[00_Brain_Index]] | [[Dashboard]]")
                print(f"Linked: {f_name}")
```

## Phase 3: Dashboard Linkage
- [!] Ensure Dashboard links back to Index (FAILED: 2026-04-24 19:27:46)
    <details open><summary>Error Output</summary>

    ```
    Traceback (most recent call last):
      File "E:\myhub\writing\temp_step.py", line 2, in <module>
        if os.path.exists(path):
           ^^
    NameError: name 'os' is not defined. Did you forget to import 'os'?
    ```
    </details>
```python
path = "Dashboard.md"
if os.path.exists(path):
    with open(path, "a", encoding="utf-8") as f:
        f.write("\n\n---\n**🏠 Home**: [[00_Brain_Index]]")
    print("Dashboard linked to Home")
```
