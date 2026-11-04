"""Chart titles that state the finding, and trend readings for chart summaries.

Every title here is worked out from the same values the chart draws, so it stays
true when the figures are refreshed. The words are kept neutral: "rose", "fell",
"higher", "lower", never "soared", "slumped" or anything that suggests a cause.

A title rule is a function (labels, series, stretches) -> str, passed to
line_chart() or small_multiples() as finding=. labels are the long point labels
(for example "2008-09"); series is a list of (name, values) where None is a
missing year; stretches are the (start, end) runs that can be read together
(split at definition breaks the chart splits at, and stopping before forecasts).
"""

import re

# A line counts as "little changed" when the change from first to last is no
# more than this share of its whole range, or under 1% of its level.
FLAT = 0.15
# A peak or low counts when the line moves this share of its range beyond both ends.
TURN = 0.3
# A smaller move back at the end of a line still counts as its own last move when the
# line ends at least this share of its range away from its last peak or low, so a
# title never says "then rose" about a line whose latest figures fell.
TAIL = 0.15
# "back to about the 2019 level" needs the last figure within this share of that level.
NEAR = 0.05
# "in most years" means at least this share of year-to-year moves went the same way.
MOST = 0.75
# A rise after the last fall that is too small to count as a move (see legs) is still named when
# it is at least this share of the range, so a title never says "then fell" about a line that
# bottomed earlier and has risen since (audit 13 gap 6).
FOLD_RISE = 0.05
# A stretch of at least four year-to-year steps whose two ends are within this share of the
# line's range counts as little changed. "Rising in most years" must not pass over one (audit 14 judge).
FLAT_RUN = 0.04
# ...and the stretch must cover at least this share of the line's steps.
FLAT_SHARE = 0.25


def measured(vals, a=0, b=None):
    b = len(vals) if b is None else b
    return [i for i in range(a, b) if vals[i] is not None]


def turn_back(vals, pts, way, size):
    """The start of a move back at the end of a line: the latest peak (way 1) or low
    (way -1) in pts that the line's last point is at least size back from, with no
    later point beyond it. None when the line does not end that far back."""
    last = pts[-1]
    best = None
    for n, k in enumerate(pts[:-1]):
        if (vals[k] - vals[last]) * way >= size - 1e-9 and all((vals[k] - vals[j]) * way >= 0 for j in pts[n + 1:]):
            best = n
    if best is None:
        return None
    while best > 0 and (vals[pts[best - 1]] - vals[pts[best]]) * way >= 0:
        best -= 1  # back up to the top (or bottom) of that peak (or low)
    return pts[best]


def legs(vals, a=0, b=None):
    """The big rises and falls of a line between a and b, in order, as (start, end, +1 or -1).

    A move counts when the line goes at least TURN of its whole range one way
    before turning back by at least as much. Smaller wiggles are folded into the
    move around them, and a small change after the last big move is folded into it,
    so the last move ends at the last measured point, unless the line ends at least
    TAIL of its range back from that move's peak or low: then that turn back is the
    last move, however small, dated from the latest peak or low it starts from. A peak or low held for several
    years is dated by its first year (phrase() and sentence() then say how long it was held).
    Returns [] for a line with no move that large.
    """
    pts = measured(vals, a, b)
    if len(pts) < 2:
        return []
    span = max(vals[i] for i in pts) - min(vals[i] for i in pts)
    if span <= 0:
        return []
    thr = TURN * span
    f = pts[0]
    turns, way, ext = [f], 0, f
    lo = hi = f  # before the first big move, its start can be any earlier point
    for i in pts[1:]:
        v = vals[i]
        if way == 0:
            if v - vals[lo] >= thr:
                way, ext = 1, i
            elif vals[hi] - v >= thr:
                way, ext = -1, i
            lo = i if v < vals[lo] else lo
            hi = i if v > vals[hi] else hi
        elif (v - vals[ext]) * way > 0:
            ext = i
        elif (vals[ext] - v) * way >= thr:
            turns.append(ext)
            way, ext = -way, i
    if way == 0:
        return []
    back = turn_back(vals, [i for i in pts if i >= ext], way, TAIL * span)
    if back is not None:
        turns.append(back)
    turns.append(pts[-1])
    return [(s0, e0, 1 if vals[e0] > vals[s0] else -1) for s0, e0 in zip(turns, turns[1:])]


