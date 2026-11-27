# 2. A quotation ships only if a script can find it in its source

Date: 2026-11-27 · Status: accepted

## Context

Language models produce confident, plausible, wrong quotations, and the internet is full of lines
these teachers never said. A portrayal that repeats them is worse than no portrayal.

## Decision

- Source texts are committed under `sources/`, restructured with one heading per citable unit.
- Every passage must be a contiguous, whitespace-normalised substring of its source file, under
  the heading it names. Case, punctuation and quote characters must match exactly.
- A skill may put quotation marks only around a passage. A guard script enforces it.
- The portrayals are told the same thing in their ground rules, and each lists the common fakes.
- The MCP server exposes the check as a tool, `verify_quote`.

## Consequences

- Passages are cut out of the source by start and end phrase, never typed.
- Citations use the numbering of the translation quoted, which modern editions do not always
  share; a note gives the modern number only where it has been checked.
- The scripts prove that the words are in the text, not who is speaking them. That check is a
  person's: the first release shipped a line of Dr. Loÿ's as Jung's until a reviewer caught it,
  and the Jung builder now keeps only Jung's own letters.
- Translations are limited to ones that are free to redistribute, so the English is Victorian
  in places. That is the price of being checkable.
