import json
import time
import random
import re
from datetime import datetime, timezone, timedelta
import requests
from tqdm import tqdm
import os

DONE_PATH = "out/done_threads.txt"
os.makedirs("out", exist_ok=True)

SUBREDDIT = "Habs"

# PullPush base (comments)
PULLPUSH_BASE = "https://api.pullpush.io/reddit/search"

# Reddit public JSON search (threads)
REDDIT_SEARCH_URL = f"https://www.reddit.com/r/{SUBREDDIT}/search.json"

GAME_THREAD_RE = re.compile(r"^\s*Game Thread\s*:", re.I)
POST_GAME_RE   = re.compile(r"^\s*Post Game Thread\s*:", re.I)
PRE_GAME_RE    = re.compile(r"^\s*Pre-Game Thread\s*:", re.I)

def is_game_thread_title(title: str) -> bool:
    if not title:
        return False
    t = title.strip()
    if POST_GAME_RE.match(t):  # exclude post-game
        return False
    if PRE_GAME_RE.match(t):   # exclude pre-game
        return False
    return bool(GAME_THREAD_RE.match(t))

def utc_now():
    return datetime.now(timezone.utc)

def to_epoch_days_ago(days: int) -> int:
    return int((utc_now() - timedelta(days=days)).timestamp())

# --- Robust GET with retries/backoff ---
def get_json(url, params=None, headers=None, timeout=60, max_retries=8):
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=timeout)
            if r.status_code in (429, 500, 502, 503, 504):
                raise RuntimeError(f"HTTP {r.status_code} transient")
            r.raise_for_status()
            return r.json()
        except (requests.exceptions.Timeout,
                requests.exceptions.ConnectionError,
                RuntimeError,
                requests.exceptions.HTTPError) as e:
            last_err = e
            sleep_for = min(60, 2 ** (attempt - 1)) + random.uniform(0, 1.5)
            print(f"[warn] {type(e).__name__} attempt {attempt}/{max_retries} -> sleep {sleep_for:.1f}s")
            time.sleep(sleep_for)
    raise RuntimeError(f"Failed GET {url}. Last error: {last_err}")

# --- Step A: get thread IDs from Reddit search (no auth) ---
def fetch_threads_from_reddit(max_threads=200, days_back=800, sleep_s=1.0):
    headers = {
        # Reddit will often 429 if UA is missing/too generic
        "User-Agent": "habs-gdt-scraper (no-auth) by local-script"
    }
    query = '"Game Thread:"'  # quoted phrase search

    after = None
    threads = []
    cutoff_epoch = to_epoch_days_ago(days_back)

    while len(threads) < max_threads:
        params = {
            "q": query,
            "restrict_sr": "1",
            "sort": "new",
            "t": "all",
            "limit": "100",
        }
        if after:
            params["after"] = after

        data = get_json(REDDIT_SEARCH_URL, params=params, headers=headers, timeout=60)
        children = data.get("data", {}).get("children", [])
        if not children:
            break

        for ch in children:
            post = ch.get("data", {})
            created_utc = int(post.get("created_utc", 0))
            if created_utc and created_utc < cutoff_epoch:
                # We’ve gone far enough back
                return threads[:max_threads]

            title = post.get("title", "")
            if is_game_thread_title(title):
                threads.append({
                    "id": post.get("id"),  # base36 submission id
                    "title": title,
                    "created_utc": created_utc,
                    "permalink": post.get("permalink"),
                    "author": post.get("author"),
                    "score": post.get("score"),
                    "num_comments": post.get("num_comments"),
                    "url": post.get("url"),
                })
                if len(threads) >= max_threads:
                    break

        after = data.get("data", {}).get("after")
        if not after:
            break

        time.sleep(sleep_s)

    # de-dupe by id
    seen, uniq = set(), []
    for t in threads:
        if t["id"] and t["id"] not in seen:
            seen.add(t["id"])
            uniq.append(t)
    return uniq[:max_threads]

# --- Step B: fetch comments for each thread via PullPush link_id ---
def pullpush_comments(link_id, sleep_s=0.9, max_pages=200, stall_limit=3):
    """
    Robust comment fetch:
    - stops after max_pages
    - detects pagination stalls (same 'before' / same oldest created_utc repeatedly)
    - returns what it collected so far instead of hanging forever
    """
    all_comments = []
    before = None
    last_oldest = None
    stall_count = 0

    for page in range(1, max_pages + 1):
        params = {
            "link_id": link_id,
            "size": 100,
            "sort": "desc",
            "sort_type": "created_utc",
        }
        if before is not None:
            params["before"] = before

        data = get_json(f"{PULLPUSH_BASE}/comment/", params=params, timeout=120)
        batch = data.get("data", [])
        if not batch:
            break

        # Oldest comment in this batch (since we sort desc, last item is oldest)
        oldest = batch[-1].get("created_utc")

        # If pagination doesn't move forward, we are stalled
        if oldest is None or oldest == last_oldest:
            stall_count += 1
            if stall_count >= stall_limit:
                print(f"[warn] Stalled pagination for link_id={link_id} on page {page}. Returning partial ({len(all_comments)} comments).")
                break
        else:
            stall_count = 0
            last_oldest = oldest

        all_comments.extend(batch)

        # Critical: make sure 'before' decreases; subtract 1 to avoid repeats
        before = int(oldest) - 1

        time.sleep(sleep_s)

    return all_comments


def scrape(max_threads=200, days_back=800, out_threads="habs_game_threads.jsonl", out_comments="habs_game_thread_comments.jsonl"):
    threads = fetch_threads_from_reddit(max_threads=max_threads, days_back=days_back, sleep_s=1.0)

    done = set()
    if os.path.exists(DONE_PATH):
        with open(DONE_PATH, "r", encoding="utf-8") as f:
            done = {line.strip() for line in f if line.strip()}

    with open(out_threads, "w", encoding="utf-8") as ft:
        for idx, t in enumerate(threads, start = 1):
            ft.write(json.dumps(t, ensure_ascii=False) + "\n")

    with open(out_comments, "a", encoding="utf-8") as fc, open(DONE_PATH, "a", encoding="utf-8") as fd:
        for idx, t in enumerate(tqdm(threads, desc="Threads"), start=1):
            tid = t["id"]
            title = t["title"]

            if tid in done:
                continue

            print(f"\n[{idx}/{len(threads)}] {tid} | {title[:90]}")

            try:
                comments = pullpush_comments(tid, sleep_s=0.9, max_pages=200, stall_limit=3)
            except Exception as e:
                print(f"[warn] Skipping thread {tid} due to error: {e}")
                continue

            for c in comments:
                c["thread_id"] = tid
                c["thread_title"] = title
                fc.write(json.dumps(c, ensure_ascii=False) + "\n")

            fc.flush()
            fd.write(tid + "\n")
            fd.flush()

    print(f"Saved threads  -> {out_threads} ({len(threads)})")
    print(f"Saved comments -> {out_comments}")

if __name__ == "__main__":
    scrape(max_threads=400, days_back=800)
