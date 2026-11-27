# 3. Jung and Munger: quote less, keep less

Date: 2026-11-27 · Status: accepted

## Context

Carl Jung died in 1961 and Charlie Munger in 2023. Their work is in copyright: Jung's until 2032
where the term is life plus 70 years, and in the standard English Collected Works everywhere;
Munger's for decades. Both are also people whom users will ask for things a portrayal must not
give: therapy from one, investment advice from the other.

## Decision

**Jung.** Quote only from English editions published before 1931, which are in the public domain
in the United States (Collected Papers on Analytical Psychology, 1917; Psychology of the
Unconscious, 1916). Commit only the paragraph around each quoted passage, never a whole work; the
full editions are rebuilt locally to re-check them. His later ideas are paraphrased with a
Collected Works reference and never quoted. His skill forbids diagnosis, treatment and dream
dictionaries.

**Munger.** Commit only short quotations, one or two sentences each and under 600 words in all,
each with the title and URL of the public transcript it was cut from. No source text is
committed. A script re-fetches the transcripts to re-check them. His skill gives no investment
advice, predicts nothing, and knows nothing after November 2023.

**Both.** A `NOTICE` file states that these quotations remain with their rights holders, are not
covered by the MIT licence, and that the project is not affiliated with or endorsed by either
estate or any company.

## Consequences

- The most famous later lines of Jung cannot be quoted here; the portrayal gives their sense and
  names the book.
- Munger's passages depend on third-party transcript pages staying up; the re-check script
  reports when one changes.
- Adding another figure whose work is in copyright needs the same treatment and an issue first.