def shape(vals, a=0, b=None):
    """How a line moves between a and b: 'up', 'down', 'flat', 'peak', 'trough',
    'turns' (three or more big moves) or 'same'.

    Returns a dict with the kind, the indices of the first, last, highest and
    lowest measured points, and its big moves ("legs", see legs()), or None with
    fewer than two points.
    """
    pts = measured(vals, a, b)
    if len(pts) < 2:
        return None
    f, l = pts[0], pts[-1]
    vf, vl = vals[f], vals[l]
    hi = max(pts, key=lambda i: (vals[i], -i))
    lo = min(pts, key=lambda i: (vals[i], i))
    span = vals[hi] - vals[lo]
    out = {"f": f, "l": l, "hi": hi, "lo": lo, "most": False, "flat": True, "net": vl - vf, "legs": []}
    if span <= 0:
        out["kind"] = "same"
        return out
    net = vl - vf
    level = max(abs(vf), abs(vl), abs(vals[hi]))
    if span < 0.02 * level:  # every year within 2% of each other: no rise, fall or turn worth naming
        out["kind"] = "flat"
        return out
    flat = abs(net) <= FLAT * span or abs(net) <= 0.01 * max(abs(vf), abs(vl))
    out["flat"] = flat
    lg = legs(vals, a, b)
    out["legs"] = lg
    if len(lg) >= 3:
        out["kind"] = "turns"
    elif len(lg) == 2:
        out["kind"] = "peak" if lg[0][2] > 0 else "trough"
    elif flat:
        out["kind"] = "flat"
        out["legs"] = []
    else:
        out["kind"] = "up" if net > 0 else "down"
        steps = [vals[j] - vals[i] for i, j in zip(pts, pts[1:])]
        same = sum(1 for s in steps if s != 0 and (s > 0) == (net > 0))
        out["most"] = len(steps) >= 4 and same >= MOST * len(steps)
    return out


def held(vals, e0, b=None):
    """The last point of a peak or low held at the same value: the run of measured
    points straight after e0 with exactly its value. e0 itself when it is not held.
    So a line that was 27.1 from 2016 to 2019 is not said to have fallen after 2016."""
    b = len(vals) if b is None else b
    h = e0
    for i in range(e0 + 1, b):
        if vals[i] is None or abs(vals[i] - vals[e0]) > 1e-9:
            break
        h = i
    return h


def _until(vals, labels, s0, e0, up):
    """'rose until 2019', or 'fell in 2020' when the move took one step."""
    verb = "rose" if up else "fell"
    pts = measured(vals, s0, e0 + 1)
    return f"{verb} in {labels[e0]}" if len(pts) == 2 else f"{verb} until {labels[e0]}"


def _back(vals, labels, lg, s):
    """How far the last move took the line compared with where the move before it
    started: ' above the 2019 level', ' back to about the 2019 level' or ' back part of the way'."""
    ref = lg[-2][0]
    up = lg[-1][2] > 0
    span = vals[s["hi"]] - vals[s["lo"]]
    d = vals[lg[-1][1]] - vals[ref]
    # "about" only when the gap is small both against the line's range and against the
    # level itself, so 126 against 140 (10% lower) is not called "about the same level"
    if abs(d) <= FLAT * span and abs(d) <= NEAR * abs(vals[ref]):
        return f" back to about the {labels[ref]} level"
    if (d > 0) == up:
        return f" {'above' if up else 'below'} the {labels[ref]} level"
    return " back part of the way"


