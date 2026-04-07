"""
NVC 일일 뉴스 에이전트
- 영어/한국어 키워드로 NVC 관련 최신 정보 검색
- 중복 제거 (URL + 유사 제목)
- 한국어 번역 및 요약
- Discord Webhook으로 전송
"""

import os
import json
import requests
import anthropic
from datetime import datetime

DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

SEARCH_KEYWORDS = [
    # 영어
    "NVC Nonviolent Communication news 2026",
    "NVC Nonviolent Communication workshop 2026",
    "NVC Nonviolent Communication research 2026",
    "NVC Nonviolent Communication training 2026",
    "NVC Nonviolent Communication community 2026",
    # 한국어
    "비폭력대화 NVC 뉴스 2026",
    "비폭력대화 NVC 워크샵 2026",
    "비폭력대화 NVC 연구 2026",
    "비폭력대화 NVC 트레이닝 교육 2026",
    "비폭력대화 NVC 커뮤니티 2026",
]

PROMPT = """
오늘 날짜 기준으로 NVC(비폭력 대화, Nonviolent Communication) 관련 최신 정보를 수집하고
한국어로 요약·번역한 뒤 아래 JSON 형식으로만 응답하세요.

## 검색 키워드 (10개 모두 검색)
{keywords}

## 수행 절차
1. 위 키워드로 각각 웹 검색
2. 전체 결과를 합친 뒤 중복 제거:
   - URL이 같은 항목 → 하나만 유지
   - URL이 달라도 제목이 동일하거나 매우 유사한 항목 → 하나만 유지
3. 중복 제거 후 남은 항목을 5개 카테고리로 분류
4. 카테고리별로 관련성 높은 2~3개 항목 선택
5. 영어 등 비한국어 내용은 모두 한국어로 번역

## 출력 형식 (반드시 이 JSON만 출력, 다른 텍스트 없이)
{{
  "news": [
    {{"title": "제목(한국어)", "summary": "2~3줄 요약", "url": "https://..."}}
  ],
  "workshop": [
    {{"title": "제목(한국어)", "summary": "2~3줄 요약", "url": "https://..."}}
  ],
  "research": [
    {{"title": "제목(한국어)", "summary": "2~3줄 요약", "url": "https://..."}}
  ],
  "training": [
    {{"title": "제목(한국어)", "summary": "2~3줄 요약", "url": "https://..."}}
  ],
  "community": [
    {{"title": "제목(한국어)", "summary": "2~3줄 요약", "url": "https://..."}}
  ]
}}

항목이 없는 카테고리는 빈 배열 []로 두세요.
""".strip()


def run_agent() -> dict:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = PROMPT.format(keywords="\n".join(f"- {kw}" for kw in SEARCH_KEYWORDS))

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 12}],
        messages=[{"role": "user", "content": prompt}],
    )

    # 텍스트 블록에서 JSON 추출
    for block in response.content:
        if block.type == "text":
            text = block.text.strip()
            # JSON 코드블록 제거
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            return json.loads(text.strip())

    return {"news": [], "workshop": [], "research": [], "training": [], "community": []}


def format_category(items: list) -> str:
    if not items:
        return "오늘은 새로운 소식이 없습니다."
    lines = []
    for item in items:
        lines.append(f"**{item['title']}**")
        lines.append(item["summary"])
        lines.append(f"🔗 {item['url']}")
        lines.append("")
    return "\n".join(lines).strip()


def send_to_discord(data: dict):
    today = datetime.now().strftime("%Y년 %m월 %d일")

    fields = [
        {"name": "📰 NVC 최신 뉴스/기사", "value": format_category(data.get("news", []))[:1024],      "inline": False},
        {"name": "🏫 NVC 워크샵",         "value": format_category(data.get("workshop", []))[:1024],  "inline": False},
        {"name": "🔬 NVC 연구/논문",       "value": format_category(data.get("research", []))[:1024],  "inline": False},
        {"name": "🎓 NVC 트레이닝",        "value": format_category(data.get("training", []))[:1024],  "inline": False},
        {"name": "🌍 NVC 커뮤니티 소식",   "value": format_category(data.get("community", []))[:1024], "inline": False},
    ]

    payload = {
        "embeds": [{
            "title": f"🕊️ NVC 일일 뉴스 브리핑 — {today}",
            "color": 0x3498DB,
            "fields": fields,
            "footer": {"text": "NVC 뉴스 에이전트 | claude-sonnet-4-6 | GitHub Actions"},
        }]
    }

    r = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    print(f"Discord 전송 결과: HTTP {r.status_code}")
    if r.status_code not in (200, 204):
        print(r.text)
        raise RuntimeError(f"Discord 전송 실패: {r.status_code}")


def main():
    print("NVC 뉴스 수집 시작...")
    data = run_agent()

    total = sum(len(v) for v in data.values())
    print(f"수집된 총 항목 수: {total}")

    if total == 0:
        print("새로운 NVC 소식이 없어 오늘은 전송을 건너뜁니다.")
        return

    send_to_discord(data)
    print("완료!")


if __name__ == "__main__":
    main()
