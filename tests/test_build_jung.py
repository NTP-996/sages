"""Cutting the Jung sources: only his own letters, and only the sentence quoted."""

import build_jung

CORRESPONDENCE = """ON SOME CRUCIAL POINTS

I.

_From Dr. Loÿ._

12th January, 1913.

Loÿ writes this to Jung.

II.

_From Dr. Jung._

28th January, 1913.

Jung answers this.

_From Dr. Loÿ._

Loÿ writes again.

_From Dr. Jung._

Jung answers again.
"""


def test_only_jungs_letters_are_kept() -> None:
    kept = build_jung.jung_letters_only(CORRESPONDENCE)
    assert "Jung answers this." in kept and "Jung answers again." in kept
    assert "Loÿ writes" not in kept


def test_a_chapter_that_is_not_correspondence_is_untouched() -> None:
    essay = "THE CONCEPTION OF THE UNCONSCIOUS\n\nAn essay with no letters in it."
    assert build_jung.jung_letters_only(essay) == essay


def test_an_excerpt_is_the_sentence_and_not_the_paragraph() -> None:
    paragraph = (
        "A first sentence about something else. The term persona is really an excellent one, "
        "for persona was originally the mask which an actor wore. A third sentence follows it."
    )
    excerpt = build_jung.sentences_containing(paragraph, "persona was originally the mask")
    assert excerpt == (
        "The term persona is really an excellent one, for persona was originally the mask "
        "which an actor wore."
    )


def test_an_excerpt_spans_the_sentences_a_passage_spans() -> None:
    paragraph = "One. Two is here. Three is here too. Four."
    assert (
        build_jung.sentences_containing(paragraph, "is here. Three is")
        == "Two is here. Three is here too."
    )