def phrase(labels, vals, a=0, b=None, short=False, upto=False):
    """A few neutral words on how a line moved, for a title: 'rose between 2008 and 2025'.
    Every big rise and fall is named in order: 'rose until 2019, fell in 2020, then rose'.
    short leaves out how far a line came back after its last turn. upto names the year
    the last move ends instead ('then rose until 2023') and never compares with an earlier
    level: used when the chart goes on past a break, so the reader is not led to compare
    figures either side of it."""
    s = shape(vals, a, b)
    if s is None:
        return ""
    f, l, hi, lo = (labels[s[k]] for k in ("f", "l", "hi", "lo"))
    k = s["kind"]
    if k == "same":
        return f"stayed the same from {f} to {l}"
    if k == "up":
        return f"rose between {f} and {l}"
    if k == "down":
        return f"fell between {f} and {l}"
    if k == "flat":
        return f"changed little between {f} and {l}"
    lg = s["legs"]
    words = []
    for n, (s0, e0, w) in enumerate(lg[:-1]):
        # a leg starts where the one before it ended, or where that peak or low stopped being held
        s0 = held(vals, s0, b) if n else s0
        words.append(_until(vals, labels, s0, e0, w > 0))
        h = held(vals, e0, b)
        if h > e0:
            words.append(f"held level until {labels[h]}")
    s0, e0, w = lg[-1]
    s0 = held(vals, s0, b) if len(lg) > 1 else s0
    last = "then rose" if w > 0 else "then fell"
    seg = measured(vals, s0, e0 + 1)
    low_i = min(seg, key=lambda i: (vals[i], i))
    span = vals[s["hi"]] - vals[s["lo"]]
    if w < 0 and not upto and low_i < e0 and vals[e0] - vals[low_i] >= FOLD_RISE * span:
        # the line fell to a low and has risen a little since: say so, rather than "fell back part of the way"
        last = f"then fell until {labels[low_i]}, then rose again by {labels[e0]}"
    elif max((vals[i] - vals[s0]) * w for i in measured(vals, s0, e0 + 1)) < TURN * (vals[s["hi"]] - vals[s["lo"]]) - 1e-9:
        # a smaller turn back at the end (see TAIL): say when, not how far
        last += f" in {labels[e0]}" if len(measured(vals, s0, e0 + 1)) == 2 else f" between {labels[s0]} and {labels[e0]}"
    elif upto:
        last += f" in {labels[e0]}" if len(measured(vals, s0, e0 + 1)) == 2 else f" until {labels[e0]}"
    elif not short:
        last += _back(vals, labels, lg, s)
    return ", ".join(words + [last])


def _inner_turn(vals, s0, e0, w, span):
    """The point inside one move (s0 to e0, direction w) where the line turned: its lowest point for a
    fall, its highest for a rise. None unless the line has moved back toward e0 by FOLD_RISE of the
    whole range, so a small wobble is not called a turn."""
    pts = measured(vals, s0 + 1, e0)
    if not pts or vals[e0] is None:
        return None
    t = min(pts, key=lambda i: (vals[i] * -w, i))
    back = (vals[e0] - vals[t]) * -w
    return t if back > 0 and back >= FOLD_RISE * span else None


def _turn_mark(vals, t, w, lo, hi):
    """'a low of ' or 'a high of ' when point t is the lowest (after a fall) or highest (after a rise)
    of the whole stretch, so an earlier, lower dip is not called the low. '' otherwise."""
    if w < 0 and vals[t] == vals[lo]:
        return "a low of "
    if w > 0 and vals[t] == vals[hi]:
        return "a high of "
    return ""


def flat_run(vals, pts):
    """The longest stretch of at least a quarter of the line's steps (measured points pts)
    whose two ends are within FLAT_RUN of the line's range, as (first, last) indices; None
    when there is none. A short flat patch in a long line does not count."""
    span = max(vals[i] for i in pts) - min(vals[i] for i in pts)
    steps = len(pts) - 1
    need = max(4, FLAT_SHARE * steps)
    best = None
    for x in range(len(pts)):
        for y in range(len(pts) - 1, x + 3, -1):
            if y - x < need:
                break
            if abs(vals[pts[y]] - vals[pts[x]]) <= FLAT_RUN * span:
                if best is None or y - x > best[1] - best[0]:
                    best = (x, y)
                break
    return None if best is None else (pts[best[0]], pts[best[1]])


