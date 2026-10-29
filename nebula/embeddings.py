"""Distributional word vectors and a 2D semantic map.

No model downloads: vectors come from PPMI co-occurrence over the built-in
corpus (plus any corpus the user pastes) reduced with truncated SVD. Words the
corpus never saw are placed by character-n-gram similarity to known words, so
the map still behaves sensibly for novel input.
"""

from __future__ import annotations

import math
import re
from functools import lru_cache

import numpy as np

from .corpus import SENTENCES

TOKEN_RE = re.compile(r"[a-z][a-z'\-]*")

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
    "also", "may", "might", "must", "shall", "would", "could",
}

DEFAULT_CORPUS = tuple(SENTENCES)


def _tokens(text: str) -> list[str]:
    words = TOKEN_RE.findall(text.lower().replace("\u2019", "'"))
    return [w for w in words if len(w) > 1 and w not in STOPWORDS]


def _normalise_rows(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


@lru_cache(maxsize=6)
def _model(corpus: tuple[str, ...], dim: int = 64) -> dict:
    """Build vocab, vectors and co-occurrence stats. Cached per corpus."""
    docs = [_tokens(sentence) for sentence in corpus]
    docs = [d for d in docs if d]

    vocab: dict[str, int] = {}
    for doc in docs:
        for word in doc:
            vocab.setdefault(word, len(vocab))
    if len(vocab) < 3:
        return {"vocab": {}, "vectors": np.zeros((0, 0)), "counts": {}}

    size = len(vocab)
    cooc = np.zeros((size, size), dtype=np.float64)
    window = 4
    for doc in docs:
        ids = [vocab[w] for w in doc]
        for i, a in enumerate(ids):
            for j in range(max(0, i - window), min(len(ids), i + window + 1)):
                if i == j:
                    continue
                cooc[a, ids[j]] += 1.0 / abs(i - j)
    cooc = (cooc + cooc.T) / 2.0

    total = cooc.sum()
    row = cooc.sum(axis=1, keepdims=True)
    col = cooc.sum(axis=0, keepdims=True)
    with np.errstate(divide="ignore", invalid="ignore"):
        pmi = np.log((cooc * total) / (row * col))
    ppmi = np.nan_to_num(np.maximum(pmi, 0.0), nan=0.0, posinf=0.0)

    k = max(2, min(dim, size - 1))
    vectors = _svd(ppmi, k)
    vectors = _normalise_rows(vectors)

    counts = {w: 0 for w in vocab}
    for doc in docs:
        for word in doc:
            counts[word] += 1

    return {
        "vocab": vocab,
        "words": sorted(vocab, key=vocab.get),
        "vectors": vectors,
        "counts": counts,
    }


def _svd(matrix: np.ndarray, k: int) -> np.ndarray:
    """Truncated SVD, using sklearn/scipy when present, numpy otherwise."""
    try:
        from sklearn.decomposition import TruncatedSVD  # type: ignore
        from scipy.sparse import csr_matrix  # type: ignore

        svd = TruncatedSVD(n_components=k, random_state=7, n_iter=7)
        return svd.fit_transform(csr_matrix(matrix))
    except Exception:
        return np.linalg.svd(matrix, full_matrices=False)[0][:, :k]


# --------------------------------------------------------------------------
# character fallback
# --------------------------------------------------------------------------


def _char_ngrams(word: str, n: int = 3) -> set[str]:
    padded = f"^{word}$"
    return {padded[i:i + n] for i in range(max(1, len(padded) - n + 1))}


def _char_similarity(a: str, b: str) -> float:
    ga, gb = _char_ngrams(a), _char_ngrams(b)
    if not ga or not gb:
        return 0.0
    return len(ga & gb) / math.sqrt(len(ga) * len(gb))


def _oov_vector(word: str, model: dict) -> tuple[np.ndarray, bool]:
    words = model["words"]
    scores = sorted(
        ((_char_similarity(word, other), other) for other in words),
        reverse=True,
    )[:8]
    scores = [(s, w) for s, w in scores if s > 0.12]
    if not scores:
        return np.zeros(model["vectors"].shape[1]), True
    total = sum(s for s, _ in scores)
    vector = np.zeros(model["vectors"].shape[1])
    for score, other in scores:
        vector += model["vectors"][model["vocab"][other]] * (score / total)
    return vector, True


def _term_vector(term: str, model: dict) -> tuple[np.ndarray, bool]:
    """Vector for a word or short phrase; flag True when out of vocabulary."""
    words = _tokens(term)
    if not words:
        return np.zeros(model["vectors"].shape[1]), True
    parts: list[np.ndarray] = []
    oov = False
    for word in words:
        if word in model["vocab"]:
            parts.append(model["vectors"][model["vocab"][word]])
        else:
            vector, _ = _oov_vector(word, model)
            parts.append(vector)
            oov = True
    vector = np.mean(parts, axis=0)
    norm = np.linalg.norm(vector)
    return (vector / norm if norm else vector), oov


def _neighbours(vector: np.ndarray, model: dict, exclude: set[str],
                top: int = 6) -> list[list]:
    matrix = model["vectors"]
    if matrix.size == 0 or not np.linalg.norm(vector):
        return []
    scores = matrix @ vector
    order = np.argsort(-scores)
    out: list[list] = []
    for index in order:
        word = model["words"][int(index)]
        if word in exclude:
            continue
        out.append([word, round(float(scores[int(index)]), 3)])
        if len(out) >= top:
            break
    return out


# --------------------------------------------------------------------------
# public API
# --------------------------------------------------------------------------


def parse_terms(text: str) -> list[str]:
    parts = re.split(r"[,;\n]+", text)
    terms = []
    for part in parts:
        cleaned = re.sub(r"^\s*(?:words?|terms?|map|plot|cluster)\s*[:\-]\s*",
                         "", part.strip(), flags=re.I)
        cleaned = cleaned.strip().strip("\"'").strip()
        if cleaned:
            terms.append(cleaned[:48])
    return terms


def build_map(text: str, extra_corpus: str = "") -> dict:
    terms = parse_terms(text)
    if not terms:
        raise ValueError("type a few words separated by commas")

    corpus = DEFAULT_CORPUS
    if extra_corpus.strip():
        extra = tuple(
            line.strip() for line in re.split(r"[\n.!?]+", extra_corpus)
            if line.strip()
        )
        corpus = DEFAULT_CORPUS + extra

    model = _model(corpus)
    if not model["vocab"]:
        raise ValueError("the corpus is too small to build a map")

    vectors = []
    points = []
    oov_flags = []
    neighbour_map = {}
    for term in terms:
        vector, oov = _term_vector(term, model)
        vectors.append(vector)
        oov_flags.append(oov)
        neighbour_map[term] = _neighbours(vector, model, {term.lower()})

    matrix = np.vstack(vectors)
    coords, basis = _project_2d(matrix)

    for index, term in enumerate(terms):
        points.append({
            "label": term,
            "x": round(float(coords[index, 0]), 3),
            "y": round(float(coords[index, 1]), 3),
            "oov": oov_flags[index],
            "kind": "term",
            "neighbours": neighbour_map[term],
        })

    # faint context points: nearest corpus neighbours of each term
    context = []
    seen = {t.lower() for t in terms}
    for term in terms:
        for word, _score in neighbour_map[term][:3]:
            if word in seen:
                continue
            seen.add(word)
            vector = model["vectors"][model["vocab"][word]]
            xy = basis(vector)
            context.append({
                "label": word,
                "x": round(float(xy[0]), 3),
                "y": round(float(xy[1]), 3),
                "kind": "context",
            })

    return {
        "kind": "embed",
        "points": points,
        "context": context,
        "terms": len(terms),
        "vocabulary": len(model["vocab"]),
        "method": "PPMI co-occurrence + SVD",
    }


def _project_2d(matrix: np.ndarray):
    """Centre, PCA to 2 components, scale to roughly [-9, 9], jitter ties."""
    n = matrix.shape[0]
    if n == 0:
        return np.zeros((0, 2)), lambda v: (0.0, 0.0)

    if n == 1:
        coords = np.zeros((1, 2))
        basis = lambda v: (0.0, 0.0)  # noqa: E731
        return coords, basis

    centred = matrix - matrix.mean(axis=0, keepdims=True)
    u, s, vt = np.linalg.svd(centred, full_matrices=False)
    coords = u[:, :2] * s[:2]

    if coords.shape[1] < 2:  # degenerate (all vectors identical)
        coords = np.pad(coords, ((0, 0), (0, 2 - coords.shape[1])))

    # deterministic jitter so identical words don't hide each other
    if np.allclose(coords.std(axis=0), 0) or len(np.unique(coords.round(4), axis=0)) < n:
        rng = np.random.default_rng(11)
        coords = coords + rng.normal(0, 1e-4, coords.shape)
        radii = np.linspace(2.5, 8.0, n)
        angles = np.linspace(0, 2 * math.pi, n, endpoint=False)
        if np.allclose(coords.std(axis=0), 0):
            coords = np.column_stack([np.cos(angles), np.sin(angles)]) * radii[:, None]

    scale = max(float(np.abs(coords).max()), 1e-6)
    coords = coords / scale * 8.0

    # basis for projecting context words into the same space
    components = vt[:2].T if vt.shape[0] >= 2 else np.pad(vt.T, ((0, 0), (0, 2 - vt.shape[1])))
    mean = matrix.mean(axis=0, keepdims=True)

    def basis(vector: np.ndarray) -> tuple[float, float]:
        local = np.asarray(vector).reshape(1, -1) - mean
        xy = local @ components
        return (float(xy[0, 0]) / scale * 8.0, float(xy[0, 1]) / scale * 8.0)

    return coords, basis


if __name__ == "__main__":
    result = build_map("ocean, mountain, river, joy, anger, computer, software, bread")
    for point in result["points"]:
        print(f"{point['label']:<12} ({point['x']:6.2f}, {point['y']:6.2f})  oov={point['oov']}")
