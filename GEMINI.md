# Sages - Gemini CLI context

This extension adds the Sages skills: seven teachers to talk with (Laozi, the Buddha, Confucius,
Epictetus, Marcus Aurelius, Carl Jung, Charlie Munger), a council that puts one question to several
of them, and a front door that lists them.

Gemini CLI discovers the skills in this extension's `skills/` folder by itself. Use them only when
the user asks for a teacher or the council by name, or asks who the sages are. If your version does
not list agent skills, read `skills/sages/SKILL.md` and, for a teacher, `skills/<name>/SKILL.md`.

This file is deliberately short: it is loaded into every session.
