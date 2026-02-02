import re
from collections import defaultdict
from tqdm import tqdm
import spacy
from spacy.matcher import Matcher


CONTEXT = 2
HL_S, HL_E = "[[", "]]"
nlp = spacy.load("en_core_web_sm")


VOCAB = {
    "STATIONARY": {
        "pore size","pore diameter","porosity","mesoporous","microporous",
        "macroporous","particle size","bead size","column dimensions",
        "column length","inner diameter","stationary phase","packing material",
        "reverse phase","normal phase","sec","gpc","hilic"
    },
    "CRITICAL": {
        "critical","acceptable","allowable","specified","recommended",
        "limit","limits","range","maximum","minimum","upper","lower"
    },
    "SAMPLE": {
        "measured","observed","evaluated","obtained","ranged","varied",
        "experimental","samples"
    },
    "SOLVENT": {
        "water","methanol","ethanol","acetonitrile","thf","dmf","dmso",
        "buffer","mobile phase","eluent","solvent"
    }
}

ALL_KEYWORDS = set().union(*VOCAB.values())


matcher = Matcher(nlp.vocab)
matcher.add("MEASUREMENT", [[{"LIKE_NUM": True},{"LOWER": {"IN": ["nm","um","mm","cm"]}}]])
matcher.add("NUMERIC_RANGE", [
    [{"LIKE_NUM": True},{"TEXT": {"IN": ["-","–"]}},{"LIKE_NUM": True}],
    [{"LOWER":"between"},{"LIKE_NUM":True},{"LOWER":"and"},{"LIKE_NUM":True}]
])
matcher.add("SOLVENT_RATIO", [[{"LIKE_NUM":True},{"TEXT":{"IN":[":","/"]}},{"LIKE_NUM":True}]])


def looks_like_table(t): 
    return bool(re.search(r"\d", t)) and ("  " in t or "\t" in t)

def highlight(t):
    for k in sorted(ALL_KEYWORDS, key=len, reverse=True):
        t = re.sub(rf"\b{re.escape(k)}\b", f"{HL_S}\\g<0>{HL_E}", t, flags=re.I)
    return t

def classify(tags):
    return (
        "CONFIRMED CRITICAL RANGES" if {"CRITICAL","NUMERIC_RANGE"} <= tags else
        "USED / SAMPLE RANGES"     if {"SAMPLE","NUMERIC_RANGE"}   <= tags else
        "SOLVENT COMPOSITION"      if "SOLVENT" in tags else
        "TABLE / NUMERIC DATA"     if "TABLE"   in tags else
        "OTHER RELEVANT INFORMATION"
    )


def analyze(text):
    sents = list(nlp(text).sents)
    if not sents:
        print("\n⚠️ No sentences detected.\n")
        return {}

    hits, out = [], defaultdict(list)
    print(f"\nAnalyzing {len(sents)} sentences...\n")

    for i, s in enumerate(tqdm(sents, desc="Processing")):
        t, tl, score, tags = s.text.strip(), s.text.lower(), 0, set()

        for name, words in VOCAB.items():
            if any(w in tl for w in words):
                score += 3 if name != "SOLVENT" else 2
                tags.add(name)

        for mid,_,_ in matcher(s):
            tags.add(nlp.vocab.strings[mid])
            score += 4

        if looks_like_table(t):
            score += 3
            tags.add("TABLE")

        if score:
            hits.append((max(0,i-CONTEXT), min(len(sents),i+CONTEXT+1), score, tags))

    # merge
    merged = []
    for h in sorted(hits):
        if not merged or h[0] > merged[-1][1]:
            merged.append(list(h))
        else:
            merged[-1][1] = max(merged[-1][1], h[1])
            merged[-1][2] = max(merged[-1][2], h[2])
            merged[-1][3] |= h[3]

    for a,b,score,tags in merged:
        ctx = [highlight(sents[i].text.strip()) for i in range(a,b)]
        out[classify(tags)].append((score, ctx))

    return out


print("Paste text (Enter twice to finish):\n")
lines = []
while (l := input()):
    lines.append(l)

text = "\n".join(lines)
if not text.strip():
    print("\n⚠️ No text provided.\n")
    exit()


results = analyze(text)

for sec, items in results.items():
    print(f"\n=== {sec} ===")
    for score, ctx in items:
        print(f"\n[Score: {score}]")
        for c in ctx:
            print(" ", c)
