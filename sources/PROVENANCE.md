# Provenance

One section per file under `sources/`. Each file is the text of one translation, cut down to
the translator's words and given one `## <citation>` heading per chapter, section, discourse or
verse, so that `scripts/verify_passages.py` can check every quotation in
`skills/*/passages.jsonl` against it.

Every file here was written by the script named after its teacher in `scripts/sources/`, which
downloads the edition, removes what is listed under "Removed", inserts the headings, and fails
unless every paragraph it wrote is found word for word in the download. To rebuild one:

    uv run python scripts/sources/build_laozi.py --root .

Chapter and section numbers are those of the translation itself. Where they differ from the
numbering most modern editions use, the passage's `note` says so.

## sources/laozi/legge-tao-teh-king.txt

- Title: The Tao Teh King, or The Tao and Its Characteristics
- Translator: James Legge (1815-1897)
- Published: 1891, in The Sacred Books of the East, vol. 39
- Licence basis: public domain worldwide (the translator died in 1897)
- Downloaded from: https://gutenberg.pglaf.org/cache/epub/216/pg216.txt (Project Gutenberg ebook 216, via the pglaf.org mirror)
- Retrieved: 2026-11-27
- Removed: the distributor's header, licence and title page; the PART markers; each chapter's printed number
- Inserted: one '## Chapter N' heading per chapter
- Structure: 81 chapters; Legge's verse numbers are kept
- No-words-changed check: passed
- sha256: e642ff71b1cf4659d0ae8a79e1799006f5b05d598d67e60c44fa35ea58389c51
- bytes: 59760

## sources/confucius/legge-analects.txt

- Title: Confucian Analects (the Lunyu)
- Translator: James Legge (1815-1897)
- Published: 1861, in The Chinese Classics, vol. 1; revised 1893
- Licence basis: public domain worldwide (the translator died in 1897)
- Downloaded from: https://gutenberg.pglaf.org/cache/epub/3330/pg3330.txt (Project Gutenberg ebook 3330, via the pglaf.org mirror)
- Retrieved: 2026-11-27
- Removed: the distributor's header, licence and title page; the BOOK lines; the printed chapter labels and paragraph numbers
- Inserted: one '## Analects B.C' heading per chapter, in Legge's numbering (his 15.23 is 15.24 in most modern editions)
- Structure: 20 books, 499 chapters; chapters per book [16, 24, 26, 26, 27, 28, 37, 21, 30, 18, 25, 24, 30, 47, 41, 14, 26, 11, 25, 3]
- No-words-changed check: passed
- sha256: 35fd762c75bfad005d59d69e069b5a7be8e9c1e2347b91a2bf9803c29c6608ee
- bytes: 163128

## sources/buddha/sujato-suttas.txt

- Title: Discourses of the Buddha from the Pali Canon: a selection from the Long, Middle, Linked and Numbered Discourses, the Udana and the Sutta Nipata, and the whole Dhammapada
- Translator: Bhikkhu Sujato
- Published: 2018, SuttaCentral
- Licence basis: Creative Commons Zero (CC0), https://creativecommons.org/publicdomain/zero/1.0/ - SuttaCentral's publication record states: 'It is dedicated to the public domain via Creative Commons Zero (CC0).'
- Downloaded from: https://suttacentral.net/api/bilarasuttas/<uid>/sujato?lang=en for each uid listed in scripts/sources/build_buddha.py
- Retrieved: 2026-11-27
- Removed: the Pali root text, variant readings and references; title segments; the <em> emphasis tags; the <j> verse line-join marks (replaced by a line break)
- Inserted: one heading per discourse ('## SN 56.11') and per Dhammapada verse ('## Dhp 5'); one translation segment per line
- Structure: 45 discourses and 423 Dhammapada verses
- No-words-changed check: passed
- sha256: c3ff885662545ef8442ed40b97dff8dc9db0ffc1d5be7b2dbe61495a2cc10647
- bytes: 435525

## sources/epictetus/long-enchiridion.txt

- Title: The Encheiridion, or Manual, of Epictetus
- Translator: George Long (1800-1879)
- Published: 1877
- Licence basis: public domain worldwide (the translator died in 1879)
- Retrieved: 2026-11-27
- Removed: Long's footnotes and their reference marks, page numbers, navigation
- Downloaded from: https://en.wikisource.org/w/index.php?title=The_Discourses_of_Epictetus%3B_with_the_Encheiridion_and_Fragments/The_Encheiridion_or_Manual&action=render (English Wikisource, proofread transcription)
- Inserted: one '## Enchiridion N' heading per chapter, in this translation's numbering
- Structure: 52 chapters
- No-words-changed check: passed
- sha256: ca0255bc76fd1317e86b8aad23495faa937a0ead386871b603a3629584752830
- bytes: 44018

## sources/epictetus/long-discourses.txt

- Title: The Discourses of Epictetus, as recorded by Arrian
- Translator: George Long (1800-1879)
- Published: 1877
- Licence basis: public domain worldwide (the translator died in 1879)
- Retrieved: 2026-11-27
- Removed: Long's footnotes and their reference marks, page numbers, navigation
- Downloaded from: https://en.wikisource.org/w/index.php?title=The_Discourses_of_Epictetus%3B_with_the_Encheiridion_and_Fragments/Book_<b>/Chapter_<c>&action=render for each chapter (English Wikisource, proofread transcription)
- Inserted: one '## Discourses B.C' heading per chapter; the line after it is Long's chapter title
- Structure: 4 books, 95 chapters; chapters per book [30, 26, 26, 13]
- No-words-changed check: passed
- sha256: 4b11b7e504213bbe4fc02076af5d3735771a93e556e942cdfe5c5758606e7bc4
- bytes: 649413

## sources/marcus-aurelius/long-meditations.txt

- Title: The Thoughts of the Emperor Marcus Aurelius Antoninus (the Meditations)
- Translator: George Long (1800-1879)
- Published: 1862
- Licence basis: public domain worldwide (the translator died in 1879)
- Downloaded from: https://gutenberg.pglaf.org/cache/epub/15877/pg15877.txt (Project Gutenberg ebook 15877, via the pglaf.org mirror)
- Retrieved: 2026-11-27
- Removed: the distributor's header and licence; Long's biographical sketch and essay on the philosophy of Antoninus; the indexes; footnote blocks and their [A]-style marks; each section's printed number
- Inserted: one '## Meditations B.S' heading per section, in Long's numbering
- Structure: 12 books, 487 sections; sections per book [17, 17, 16, 51, 36, 59, 75, 61, 42, 38, 39, 36]
- No-words-changed check: passed
- sha256: a53394b88d8d9c1812e7cfb1aab4a451453d451fc17b10415d178442c8d89a4c
- bytes: 257937