def sentence(labels, vals, show, a=0, b=None, extremes=True):
    """The trend of one stretch of a line in words, with traceable numbers.

    show(i) gives the formatted figure for point i. Returns '' with no points.
    """
    pts = measured(vals, a, b)
    if not pts:
        return ""
    if len(pts) == 1:
        return f"{show(pts[0])} in {labels[pts[0]]}."
    s = shape(vals, a, b)
    f, l, hi, lo = s["f"], s["l"], s["hi"], s["lo"]
    k = s["kind"]
    said = {f, l}
    if k == "same":
        return f"{show(f)} in every year from {labels[f]} to {labels[l]}."
    if k in ("up", "down") and re.sub(r"<[^>]+>", "", show(f)) == re.sub(r"<[^>]+>", "", show(l)):
        # the figures differ, but not once rounded as shown: "fell from 2.1% to 2.1%" would be wrong
        text = f"{show(f)} in {labels[f]} and {show(l)} in {labels[l]}: little changed overall."
    elif k in ("up", "down"):
        verb, ing = ("Rose", "rising") if k == "up" else ("Fell", "falling")
        text = f"{verb} from {show(f)} in {labels[f]} to {show(l)} in {labels[l]}"
        run = flat_run(vals, pts) if s["most"] else None
        if run is not None:
            # "in most years" would pass over this stretch, so name it instead
            a0, b0 = run
            text += f", with little change from {labels[a0]} ({show(a0)}) to {labels[b0]} ({show(b0)})"
        elif s["most"]:
            text += f", {ing} in most years"
        text += "."
    elif k == "flat":
        text = f"{show(f)} in {labels[f]} and {show(l)} in {labels[l]}: little changed overall."
    else:
        lg = s["legs"]
        parts = []
        for n, (s0, e0, w) in enumerate(lg):
            verb = "rose" if w > 0 else "fell"
            if n == len(lg) - 1:
                t = _inner_turn(vals, s0, e0, w, vals[hi] - vals[lo])
                if t is None:
                    parts.append(f"then {verb} to {show(e0)} in {labels[e0]}")
                else:
                    # the line turned inside its last move and has moved back since: say so
                    parts.append(f"then {verb} to {_turn_mark(vals, t, w, lo, hi)}{show(t)} in {labels[t]}, "
                                 f"then {'rose' if w < 0 else 'fell'} again to {show(e0)} in {labels[e0]}")
            else:
                # "a high" only when no later point in the stretch passes it, so an earlier, lower peak is not read as the high
                later = [vals[i] for i in measured(vals, e0 + 1, b)]
                if not any((v - vals[e0]) * w > 0 for v in later):
                    parts.append(f"{verb} to a {'high' if w > 0 else 'low'} of {show(e0)} in {labels[e0]}")
                else:
                    parts.append(f"{verb} to {show(e0)} in {labels[e0]}")
                said.add(e0)
                h = held(vals, e0, b)
                if h > e0:
                    parts.append(f"stayed at {show(e0)} until {labels[h]}")
                    said.add(h)
        text = f"From {show(f)} in {labels[f]}, " + ", ".join(parts) + "."
        if len(lg) == 2:  # keep the familiar wording for a single turn
            w0, e0 = lg[0][2], lg[0][1]
            # "a low of" only when it is the lowest point of the stretch (or "a high of" the highest),
            # so a dip that an earlier year went below is not called the low.
            high = "high" if w0 > 0 else "low"
            top = vals[hi] if w0 > 0 else vals[lo]
            mark = f"a {high} of " if vals[e0] == top else ""
            h = held(vals, e0, b)
            hold = f"stayed at {show(e0)} until {labels[h]}, " if h > e0 else ""
            # The last move may turn inside itself (a low in 2021-22, then a small rise to the latest year):
            # name that turn, as the title does, rather than skip it.
            t = _inner_turn(vals, e0, l, lg[1][2], vals[hi] - vals[lo])
            if t is None:
                text = (f"{'Rose' if w0 > 0 else 'Fell'} from {show(f)} in {labels[f]} to {mark}{show(e0)} in {labels[e0]}, "
                        f"{hold}then {'fell' if w0 > 0 else 'rose'} to {show(l)} in {labels[l]}.")
            else:
                text = (f"{'Rose' if w0 > 0 else 'Fell'} from {show(f)} in {labels[f]} to {mark}{show(e0)} in {labels[e0]}, "
                        f"{hold}then {'fell' if w0 > 0 else 'rose'} to {_turn_mark(vals, t, lg[1][2], lo, hi)}{show(t)} in {labels[t]}, "
                        f"then {'rose' if w0 > 0 else 'fell'} again to {show(l)} in {labels[l]}.")
    if extremes and len(pts) >= 3:
        extra = []
        if hi not in said:
            extra.append(f"highest {show(hi)} ({labels[hi]})")
        if lo not in said:
            extra.append(f"lowest {show(lo)} ({labels[lo]})")
        if extra:
            text += " In between: " + " and ".join(extra) + "."
    return text


def _common(series, a, b, first):
    """The first (or last) point in [a, b) that most groups have."""
    ends = [measured(vals, a, b) for _, vals in series]
    ends = [(p[0] if first else p[-1]) for p in ends if p]
    if not ends:
        return None
    return max(set(ends), key=lambda i: (ends.count(i), -i if first else i))


