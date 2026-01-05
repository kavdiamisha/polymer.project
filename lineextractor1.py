print("Paste your text below. Press Enter twice to finish:")

lines = []
while True:
    line = input()
    if line == "":
        break
    lines.append(line)

text = "\n".join(lines)

stationary_keywords = [
    "pore size",
    "average pore size",
    "pore diameter",
    "porosity",
    "angstrom",
    "Å",
    "nanometer",
    "nm",
    "mesoporous",
    "microporous",
    "macroporous"
    "particle size",
    "particle diameter",
    "bead size",
    "micron",
    "µm",
    "micrometer",
    "spherical particles",
    "packing material"
    "column dimensions",
    "column size",
    "column length",
    "inner diameter",
    "ID",
    "mm",
    "cm",
    "length × diameter",
    "dimensions"
    "stationary phase",
    "column packing",
    "packing phase",
    "separation medium",
    "chromatographic phase",
    "silica",
    "polymer-based",
    "crosslinked polymer",
    "polystyrene",
    "divinylbenzene",
    "PS-DVB",
    "modified",
    "surface modification",
    "functionalized",
    "coated",
    "bonded phase",
    "end-capped"
     "single column",
    "two columns",
    "three columns",
    "column set",
    "columns connected",
    "in series",
    "tandem columns"
    "Agilent",
    "Waters",
    "Phenomenex",
    "Shimadzu",
    "Thermo Fisher",
    "Tosoh",
    "Polymer Laboratories",
    "manufacturer",
    "supplied by",
    "purchased from"
    "reverse phase",
    "reversed-phase",
    "normal phase",
    "size exclusion",
    "SEC",
    "GPC",
    "ion exchange",
    "HILIC"

]
def extract_ranked_sentences(text, stationary_keywords):
    sentences = text.split(".")
    keywords = [k.lower() for k in stationary_keywords]

    scored_sentences = []

    for sentence in sentences:
        sentence_lower = sentence.lower()
        score = sum(1 for k in keywords if k in sentence_lower)

        if score > 0:
            scored_sentences.append((score, sentence.strip()))

    # Sort by score (highest first)
    scored_sentences.sort(reverse=True)

    return [s for score, s in scored_sentences]


result = extract_ranked_sentences(text, stationary_keywords)

print("\nImportant sentences:")
for sentence in result:
    print("-", sentence)