import json

IN_PATH = "habs_clean_comments.jsonl"
OUT_PATH = "habs_unconditional_train.txt"

def main():
    n = 0
    with open(IN_PATH, "r", encoding="utf-8") as fin, open(OUT_PATH, "w", encoding="utf-8") as fout:
        for line in fin:
            row = json.loads(line)
            text = row.get("body", "").strip()
            if not text:
                continue

            # Each line is one comment. Add a separator token between samples.
            fout.write(text.replace("\n", " ") + "\n")
            n += 1

    print(f"Built {n} training rows")

if __name__ == "__main__":
    main()