def overview(labels, series, a, b, show, group_breaks=None):
    """One sentence comparing every group's first and last figure in one stretch:
    how many were higher and lower, and which moved most. For small multiples whose
    full figures are in a table beside the chart. show(si, i) formats a figure.

    group_breaks: {series index: [(index, text), ...]} definition changes that affect
    only some groups. Such a group is left out of the comparison if a break falls
    inside the stretch, and its change is then given separately, from the break on."""
    f, l = _common(series, a, b, True), _common(series, a, b, False)
    if f is None or f == l:
        return ""
    group_breaks = group_breaks or {}
    crossed = {si: max(i for i, _ in br if f < i <= l) for si, br in group_breaks.items() if any(f < i <= l for i, _ in br)}
    def shown(si, i):
        # The figure as the reader sees it, so a change that rounds away is not called a rise or fall.
        text = re.sub(r"<[^>]+>", "", show(si, i)).replace(",", "").replace("£", "")
        m = re.search(r"-?\d+(?:\.\d+)?", text)
        return float(m.group(0)) if m else series[si][1][i]
    moved = [(round(shown(si, l) - shown(si, f), 6), si) for si, (_, vals) in enumerate(series)
             if si not in crossed and vals[f] is not None and vals[l] is not None]
    if len(moved) < 2:
        return ""
    n = len(moved)
    up = [m for m in moved if m[0] > 0]
    down = [m for m in moved if m[0] < 0]
    same = [m for m in moved if m[0] == 0]

    def tally(xs, word):
        if len(xs) == n:
            return f"all {n} shown were {word}"
        return f"{len(xs)} of the {n} shown {'was' if len(xs) == 1 else 'were'} {word}"
    parts = [tally(xs, w) for xs, w in ((up, "higher"), (down, "lower"), (same, "the same when rounded")) if xs]
    if not up and not down:
        return f"Comparing {labels[f]} with {labels[l]}, every group was the same."
    text = f"Comparing {labels[f]} with {labels[l]}, " + (", ".join(parts[:-1]) + " and " + parts[-1] if len(parts) > 1 else parts[0]) + "."

    def said(ms, word):
        # Ties on the figures shown are named together, not as one "largest".
        best = max(ms) if word == "rise" else min(ms)
        tied = [m for m in ms if m[0] == best[0]]
        # Within a tie on the rounded figures, the unrounded data still have an order: put it first and say so.
        raw = {si: series[si][1][l] - series[si][1][f] for _, si in tied}
        tied.sort(key=lambda m: -abs(raw[m[1]]))
        names = [f"{series[si][0]} ({show(si, f)} to {show(si, l)})" for _, si in tied]
        if len(names) == 1:
            return f"the largest {word} was {names[0]}"
        text = f"the largest {word}s, equal on the figures shown, were " + ", ".join(names[:-1]) + " and " + names[-1]
        lead = [abs(raw[si]) for _, si in tied]
        if lead[0] > lead[1] + 1e-9:
            text += f", and before rounding {series[tied[0][1]][0]}'s {word} was the larger"
        return text
    if up and down:
        rise, fall = said(up, "rise"), said(down, "fall")
        text += f" {rise[:1].upper() + rise[1:]}; {fall}."
    elif up:
        rise = said(up, "rise")
        text += f" {rise[:1].upper() + rise[1:]}."
    else:
        fall = said(down, "fall")
        text += f" {fall[:1].upper() + fall[1:]}."
    for si, i in sorted(crossed.items()):
        reason = next(t for k, t in group_breaks[si] if k == i)
        vals = series[si][1]
        since = next((k for k in range(i, l + 1) if vals[k] is not None), None)
        text += f" {series[si][0]} is left out, because {reason}; it is compared only from {labels[i]}"
        text += f": {show(si, since)} to {show(si, l)}." if since is not None and since < l and vals[l] is not None else "."
    return text


def lower_first(text):
    return text if text[1:2].isupper() else text[:1].lower() + text[1:]


# ---------------------------------------------------------------- title rules
# Each returns a function (labels, series, stretches) -> str.
# A rule that describes how lines moved also carries .lines: a function
# (stretches) -> [(series index, a, b)] naming the lines and years it describes.
# The chart writes these beside its heading, so builder/check.py can confirm the
# heading names every big rise and fall of those lines.

def describes(rule, lines):
    rule.lines = lines
    return rule


