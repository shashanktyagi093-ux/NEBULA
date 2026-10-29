"""Text analytics: sentiment curve, readability, keywords and entities.

Everything runs locally with small lexicons and a few robust heuristics. The
output is shaped for a graph: two series (sentiment momentum and cumulative
sentiment) plus markers for the things the reader should notice.
"""

from __future__ import annotations

import math
import re
from collections import Counter

WORD_RE = re.compile(r"[A-Za-z][A-Za-z'\u2019\-]*|\d+(?:[.,]\d+)*")
SENTENCE_RE = re.compile(r"[^.!?\n]+[.!?]*")

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "than", "so", "as",
    "of", "in", "on", "at", "to", "from", "by", "with", "without", "for",
    "about", "into", "over", "under", "above", "below", "between", "through",
    "is", "are", "was", "were", "be", "been", "being", "am", "it", "its",
    "this", "that", "these", "those", "there", "here", "when", "where",
    "who", "whom", "which", "what", "why", "how", "all", "any", "both",
    "each", "few", "more", "most", "some", "such", "no", "not", "only",
    "own", "same", "too", "very", "can", "will", "just", "should", "now",
    "i", "you", "he", "she", "we", "they", "me", "him", "her", "us", "them",
    "my", "your", "his", "their", "our", "mine", "yours", "do", "does",
    "did", "have", "has", "had", "up", "down", "out", "off", "again",
    "once", "because", "while", "until", "after", "before", "during",
    "also", "may", "might", "must", "shall", "would", "could", "not",
    "very", "really", "quite", "still", "even", "ever", "never", "always",
    "much", "many", "well", "back", "way", "thing", "things", "get", "got",
    "make", "made", "like", "one", "two", "us", "who",
}

SENTIMENT = {
    # positive
    "good": 1.0, "great": 1.2, "excellent": 1.5, "amazing": 1.6,
    "awesome": 1.5, "wonderful": 1.5, "fantastic": 1.5, "delightful": 1.3,
    "love": 1.4, "loved": 1.3, "loves": 1.3, "like": 0.7, "liked": 0.7,
    "enjoy": 1.0, "enjoyed": 1.0, "happy": 1.2, "glad": 1.0, "joy": 1.3,
    "joyful": 1.3, "calm": 0.8, "peaceful": 1.0, "beautiful": 1.2,
    "brilliant": 1.4, "perfect": 1.4, "nice": 0.8, "kind": 0.9,
    "helpful": 1.0, "help": 0.6, "helps": 0.6, "helped": 0.7,
    "success": 1.2, "successful": 1.2, "win": 1.0, "won": 1.0, "winning": 1.0,
    "improve": 1.0, "improved": 1.0, "improvement": 1.0, "better": 0.9,
    "best": 1.4, "strong": 0.9, "fast": 0.6, "easy": 0.7, "simple": 0.5,
    "clear": 0.7, "clean": 0.7, "safe": 0.9, "secure": 0.8, "useful": 1.0,
    "fun": 0.9, "funny": 0.8, "interesting": 0.9, "exciting": 1.2,
    "excited": 1.1, "hope": 0.8, "hopeful": 1.0, "optimistic": 1.1,
    "grateful": 1.2, "thankful": 1.2, "thanks": 0.8, "proud": 1.1,
    "recommend": 1.0, "recommended": 1.0, "worth": 0.6, "fresh": 0.6,
    "warm": 0.7, "bright": 0.7, "sweet": 0.8, "rich": 0.6, "healthy": 1.0,
    "recover": 0.7, "recovered": 0.8, "recovery": 0.8, "ship": 0.5,
    "shipped": 0.5, "smooth": 0.8, "reliable": 1.0, "stable": 0.8,
    # negative
    "bad": -1.0, "terrible": -1.6, "awful": -1.6, "horrible": -1.6,
    "hate": -1.4, "hated": -1.3, "dislike": -1.0, "sad": -1.2,
    "angry": -1.3, "anger": -1.3, "furious": -1.6, "upset": -1.1,
    "annoyed": -1.0, "annoying": -1.1, "frustrated": -1.2,
    "frustrating": -1.2, "disappointed": -1.3, "disappointing": -1.3,
    "fail": -1.2, "failed": -1.3, "failure": -1.3, "failing": -1.2,
    "error": -0.9, "bug": -0.8, "buggy": -1.0, "broken": -1.3,
    "crash": -1.2, "crashed": -1.2, "slow": -0.8, "confusing": -1.0,
    "difficult": -0.8, "hard": -0.6, "weak": -0.9, "poor": -1.1,
    "worst": -1.6, "worse": -1.0, "problem": -0.9, "problems": -0.9,
    "issue": -0.7, "issues": -0.7, "risk": -0.7, "danger": -1.2,
    "dangerous": -1.3, "unsafe": -1.3, "ugly": -1.1, "boring": -0.9,
    "tired": -0.7, "exhausted": -1.1, "stress": -1.0, "stressed": -1.1,
    "pain": -1.2, "painful": -1.3, "sick": -1.0, "hurt": -1.0,
    "lost": -0.9, "lose": -1.0, "loss": -1.0, "miss": -0.6,
    "cheap": -0.5, "expensive": -0.5, "waste": -1.2, "useless": -1.4,
    "unfortunately": -1.0, "sorry": -0.7, "wrong": -1.0, "doubt": -0.7,
    "afraid": -1.1, "scared": -1.2, "fear": -1.2, "lonely": -1.1,
}

