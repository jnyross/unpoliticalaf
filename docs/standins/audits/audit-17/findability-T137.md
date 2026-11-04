# Findability check: class-size picker and renting figure (T137)

Gap 3 and gap 4 of goal audit 17 asked whether a phone reader can reach the renting figure and the single-year class-size picker within 40 actions of the home page.

- Commit tested: `f113d8a` (same as `main`), built with `make build` and served locally.
- Device: phone viewport, 360 × 640, using `scripts/standins.py phone` (each scroll, tap, expand or choose is one action; starting is free).
- The check was run by a worker who knows the site's layout, so these counts are a best case. Route 1 was chosen from the home page's visible cards, and the scrolls are the ones a reader would make.

## Renting figure: 1 action

1. Home page, tap "Renting" (home card). Lands on `life/housing.html#key-answer`.

The first answer box reads: "In 2024-25, 65% of households in England owned their home and 19% rented privately." The figure is on the first screen, so no scrolling is needed.

## Class-size single-year picker: 7 actions

1. Home page, tap "Class sizes" (home card). Lands on `life/schools.html#key-answer`.
2. Scroll (screen 2): "Classes of more than 30".
3. Scroll (screen 3): the "Pick a year, or compare two years of class sizes" link is visible here, and is a shortcut to the finder.
4. Scroll (screen 4): "Find or compare years" section, with the two-year compare form and a collapsed "Find one year's figure".
5. Tap "Find one year's figure" to expand it.
6. Scroll: a list of year links, 2008 to 2025, plus "Earlier years, 1971 to 2007".
7. Tap "2019". Lands on `life/2019.html#schools`.

The finder works without JavaScript because each year is a plain link.

## Result

Both are within 40 actions, so no route change is needed. The class-size picker is 7 actions in, and the renting figure is 1 action in.

Screenshots are kept in the worker's scratch area and are not committed (see `docs/standins/README.md`).
