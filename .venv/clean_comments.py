import json
import re

IN_PATH = "habs_game_thread_comments.jsonl"
OUT_PATH = "habs_clean_comments.jsonl"

URL_RE = re.compile(r"https?://\S+|www\.\S+", re.I)

def clean_text(s:str) -> str:
    '''
    Removes reddit quote blocks, removes urls, collapses whitespace
    :param s: takes comment as input
    :return: cleaned text
    '''

    s = s.replace("\r\n", "\n").replace("\r", "\n")
    # remove reddit quote blocks >
    s = "\n".join(line for line in s.split("\n") if not line.lstrip().startswith(">"))
    # remove reddit urls
    s = URL_RE.sub("", s)
    # collapse whitespace
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def main(min_chars = 5, max_chars = 600):
    '''
    Opens unclean comment jsonl, cleans it and outputs a new jsonl with cleaned comments
    :param min_chars: minimum chars per comment
    :param max_chars: maximum chars per comment
    :return: output is a cleaned comment jsonl
    '''
    # track kept and skipped comments
    kept = 0
    skipped = 0
    # iterate through each line
    with open(IN_PATH, "r", encoding="utf-8") as fin, open(OUT_PATH, "w", encoding="utf-8") as fout:
        for line in fin:
            obj = json.loads(line)
            body = obj.get("body") or obj.get("body_text") or ""
            body = body.strip()

            # skip if comment deleted or removed
            if body.lower() in ("[deleted]", "[removed]"):
                skipped +=1
                continue

            # clean text
            body2 = clean_text(body)

            # if shorter than min length or longer than max length skip
            if len(body2) < min_chars or len(body2) > max_chars:
                skipped +=1
                continue
            # map for output
            out = {
                "thread_id": obj.get("thread_id"),
                "thread_title": obj.get("thread_title"),
                "created_utc": obj.get("created_utc"),
                "score": obj.get("score"),
                "body": body2,
            }
            fout.write(json.dumps(out, ensure_ascii=False) + "\n")
            kept += 1

    print(f"Skipped {skipped} comments")
    print(f"Kept {kept} comments")

if __name__ == "__main__":
    main()

