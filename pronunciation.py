import re

MAX_CHARS = 14800

SPECIAL_PRONUNCIATIONS = {
    "mRNK": "em-er-en-ka", "tRNK": "te-er-en-ka", "rRNK": "er-er-en-ka",
    "DNK": "de-en-ka", "RNK": "er-en-ka", "ATP": "a-te-pe", "ADP": "a-de-pe",
    "AI": "a-i", "TTS": "te-te-es", "PDF": "pe-de-ef", "DOCX": "dok-eks", "TXT": "te-iks-te",
}

EXACT_PRONUNCIATIONS = {
    "sitoplazma": "si-toplazma", "mitoxondriya": "mi-to-xondriya",
    "ribosoma": "ri-bo-so-ma", "eritrotsit": "e-rit-ro-tsit", "leykotsit": "ley-ko-tsit",
    "trombotsit": "trom-bo-tsit", "miokard": "mi-o-kard", "sinaps": "si-naps",
    "immunitet": "im-mu-ni-tet", "mikroorganizm": "mi-kro-or-ga-nizm",
    "fiziologiya": "fi-zi-o-lo-gi-ya", "farmakologiya": "far-ma-ko-lo-gi-ya",
    "patologiya": "pa-to-lo-gi-ya", "anatomiya": "a-na-to-mi-ya",
    "histologiya": "his-to-lo-gi-ya", "gipofiz": "gi-po-fiz", "gipotalamus": "gi-po-ta-la-mus",
    "aminokislota": "a-mi-no-kis-lo-ta", "antigen": "an-ti-gen", "antitelo": "an-ti-te-lo",
    "replikatsiya": "rep-li-ka-tsi-ya", "transkripsiya": "tran-skrip-si-ya",
    "translyatsiya": "trans-lya-tsi-ya", "xromosoma": "xro-mo-so-ma",
    "hujayra": "hu-jay-ra", "vakuola": "va-ku-o-la", "vakuala": "va-ku-a-la",
    "plastida": "plas-ti-da", "nefron": "nef-ron", "kutikula": "ku-ti-ku-la",
    "glomerulonefrit": "glo-me-ru-lo-nef-rit",
}

def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u2018", "ʻ").replace("\u2019", "ʻ").replace("\u02BB", "ʻ").replace("`", "ʻ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def split_text(text: str, max_chars: int = MAX_CHARS) -> list[str]:
    text = normalize_text(text)
    if len(text) <= max_chars:
        return [text]
    pieces = [p.strip() for p in re.split(r"(?<=[.!?…])\s+", text) if p.strip()]
    chunks, current = [], ""
    for piece in pieces:
        candidate = piece if not current else current + "\n\n" + piece
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
        if len(piece) <= max_chars:
            current = piece
            continue
        words = piece.split(); buf = ""
        for word in words:
            candidate = word if not buf else buf + " " + word
            if len(candidate) <= max_chars:
                buf = candidate
            else:
                if buf:
                    merged = buf if not current else current + " " + buf
                    if len(merged) <= max_chars:
                        current = merged
                    else:
                        if current: chunks.append(current)
                        current = buf
                while len(word) > max_chars:
                    if current: chunks.append(current); current = ''
                    chunks.append(word[:max_chars])
                    word = word[max_chars:]
                buf = word
        if buf:
            merged = buf if not current else current + " " + buf
            if len(merged) <= max_chars:
                current = merged
            else:
                if current: chunks.append(current)
                current = buf
    if current: chunks.append(current)
    return chunks

def _replace_special_tokens(text: str) -> str:
    boundary = r"[\wʻ']"
    for src, dst in sorted(SPECIAL_PRONUNCIATIONS.items(), key=lambda x: len(x[0]), reverse=True):
        pattern = rf"(?<!{boundary}){re.escape(src)}(?!{boundary})"
        text = re.sub(pattern, dst, text)
    return text

def _replace_known_terms(text: str) -> str:
    boundary = r"[\wʻ']"
    for src, dst in sorted(EXACT_PRONUNCIATIONS.items(), key=lambda x: len(x[0]), reverse=True):
        pattern = rf"(?<!{boundary}){re.escape(src)}(?=(?:lar|ning|ni|ga|da|dan|ligi|lik)?(?!{boundary}))"
        text = re.sub(pattern, dst, text, flags=re.IGNORECASE)
    return text

def _pause_hyphenated_words(text: str) -> str:
    return re.sub(r"(?<=[A-Za-zʻ'])-(?=[A-Za-zʻ'])", "; ", text)

def prepare_for_tts(text: str) -> str:
    text = normalize_text(text)
    # Convert pauses in the original text before creating pronunciation hyphens.
    # Generated syllable hyphens must stay intact for Edge TTS.
    text = _pause_hyphenated_words(text)
    text = _replace_special_tokens(text)
    text = _replace_known_terms(text)
    text = re.sub(r"\s*;\s*", "; ", text)
    text = re.sub(r"\s*:\s*", ": ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()