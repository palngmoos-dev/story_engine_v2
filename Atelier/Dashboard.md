# 🚀 Grand Atelier 관제탑

## 📅 진행 중인 작업 (Projects)
```dataview
TABLE status as "상태", priority as "우선순위"
FROM "00_Projects"
WHERE status != "Completed"
SORT file.mtime desc
```

## 🎭 최신 스토리 자산 (Recent Assets)
```dataview
LIST FROM "20_Resources/Story_Assets"
LIMIT 10
SORT file.mtime desc
```

## 🧠 핵심 시스템 규칙
- [[10_Areas/AGENT_RULES|에이전트 규칙]]
- [[10_Areas/Design/Obsidian_Master_Report|마스터 리서치 보고서]]


---
**🏠 Home**: [[00_Brain_Index]]