def lines_of(rule, stretches):
    """The (series index, a, b) runs a title rule describes, or [] for other rules."""
    return list(getattr(rule, "lines", lambda st: [])(stretches))

def _stretch(stretches, which):
    if which == "last":
        return stretches[-1]
    if which == "first":
        return stretches[0]
    return stretches[0][0], stretches[-1][1]


MIN_DIP = 0.005


def smaller_moves(labels, vals, a=0, b=None, unit=None):
    """The year-on-year moves that run against the big moves a title names: small falls
    inside a rise, small rises inside a fall. Read from the same legs as phrase(), so a
    title that says 'rose until 2019' can also say which years dipped, rather than
    hiding them. Returns (label, 'fell' or 'rose') pairs in order."""
    s = shape(vals, a, b)
    if s is None or s["kind"] in ("same", "flat"):
        return []
    if s["kind"] in ("up", "down"):
        legs_ = [(s["f"], s["l"], 1 if s["kind"] == "up" else -1)]
    else:
        legs_ = s["legs"]
    out = []
    pts_all = measured(vals, a, b)
    span = max(vals[i] for i in pts_all) - min(vals[i] for i in pts_all) if pts_all else 0
    for s0, e0, w in legs_:
        pts = measured(vals, s0, e0 + 1)
        for i, j in zip(pts, pts[1:]):
            if unit:
                # a move counts only if the figures as printed (rounded to unit) differ
                moved = (round(vals[j] / unit) - round(vals[i] / unit)) * w
                if moved < 0:
                    out.append((labels[j], "fell" if vals[j] < vals[i] else "rose"))
                continue
            d = (vals[j] - vals[i]) * w
            # without a printed unit, a move under 0.5% of the line's range is not named
            if d < -MIN_DIP * span:
                out.append((labels[j], "fell" if vals[j] < vals[i] else "rose"))
    return out


def _listed(words):
    return words[0] if len(words) == 1 else ", ".join(words[:-1]) + " and " + words[-1]


def smaller_moves_text(labels, vals, a=0, b=None, subject="", unit=None):
    """'; smaller moves in primary class sizes: fell in 2007, rose in 2023', or '' when
    the line has none. Used with trend(dips=True) and pair(dips=True)."""
    found = smaller_moves(labels, vals, a, b, unit)
    if not found:
        return ""
    parts = []
    for verb in ("fell", "rose"):
        years = [y for y, k in found if k == verb]
        if years:
            parts.append(f"{verb} in {_listed(years)}")
    head = f"smaller moves in {subject}: " if subject else "smaller moves: "
    return "; " + head + ", ".join(parts)


def _unit(dips):
    """dips: True for a rule that needs no printed unit, or the unit the figures are printed in (1 for whole numbers, 0.1 for one decimal place)."""
    return None if dips is True or dips is False else dips


def trend(subject, si=0, which="last", after="", dips=False):
    """'{subject} rose between 2008 and 2025': the line's movement over one stretch.
    which: 'last' (default, the latest comparable run), 'first' or 'all'.
    When the stretch ends at a break with figures after it, the title names the year it
    ends and makes no "back to the 2019 level" comparison (see phrase(upto=)).
    after: words added at the end, such as why later years are not compared.
    dips: also name the smaller moves against the big ones (see smaller_moves_text). Give
    the printed unit (1, or 0.1) so only moves that show in the table are named."""
    def rule(labels, series, stretches):
        a, b = _stretch(stretches, which)
        vals = series[si][1]
        upto = any(st[0] == b for st in stretches) and any(v is not None for v in vals[b:])
        p = phrase(labels, vals, a, b, upto=upto)
        extra = smaller_moves_text(labels, vals, a, b, unit=_unit(dips)) if dips else ""
        return f"{subject} {p}{extra}{after}" if p else ""
    return describes(rule, lambda st: [(si, *_stretch(st, which))])


def gap(first_name, second_name, si=0, sj=1, which="all"):
    """Compares two lines year by year: 'X was higher than Y in every year from A to B'."""
    def rule(labels, series, stretches):
        a, b = _stretch(stretches, which)
        x, y = series[si][1], series[sj][1]
        shared = [i for i in range(a, b) if x[i] is not None and y[i] is not None]
        if not shared:
            return ""
        above = [i for i in shared if x[i] > y[i]]
        span = f"from {labels[shared[0]]} to {labels[shared[-1]]}"
        if len(above) == len(shared):
            return f"{first_name} was higher than {second_name} in every year {span}"
        if not above:
            return f"{first_name} was lower than {second_name} in every year {span}"
        return f"{first_name} was higher than {second_name} in {len(above)} of the {len(shared)} years {span}"
    return rule


