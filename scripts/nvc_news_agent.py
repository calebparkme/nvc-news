"""
NVC 일일 뉴스 에이전트
- 영어/한국어 키워드로 NVC 관련 최신 정보 검색
- 중복 제거 (URL + 유사 제목)
- 한국어 번역 및 요약
- Discord Webhook으로 전송
"""

import os
import re
import json
import sys
import requests
import anthropic
from datetime import datetime

# ── Secrets 확인 ───────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")

if not ANTHROPIC_API_KEY:
    print("❌ 오류: ANTHROPIC_API_KEY 가 설정되어 있지 않습니다.")
    print("   GitHub 저장소 Settings → Secrets → Actions 에서 추가하세요.")
    sys.exit(1)

if not DISCORD_WEBHOOK_URL:
    print("❌ 오류: DISCORD_WEBHOOK_URL 이 설정되어 있지 않습니다.")
    print("   GitHub 저장소 Settings → Secrets → Actions 에서 추가하세요.")
    sys.exit(1)

# ── 검색 키워드 ────────────────────────────────────────────────────────────────
SEARCH_KEYWORDS = [
    "NVC Nonviolent Communication news 2026",
    "NVC Nonviolent Communication workshop 2026",
    "NVC Nonviolent Communication research 2026",
    "NVC Nonviolent Communication training 2026",
    "NVC Nonviolent Communication community 2026",
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

EMPTY_RESULT = {"news": [], "workshop": [], "research": [], "training": [], "community": []}


def extract_json(text: str) -> dict:
    """텍스트에서 JSON을 추출합니다 (마크다운 코드블록 포함)."""
    text = text.strip()

    # ```json ... ``` 또는 ``` ... ``` 블록 제거
    match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
    if match:
        text = match.group(1)
    else:
        # 중괄호로 시작하는 첫 번째 JSON 객체 추출
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            text = match.group(0)

    return json.loads(text)


def run_agent() -> dict:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = PROMPT.format(keywords="\n".join(f"- {kw}" for kw in SEARCH_KEYWORDS))

    print("Claude API 호출 중...")
    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            tools=[{
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 6,
            }],
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APIError as e:
        print(f"❌ Anthropic API 오류: {e}")
        raise

    print(f"응답 stop_reason: {response.stop_reason}")
    print(f"응답 블록 수: {len(response.content)}")

    for i, block in enumerate(response.content):
        print(f"  블록 {i}: type={block.type}")
        if block.type == "text":
            print(f"  텍스트 미리보기: {block.text[:200]}")
            try:
                return extract_json(block.text)
            except (json.JSONDecodeError, AttributeError) as e:
                print(f"⚠️  JSON 파싱 실패: {e}")
                print(f"전체 텍스트:\n{block.text}")

    print("⚠️  텍스트 블록에서 JSON을 찾지 못했습니다. 빈 결과 반환.")
    return EMPTY_RESULT


def is_valid_url(url: str) -> bool:
    """URL에 실제로 접근 가능한지 HEAD 요청으로 확인합니다."""
    if not url or not url.startswith("http"):
        return False
    try:
        r = requests.head(url, timeout=5, allow_redirects=True,
                          headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code < 400:
            return True
        # HEAD를 막는 서버는 GET으로 재시도
        if r.status_code == 405:
            r = requests.get(url, timeout=5, allow_redirects=True,
                             headers={"User-Agent": "Mozilla/5.0"})
            return r.status_code < 400
        return False
    except Exception:
        return False


def filter_valid_urls(data: dict) -> dict:
    """각 항목의 URL을 검증하고 유효하지 않은 항목을 제거합니다."""
    result = {}
    for category, items in data.items():
        valid_items = []
        for item in items:
            url = item.get("url", "")
            if is_valid_url(url):
                valid_items.append(item)
            else:
                print(f"  ⚠️  유효하지 않은 URL 제거: {url}")
        result[category] = valid_items
    return result


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
            "footer": {"text": "NVC 뉴스 에이전트 | claude-haiku-4-5 | GitHub Actions"},
        }]
    }

    print("Discord 전송 중...")
    r = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    print(f"Discord 전송 결과: HTTP {r.status_code}")
    if r.status_code not in (200, 204):
        print(f"Discord 응답: {r.text}")
        raise RuntimeError(f"Discord 전송 실패: {r.status_code}")


def main():
    print(f"=== NVC 뉴스 에이전트 시작: {datetime.now().isoformat()} ===")

    data = run_agent()

    print("URL 유효성 검증 중...")
    data = filter_valid_urls(data)

    total = sum(len(v) for v in data.values())
    print(f"유효한 항목 수: {total}")

    if total == 0:
        print("새로운 NVC 소식이 없어 오늘은 전송을 건너뜁니다.")
        return

    send_to_discord(data)
    print("=== 완료 ===")


if __name__ == "__main__":
    main()
