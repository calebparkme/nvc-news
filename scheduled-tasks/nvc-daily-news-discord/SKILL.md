---
name: nvc-daily-news-discord
description: 매일 NVC 최신 뉴스/교육/연구 정보를 수집해 한국어로 요약 후 Discord 전송
---

오늘 날짜 기준으로 NVC(비폭력 대화, Nonviolent Communication) 관련 최신 정보를 웹에서 수집하고, 중복을 제거한 뒤 이전에 보낸 적 없는 새 항목만 한국어로 요약·번역하여 Discord Webhook으로 전송하는 작업을 수행하세요.

## 히스토리 파일 경로
C:\Users\caleb\.claude\scheduled-tasks\nvc-daily-news-discord\sent_history.json

## 1단계: 히스토리 로드
Bash 도구로 아래를 실행해 기존에 전송한 URL 목록을 불러오세요:
```python
import json, os
HISTORY_FILE = r"C:\Users\caleb\.claude\scheduled-tasks\nvc-daily-news-discord\sent_history.json"
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        sent_urls = set(json.load(f))
else:
    sent_urls = set()
print(f"기존 전송 항목 수: {len(sent_urls)}")
```

## 2단계: 웹 검색 (영어 + 한국어 키워드)
WebSearch 도구를 사용해 아래 10개 키워드로 각각 검색하세요.

**영어 키워드 (5개):**
1. "NVC Nonviolent Communication news 2026"
2. "NVC Nonviolent Communication workshop 2026"
3. "NVC Nonviolent Communication research 2026"
4. "NVC Nonviolent Communication training 2026"
5. "NVC Nonviolent Communication community 2026"

**한국어 키워드 (5개):**
6. "비폭력대화 NVC 뉴스 2026"
7. "비폭력대화 NVC 워크샵 2026"
8. "비폭력대화 NVC 연구 2026"
9. "비폭력대화 NVC 트레이닝 교육 2026"
10. "비폭력대화 NVC 커뮤니티 2026"

검색 결과를 수집할 때 각 항목의 URL과 제목을 함께 기록하세요.

## 3단계: 중복 제거 (2중 필터)
수집한 전체 결과에서 아래 두 가지를 순서대로 제거하세요:

**3-1. 이번 실행 내 중복 제거**
- 10개 키워드 검색 결과를 합친 뒤 URL 기준으로 중복 항목 제거 (같은 URL이 여러 키워드에서 나왔으면 하나만 유지)
- URL이 달라도 제목이 동일하거나 매우 유사한 항목도 하나만 유지

**3-2. 과거 전송 이력 제거**
- sent_urls에 이미 있는 URL은 모두 제외

## 4단계: 분류 및 요약 (새 항목만)
중복 제거 후 남은 항목을 아래 5개 카테고리로 분류하고, 카테고리별로 가장 관련성 높은 2~3개 항목을 선택하세요:
- 📰 NVC 최신 뉴스/기사
- 🏫 NVC 워크샵
- 🔬 NVC 연구/논문
- 🎓 NVC 트레이닝
- 🌍 NVC 커뮤니티 소식

## 5단계: 한국어 번역 및 정리
한국어가 아닌 모든 내용(제목, 요약)을 한국어로 번역하세요.
각 항목 형식:
```
**[제목(한국어)]**
요약 2~3줄
🔗 출처: URL
```
항목이 없는 카테고리는 "오늘은 새로운 소식이 없습니다."로 표시하세요.

모든 카테고리에 새 항목이 하나도 없으면 Discord 전송을 건너뛰고 "새로운 NVC 소식이 없어 오늘은 전송을 건너뜁니다."를 출력한 뒤 종료하세요.

## 6단계: Discord 전송
아래 Python 스크립트를 작성하고 Bash 도구로 실행하세요.
수집한 실제 내용과 이번에 새로 수집한 URL 목록(new_urls)을 채워넣으세요.
(requests 없으면 먼저: pip install requests)

```python
import requests, json, os
from datetime import datetime

WEBHOOK_URL = "https://discord.com/api/webhooks/1490449299199496264/NXpGySF76HpnXdWZpzAOJJIV0j5OE9So5LWFhuKSFU5E7B9J6kXFgDav3MPkmWbqbXV0"
HISTORY_FILE = r"C:\Users\caleb\.claude\scheduled-tasks\nvc-daily-news-discord\sent_history.json"

# 이번에 새로 전송하는 항목의 URL 전체 목록
new_urls = [
    # "https://example.com/article1",
]

# 수집한 내용으로 채우세요 (각 1024자 이하)
news_text      = """[NVC 뉴스/기사 내용]"""
workshop_text  = """[NVC 워크샵 내용]"""
research_text  = """[NVC 연구/논문 내용]"""
training_text  = """[NVC 트레이닝 내용]"""
community_text = """[NVC 커뮤니티 소식 내용]"""

today = datetime.now().strftime("%Y년 %m월 %d일")

payload = {
    "embeds": [{
        "title": f"🕊️ NVC 일일 뉴스 브리핑 — {today}",
        "color": 0x3498DB,
        "fields": [
            {"name": "📰 NVC 최신 뉴스/기사", "value": news_text[:1024],      "inline": False},
            {"name": "🏫 NVC 워크샵",         "value": workshop_text[:1024],  "inline": False},
            {"name": "🔬 NVC 연구/논문",       "value": research_text[:1024],  "inline": False},
            {"name": "🎓 NVC 트레이닝",        "value": training_text[:1024],  "inline": False},
            {"name": "🌍 NVC 커뮤니티 소식",   "value": community_text[:1024], "inline": False},
        ],
        "footer": {"text": "NVC 뉴스 에이전트 | claude-sonnet-4-6"}
    }]
}

r = requests.post(WEBHOOK_URL, json=payload)
print(f"Discord 전송 결과: HTTP {r.status_code}")

if r.status_code in (200, 204):
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)
    else:
        existing = []
    updated = list(set(existing + new_urls))
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(updated, f, ensure_ascii=False, indent=2)
    print(f"히스토리 업데이트 완료: 총 {len(updated)}개 URL 저장됨")
else:
    print(r.text)
```

HTTP 200 또는 204가 나오면 성공입니다. 반드시 전송 결과와 히스토리 저장 결과를 확인하고 출력하세요.