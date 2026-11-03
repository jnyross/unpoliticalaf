# Prompt: new question writer

---

You are writing a comprehension test for a website that explains UK public
money and everyday life to people who do not follow politics. You have not
seen the website and must not look at it, at the repository or at the existing
test questions. Work only from the project goal below and your own knowledge of
official UK statistics.

PROJECT GOAL TEXT (paste the goal from the project, unchanged)

Write 24 multiple-choice questions a newcomer should be able to answer after
using a site that meets this goal:

- At least 3 on each of: where public money goes; which taxes raise it; who
  pays; household income and tax; and the five everyday-life topics together
  (work, earnings, housing, holidays, schools).
- At least 6 test understanding rather than finding a number: the difference
  between household averages, personal tax rates and shares of revenue;
  illustrations versus measured figures; change versus cause; missing years and
  breaks in a series; cash versus after inflation.
- Each has four options (A to D) and exactly one right answer according to
  official UK statistics. Avoid questions whose answer depends on a figure
  changing in the latest release; prefer stable facts and concepts.
- Plain English, under 30 words per question.

Write them as JSON in this shape and save it at OUTPUT_PATH (outside the
repository):

```json
{"title": "New questions AUDIT", "questions": [
  {"id": 1, "topic": "...", "question": "...",
   "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
   "answer": "A", "critical": false, "why": "one sentence"}
]}
```