def leader(template, which="all", skip=(), close=None, close_template=None):
    """Names the highest line. template takes {name} and {span}: 'in every year from
    A to B' when the same line is highest throughout, or 'in B' (the latest year
    with every group) when it changes. skip: group names left out, such as 'Everything else'.
    close: when the top line leads the next by less than this in the latest year, use
    close_template instead (it also takes {second} and {lsecond}) and name both, so a
    gap within survey noise is not called "the largest"."""
    def rule(labels, series, stretches):
        a, b = _stretch(stretches, which)
        shown = [(si, v) for si, (nm, v) in enumerate(series) if nm not in skip]
        tops = []
        for i in range(a, b):
            vals = [(v[i], si) for si, v in shown if v[i] is not None]
            if len(vals) == len(shown):
                tops.append((i, max(vals)[1]))
        if not tops:
            return ""
        last_i, last_top = tops[-1]
        same = len(tops) > 1 and all(t == last_top for _, t in tops)
        span = f"in every year from {labels[tops[0][0]]} to {labels[last_i]}" if same else f"in {labels[last_i]}"
        name = series[last_top][0]
        if close is not None:
            ranked = sorted(((series[si][1][last_i], si) for si, _ in shown), reverse=True)
            if ranked[0][0] - ranked[1][0] < close:
                second = series[ranked[1][1]][0]
                return close_template.format(name=name, lname=lower_first(name), second=second,
                                             lsecond=lower_first(second), span=f"in {labels[last_i]}")
        return template.format(name=name, lname=lower_first(name), span=span)
    return rule


def moves(names=None, which="last"):
    """'From A to B, the share owning outright rose most and the share with a mortgage
    fell most': the groups whose figure rose and fell most between the first and last
    year of a stretch. names maps a group's name to the words used for it."""
    def rule(labels, series, stretches):
        a, b = _stretch(stretches, which)
        f, l = _common(series, a, b, True), _common(series, a, b, False)
        if f is None or f == l:
            return ""
        ch = [(v[l] - v[f], nm) for nm, v in series if v[f] is not None and v[l] is not None]
        if len(ch) < 2:
            return ""
        say = (names or {}).get
        up, down = max(ch), min(ch)
        parts = []
        if up[0] > 0:
            parts.append(f"{say(up[1], up[1])} rose most")
        if down[0] < 0:
            parts.append(f"{say(down[1], down[1])} fell most")
        if not parts:
            return ""
        return f"From {labels[f]} to {labels[l]}, " + " and ".join(parts)
    return rule


def count(subject, noun, which="last"):
    """'{subject} was higher in 2025 than in 2008 in 9 of the 12 {noun}'."""
    def rule(labels, series, stretches):
        a, b = _stretch(stretches, which)
        f, l = _common(series, a, b, True), _common(series, a, b, False)
        if f is None or f == l:
            return ""
        ch = [v[l] - v[f] for _, v in series if v[f] is not None and v[l] is not None]
        if not ch:
            return ""
        up = sum(1 for c in ch if c > 0)
        down = sum(1 for c in ch if c < 0)
        when = f"in {labels[l]} than in {labels[f]}"
        if up == len(ch):
            return f"{subject} was higher {when} in all {len(ch)} {noun}"
        if down == len(ch):
            return f"{subject} was lower {when} in all {len(ch)} {noun}"
        if up >= down:
            return f"{subject} was higher {when} in {up} of the {len(ch)} {noun}"
        return f"{subject} was lower {when} in {down} of the {len(ch)} {noun}"
    return rule


def narrowing(what, unit_fmt, si=0, sj=1, which="all"):
    """'The gap between X and Y narrowed from 12 to 6 points between A and B': the
    difference between two lines in their first and last shared years.
    unit_fmt formats a difference, for example lambda d: f"{d:.1f} points"."""
    def rule(labels, series, stretches):
        a, b = _stretch(stretches, which)
        x, y = series[si][1], series[sj][1]
        shared = [i for i in range(a, b) if x[i] is not None and y[i] is not None]
        if len(shared) < 2:
            return ""
        f, l = shared[0], shared[-1]
        g1, g2 = abs(x[f] - y[f]), abs(x[l] - y[l])
        if (x[f] - y[f]) * (x[l] - y[l]) <= 0:
            return f"{what} closed or changed sides between {labels[f]} and {labels[l]}"
        if unit_fmt(g1) == unit_fmt(g2):
            return f"{what} was about the same in {labels[f]} and {labels[l]}, at {unit_fmt(g2)}"
        word = "narrowed" if g2 < g1 else "widened"
        return f"{what} {word} from {unit_fmt(g1)} in {labels[f]} to {unit_fmt(g2)} in {labels[l]}"
    return rule


