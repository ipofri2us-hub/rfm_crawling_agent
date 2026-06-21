"""
arXiv / GitHub / HuggingFace에서 신규 항목을 수집하는 모듈.

모든 수집 함수는 아래의 공통 스키마(dict)로 결과를 반환합니다.
  {
    "title": str,
    "summary": str,
    "url": str,
    "source": "arxiv" | "github" | "huggingface",
    "published_date": "YYYY-MM-DD",
    "repo_stars": int | None,
  }
"""

import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

import requests

ARXIV_API_URL = "https://export.arxiv.org/api/query"
GITHUB_API_URL = "https://api.github.com/search/repositories"
HF_API_URL = "https://huggingface.co/api/models"

REQUEST_TIMEOUT = 15


def fetch_arxiv(keywords: list[str], days: int, max_results: int = 10) -> list[dict]:
    """arXiv에서 최근 N일 이내 제출된 논문을 키워드로 검색합니다."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    items = []

    for keyword in keywords:
        params = {
            "search_query": f'all:"{keyword}"',
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": max_results,
        }
        try:
            resp = requests.get(ARXIV_API_URL, params=params, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"[arxiv] '{keyword}' 검색 실패: {e}")
            continue

        ns = {"atom": "http://www.w3.org/2005/Atom"}
        root = ET.fromstring(resp.text)

        for entry in root.findall("atom:entry", ns):
            published_str = entry.findtext("atom:published", default="", namespaces=ns)
            try:
                published = datetime.strptime(published_str, "%Y-%m-%dT%H:%M:%SZ").replace(
                    tzinfo=timezone.utc
                )
            except ValueError:
                continue

            if published < cutoff:
                continue

            items.append(
                {
                    "title": entry.findtext("atom:title", default="", namespaces=ns).strip(),
                    "summary": entry.findtext("atom:summary", default="", namespaces=ns).strip(),
                    "url": entry.findtext("atom:id", default="", namespaces=ns).strip(),
                    "source": "arxiv",
                    "published_date": published.strftime("%Y-%m-%d"),
                    "repo_stars": None,
                }
            )

    return items


def fetch_github(keywords: list[str], star_threshold: int, days: int) -> list[dict]:
    """GitHub에서 키워드와 관련된, 최근 업데이트되고 star가 많은 레포를 검색합니다.

    참고: GitHub Search API는 "최근 N일간 star 증가량"을 직접 제공하지 않으므로,
    여기서는 "최근 N일 이내에 push된 레포 중 현재 star 수가 임계치 이상"인
    레포를 트렌딩 후보로 사용하는 간단한 방식으로 대체합니다.
    """
    pushed_after = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    items = []
    seen_urls = set()

    for keyword in keywords:
        query = f'"{keyword}" in:name,description,readme pushed:>={pushed_after} stars:>={star_threshold}'
        params = {"q": query, "sort": "stars", "order": "desc", "per_page": 10}
        try:
            resp = requests.get(GITHUB_API_URL, params=params, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"[github] '{keyword}' 검색 실패: {e}")
            continue

        for repo in resp.json().get("items", []):
            url = repo["html_url"]
            if url in seen_urls:
                continue
            seen_urls.add(url)

            items.append(
                {
                    "title": repo["full_name"],
                    "summary": repo.get("description") or "",
                    "url": url,
                    "source": "github",
                    "published_date": repo["pushed_at"][:10],
                    "repo_stars": repo["stargazers_count"],
                }
            )

    return items


def fetch_huggingface(keywords: list[str], days: int) -> list[dict]:
    """HuggingFace Hub에서 최근 수정된 모델을 키워드로 검색합니다."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    items = []
    seen_ids = set()

    for keyword in keywords:
        params = {"search": keyword, "sort": "lastModified", "direction": -1, "limit": 10}
        try:
            resp = requests.get(HF_API_URL, params=params, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"[huggingface] '{keyword}' 검색 실패: {e}")
            continue

        for model in resp.json():
            model_id = model.get("id")
            if not model_id or model_id in seen_ids:
                continue

            last_modified = model.get("lastModified", "")
            try:
                modified_dt = datetime.strptime(last_modified[:19], "%Y-%m-%dT%H:%M:%S").replace(
                    tzinfo=timezone.utc
                )
            except ValueError:
                continue

            if modified_dt < cutoff:
                continue

            seen_ids.add(model_id)
            items.append(
                {
                    "title": model_id,
                    "summary": ", ".join(model.get("tags", [])[:10]),
                    "url": f"https://huggingface.co/{model_id}",
                    "source": "huggingface",
                    "published_date": modified_dt.strftime("%Y-%m-%d"),
                    "repo_stars": model.get("likes"),
                }
            )

    return items


def collect_all(config: dict) -> list[dict]:
    """arXiv/GitHub/HuggingFace 결과를 합치고 URL 기준으로 중복을 제거합니다."""
    keywords = config["keywords"]
    days = config["lookback_days"]
    star_threshold = config["github_star_threshold"]
    arxiv_max_results = config.get("arxiv_max_results", 10)

    all_items = []
    all_items += fetch_arxiv(keywords, days, arxiv_max_results)
    all_items += fetch_github(keywords, star_threshold, days)
    all_items += fetch_huggingface(keywords, days)

    deduped = {}
    for item in all_items:
        deduped[item["url"]] = item

    return list(deduped.values())
