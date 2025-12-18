import json
import re

IN_PATH = "habs_clean_comments.jsonl"
OUT_PATH = "habs_action_train.jsonl"

# Keyword based tags
RULES = [
    ("GOAL_FOR",      re.compile(r"\b(goal|scores|scored|snip(e|ed)|snipe|lets go|we lead|go habs go)\b", re.I)),
    ("GOAL_AGAINST",  re.compile(r"\b(we suck|brutal|wake up|again\?|another one|against us|they score|allowed)\b", re.I)),
    ("POWERPLAY",     re.compile(r"\b(pp|power ?play)\b", re.I)),
    ("PENALTY",       re.compile(r"\b(penalty|penalized|2 minutes|hook(ing)?|trip(ping)?|slash(ing)?|interference)\b", re.I)),
    ("REFS",          re.compile(r"\b(ref|refs|officiating|zebra|that call|no call)\b", re.I)),
    ("GOALIE_SAVE",   re.compile(r"\b(save|saved|robbed|stonewall|goalie)\b", re.I)),
    ("HIT_FIGHT",     re.compile(r"\b(hit|big hit|crunch|fight|drop(ped)? the gloves)\b", re.I)),
    ("LINE_CHANGES",  re.compile(r"\b(line(s)?|pairing(s)?|bench(ing)?|scratch(ed)?)\b", re.I)),
]

def tag_comment(text: str) -> str:
    '''
    searches text for any macthes in rules and tags if found, tags with "CHATTER" if not
    :param text: comment text to be tagged
    :return: either the tag if found in RULES or "CHATTER
    '''
    for tag, rx in RULES:
        if rx.search(text):
            return tag

    return "CHATTER"

def main():
    n = 0
    with open(IN_PATH, "r", encoding="utf-8") as fin, open(OUT_PATH, "w", encoding="utf-8") as fout:
        for line in fin:
            row = json.loads(line)
            body = row["body"]
            tag = tag_comment(body)

            train = {
                "text": f"Action: {tag}\nComment: {body}\n",
            }
            fout.write(json.dumps(train, ensure_ascii=False) + "\n")
            n += 1

    print(f"Built {n} training rows")

if __name__ == "__main__":
    main()