def pair(subject_a, subject_b, si=0, sj=1, which="all", together=None, dips=False):
    """'Primary classes rose between 2008 and 2025, while secondary classes fell': two
    lines' movements over the same years, with the years named once. together: a
    template with {phrase}, used when both lines moved the same way over the same years.
    dips: also name line si's smaller moves against its big ones, after the sentence."""
    def rule(labels, series, stretches):
        a, b = _stretch(stretches, which)
        if dips:
            text = rule_base(labels, series, stretches)
            extra = smaller_moves_text(labels, series[si][1], a, b, subject=subject_a.lower(), unit=_unit(dips))
            return f"{text}{extra}" if text and extra else text
        return rule_base(labels, series, stretches)

    def rule_base(labels, series, stretches):
        a, b = _stretch(stretches, which)
        pa = phrase(labels, series[si][1], a, b, short=True)
        pb = phrase(labels, series[sj][1], a, b, short=True)
        if together and pa == pb:
            return together.format(phrase=pa)
        if not pa or not pb:
            return f"{subject_a} {pa}" if pa else ""
        sa, sb = shape(series[si][1], a, b), shape(series[sj][1], a, b)
        tail = f" between {labels[sa['f']]} and {labels[sa['l']]}"
        if (sa["f"], sa["l"]) == (sb["f"], sb["l"]) and pb.endswith(tail):
            pb = pb[: -len(tail)]
        joiner = "; " if pa.split()[0] == pb.split()[0] else ", while "
        return f"{subject_a} {pa}{joiner}{subject_b} {pb}"
    return describes(rule, lambda st: [(si, *_stretch(st, which)), (sj, *_stretch(st, which))])


def within(template, fmt_value, si=0, which="all"):
    """'Income Tax raised between 22% and 29% of receipts in every year from A to B':
    the range one line stayed within. template takes {lo}, {hi}, {first}, {last}."""
    def rule(labels, series, stretches):
        a, b = _stretch(stretches, which)
        vals = series[si][1]
        pts = measured(vals, a, b)
        if not pts:
            return ""
        lo, hi = min(vals[i] for i in pts), max(vals[i] for i in pts)
        return template.format(lo=fmt_value(lo), hi=fmt_value(hi), first=labels[pts[0]], last=labels[pts[-1]])
    return rule


def both(*rules, sep="; "):
    """Joins two findings into one title. The later ones should start in lower case."""
    def rule(labels, series, stretches):
        parts = [r(labels, series, stretches) for r in rules]
        return sep.join(p for p in parts if p)
    return describes(rule, lambda st: [x for r in rules for x in lines_of(r, st)])


def place(points, y, group=None):
    """Where year y sits among the other years: ', higher than in 7 of the other 17 years shown'
    (with ties: ', higher than in 7 of the other 17 years shown, level with 2 other years').

    points: (year, value) pairs with a value. Only years measured the same way
    (same group) are counted. Returns '' when y has no value or nothing to compare."""
    mine = dict(points).get(y)
    if mine is None:
        return ""
    others = [v for yr, v in points if yr != y and (group is None or group(yr) == group(y))]
    if not others:
        return ""
    n = len(others)
    which = "measured the same way" if group else "shown"
    higher = sum(1 for v in others if mine > v)
    lower = sum(1 for v in others if mine < v)
    level = n - higher - lower  # years with exactly the same figure: a tie is said, not left out
    if higher == n:
        return f", the highest of the {n + 1} years {which}"
    if lower == n:
        return f", the lowest of the {n + 1} years {which}"
    if higher == 0:
        if level == n:
            return f", level with every other year {which}"
        return f", not higher than in any of the other {n} years {which}, level with {level} of them"
    tie = "" if level == 0 else f", level with {level} other year{'s' if level != 1 else ''}"
    return f", higher than in {higher} of the other {n} years {which}{tie}"