NEGATORS = {
    "not", "no", "never", "neither", "nor", "cannot", "can't", "don't",
    "doesn't", "didn't", "isn't", "wasn't", "aren't", "weren't", "won't",
    "wouldn't", "shouldn't", "couldn't", "hardly", "barely", "without",
    "nothing", "none", "nobody",
}

INTENSIFIERS = {
    "very": 1.6, "really": 1.45, "extremely": 1.9, "incredibly": 1.8,
    "totally": 1.5, "absolutely": 1.8, "so": 1.35, "quite": 1.25,
    "slightly": 0.55, "somewhat": 0.7, "fairly": 0.85, "pretty": 1.1,
    "super": 1.6, "highly": 1.5, "deeply": 1.6, "truly": 1.5,
}

ENTITY_RE = re.compile(
    r"\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)"          # Multi Word Names
    r"|\b[A-Z][a-z]{2,}\b"                            # Capitalised words
    r"|\b\d{4}\b"                                     # years
    r"|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"             # dates
    r"|\bhttps?://\S+"
    r"|\b[\w.+-]+@[\w-]+\.[\w.]+\b"
    r"|[@#][A-Za-z0-9_]+"
)


def syllables(word: str) -> int:
    word = word.lower()
    groups = re.findall(r"[aeiouy]+", word)
    count = len(groups)
    if word.endswith("e") and count > 1 and not word.endswith(("le", "ee")):
        count -= 1
    return max(1, count)


def _sentiment_series(words: list[str]) -> list[float]:
    raw: list[float] = []
    for index, word in enumerate(words):
        score = SENTIMENT.get(word, 0.0)
        window = words[max(0, index - 3):index]
        if any(w in NEGATORS for w in window[-3:]) and score:
            score = -0.8 * score
        for prev in window[-2:]:
            if prev in INTENSIFIERS and score:
                score *= INTENSIFIERS[prev]
                break
        raw.append(score)
    return raw


