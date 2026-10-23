"""Tokenize Uthmani Quran text without breaking hair-space ligatures."""
import re


# U+200A HAIR SPACE is used inside some orthographic words in the bundled
# Uthmani text (for example, إسرائيل and ذلك). It is not a word boundary.
QURAN_WORD_PATTERN = re.compile(r"\S+(?:\u200a+\S+)*")


def split_quran_words(text):
    """Return complete source tokens while preserving every character."""
    return QURAN_WORD_PATTERN.findall(str(text or ""))
