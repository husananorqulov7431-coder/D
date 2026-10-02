import re
from typing import Dict

MAX_CHARS = 14800

SPECIAL_PRONUNCIATIONS: Dict[str, str] = {
    "mRNK": "em-er-en-ka",
    "tRNK": "te-er-en-ka",
    "rRNK": "er-er-en-ka",
    "DNK": "de-en-ka",
    "RNK": "er-en-ka",
    "ATP": "a-te-pe",
    "ADP": "a-de-pe",
    "AI": "a-i",
    "TTS": "te-te-es",
    "PDF": "pe-de-ef",
    "DOCX": "dok-eks",
    "TXT": "te-iks-te",
}

EXACT_PRONUNCIATIONS: Dict[str, str] = {
    "sitoplazma": "si-toplazma",
    "mitoxondriya": "mi-to-xondriya",
    "ribosoma": "ri-bo-so-ma",
    "eritrotsit": "e-rit-ro-tsit",
    "leykotsit": "ley-ko-tsit",
    "trombotsit": "trom-bo-tsit",
    "miokard": "mi-o-kard",
    "sinaps": "si-naps",
    "immunitet": "im-mu-ni-tet",
    "mikroorganizm": "mi-kro-or-ga-nizm",
    "fiziologiya": "fi-zi-o-lo-gi-ya",
    "farmakologiya": "far-ma-ko-lo-gi-ya",
    "patologiya": "pa-to-lo-gi-ya",
    "anatomiya": "a-na-to-mi-ya",
    "histologiya": "his-to-lo-gi-ya",
    "gipofiz": "gi-po-fiz",
    "gipotalamus": "gi-po-ta-la-mus",
    "aminokislota": "a-mi-no-kis-lo-ta",
    "antigen": "an-ti-gen",
    "antitelo": "an-ti-te-lo",
    "replikatsiya": "rep-li-ka-tsi-ya",
    "transkripsiya": "tran-skrip-si-ya",
    "translyatsiya": "trans-lya-tsi-ya",
    "xromosoma": "xro-mo-so-ma",
    "hujayra": "hu-jay-ra",
    "vakuola": "va-ku-o-la",
    "vakuala": "va-ku-a-la",
    "plastida": "plas-ti-da",
    "nefron": "nef-ron",
    "kutikula": "ku-ti-ku-la",
    "glomerulonefrit": "glo-me-ru-lo-nef-rit",
}

def normalize_text(text: str) -> str:
    text = text.replace("
", "
").replace("", "
")
    text = text.replace("‘", "ʻ").replace("’", "ʻ").replace("ʻ", "ʻ")
    text = re.sub(r"[ 	]+", " ", text)
    text = re.sub(r"
{3,}", "

", text)
    return text.strip()

def split_text(text: str, max_chars: int = MAX_CHARS) -> list[str]:
    text = normalize_text(text)
    if len(text) <= max_chars:
        return [text]

    pieces = [p.strip() for p in re.split(r"(?<=[.!?…])s+", text) if p.strip()]
    chunks: list[str] = []
    current = ""

    for piece in pieces:
        if len(piece) <= max_chars:
            candidate = piece if not current else current + "

" + piece
            if len(candidate) <= max_chars:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                current = piece
            continue

        for sentence_piece in re.split(r"(?<=[,;:])s+", piece):
            if not sentence_piece:
                continue
            if len(sentence_piece) > max_chars:
                words = sentence_piece.split()
                buf = ""
                for word in words:
                    if len(word) > max_chars:
                        if buf:
                            if current:
                                chunks.append(current)
                            current = buf
                            buf = ""
                        while len(word) > max_chars:
                            chunks.append(word[:max_chars])
                            word = word[max_chars:]
                        buf = word
                        continue
                    cand = word if not buf else buf + " " + word
                    if len(cand) <= max_chars:
                        buf = cand
                    else:
                        if current:
                            chunks.append(current)
                        current = buf
                        buf = word
                if buf:
                    cand = buf if not current else current + " " + buf
                    if len(cand) <= max_chars:
                        current = cand
                    else:
                        if current:
                            chunks.append(current)
                        current = buf
            else:
                candidate = sentence_piece if not current else current + " " + sentence_piece
                if len(candidate) <= max_chars:
                    current = candidate
                else:
                    if current:
                        chunks.append(current)
                    current = sentence_piece

    if current:
        chunks.append(current)
    return chunks

def _replace_special_tokens(text: str) -> str:
    for src, dst in sorted(SPECIAL_PRONUNCIATIONS.items(), key=lambda x: len(x[0]), reverse=True):
        text = re.sub(rf"(?<![wʻ']){re.escape(src)}(?![wʻ'])", dst, text)
    return text

def _replace_known_terms(text: str) -> str:
    for src, dst in sorted(EXACT_PRONUNCIATIONS.items(), key=lambda x: len(x[0]), reverse=True):
        pattern = rf"(?<![wʻ']){re.escape(src)}(?=(?:lar|ning|ni|ga|da|dan|ligi|lik)?(?![wʻ']))"
        text = re.sub(pattern, dst, text, flags=re.IGNORECASE)
    return text

def _pause_hyphenated_words(text: str) -> str:
    return re.sub(r"(?<=[A-Za-zʻ'])-(?=[A-Za-zʻ'])", "; ", text)

def prepare_for_tts(text: str) -> str:
    text = normalize_text(text)
    text = _replace_special_tokens(text)
    text = _replace_known_terms(text)
    text = _pause_hyphenated_words(text)
    text = re.sub(r"s*;s*", "; ", text)
    text = re.sub(r"s*:s*", ": ", text)
    text = re.sub(r"s+", " ", text)
    return text.strip()