def analyse(text: str) -> dict:
    text = (text or "").strip()
    if not text:
        raise ValueError("type some text to analyse")

    matches = list(WORD_RE.finditer(text))
    words = [m.group(0).replace("\u2019", "'") for m in matches]
    lowered = [w.lower() for w in words]
    sentences = [s.strip() for s in SENTENCE_RE.findall(text) if s.strip()]
    if not sentences:
        sentences = [text]

    raw = _sentiment_series(lowered)

    # rolling window of 3 for a smoother momentum curve
    momentum: list[float] = []
    for index in range(len(raw)):
        lo = max(0, index - 1)
        hi = min(len(raw), index + 2)
        window = [v for v in raw[lo:hi]]
        momentum.append(sum(window) / max(1, len(window)))

    cumulative: list[float] = []
    running = 0.0
    for value in raw:
        running += value
        cumulative.append(running)
    peak = max((abs(v) for v in cumulative), default=0.0) or 1.0
    cumulative = [v / peak for v in cumulative]

    # entities: keep capitalised names that are not just sentence openers
    sentence_starts = set()
    for sentence in sentences:
        first = WORD_RE.search(sentence)
        if first:
            sentence_starts.add(first.start())
    entities: list[dict] = []
    seen: set[str] = set()
    for match in ENTITY_RE.finditer(text):
        value = match.group(0).strip()
        if not value or value.lower() in STOPWORDS:
            continue
        if match.start() in sentence_starts and len(value.split()) == 1:
            continue
        if value.lower() in seen:
            continue
        seen.add(value.lower())
        position = sum(1 for m in matches if m.start() < match.start())
        entities.append({
            "label": value,
            "x": position,
            "kind": "entity",
        })

    # keywords: content words + bigrams
    content = [w for w in lowered if w not in STOPWORDS and len(w) > 2]
    counts = Counter(content)
    keywords = [
        {"word": word, "count": count}
        for word, count in counts.most_common(8)
    ]
    bigrams = Counter(
        f"{lowered[i]} {lowered[i + 1]}"
        for i in range(len(lowered) - 1)
        if lowered[i] not in STOPWORDS and lowered[i + 1] not in STOPWORDS
        and len(lowered[i]) > 2 and len(lowered[i + 1]) > 2
    )
    for phrase, count in bigrams.most_common(3):
        if count > 1:
            keywords.append({"word": phrase, "count": count})

    # readability
    word_count = len(words)
    sentence_count = max(1, len(sentences))
    syllable_count = sum(syllables(w) for w in words) or 1
    flesch = (
        206.835
        - 1.015 * (word_count / sentence_count)
        - 84.6 * (syllable_count / word_count)
    )
    grade = 0.39 * (word_count / sentence_count) + 11.8 * (
        syllable_count / word_count) - 15.59

    overall = sum(raw) / max(1, len(raw))
    verdict = (
        "positive" if overall > 0.15
        else "negative" if overall < -0.15
        else "neutral"
    )

    series = [
        {"name": "sentiment", "points": [[i, round(v, 4)] for i, v in enumerate(momentum)]},
        {"name": "cumulative", "points": [[i, round(v, 4)] for i, v in enumerate(cumulative)]},
    ]

    markers = entities[:40]
    # mark the strongest sentiment words too
    ranked = sorted(
        ((abs(v), i) for i, v in enumerate(raw) if abs(v) >= 0.9),
        reverse=True,
    )[:8]
    for _score, index in ranked:
        markers.append({
            "label": words[index],
            "x": index,
            "kind": "hot" if raw[index] > 0 else "cold",
        })

    return {
        "kind": "text",
        "series": series,
        "markers": markers,
        "tokens": words[:400],
        "readout": {
            "sentiment": round(overall, 3),
            "verdict": verdict,
            "words": word_count,
            "unique": len(set(lowered)),
            "sentences": sentence_count,
            "characters": len(text),
            "avg_word_length": round(
                sum(len(w) for w in words) / max(1, word_count), 2),
            "flesch": round(flesch, 1),
            "grade": round(max(0.0, grade), 1),
            "reading_minutes": round(word_count / 200, 2),
            "keywords": keywords,
            "entities": entities[:12],
        },
    }


if __name__ == "__main__":
    demo = ("The launch was not great, but the team recovered quickly and "
            "shipped a delightful update to Paris on Monday.")
    result = analyse(demo)
    print(result["readout"]["verdict"], result["readout"]["flesch"])
    print(result["readout"]["keywords"])
    print([m["label"] for m in result["markers"]])
