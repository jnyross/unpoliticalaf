# Prompt: informal check

Replace the parts in capitals before starting the session.

---

You play this person: PROFILE. A friend has sent you a link to a website about
where UK public money goes and how everyday life has changed. Spend up to 40
actions looking around it on your phone, as this person would, with the
commands below. Open each screenshot with the Read tool: it is all you can see.
Do not read any file in the repository, and do not use the web.

```
python scripts/standins.py phone start  --state STATE_DIR/IN.json --shots SHOTS_DIR
python scripts/standins.py phone scroll --state STATE_DIR/IN.json down     (or up)
python scripts/standins.py phone tap    --state STATE_DIR/IN.json NUMBER
python scripts/standins.py phone choose --state STATE_DIR/IN.json NUMBER "CHOICE"
python scripts/standins.py phone back   --state STATE_DIR/IN.json
```

Try to find out three things this person might wonder about: where most public
money goes, how much of a household's income goes on tax, and how one part of
everyday life (work, pay, housing, holidays or schools) has changed since they
were young.

Then write STATE_DIR/IN-notes.md: what you found out, in this person's words,
and a list of everything that confused you, slowed you down or nearly misled
you, one sentence each, saying which page it was on. Mark any that stopped you
from finding an answer as **blocking**.
