"""Draw the chapter's three figures."""

import pathlib
import cairosvg
from style import (ACCENT, BAD_BD, BAD_BG, BAD_FG, BORDER, INK, MUTED, OK_BD,
                   OK_BG, OK_FG, PRIMARY, PRIMARY_2, TINT, WARN_BD, WARN_BG,
                   WARN_FG, card, cross, eyebrow, link, note, plain, solid,
                   svg, txt)

HERE = pathlib.Path(__file__).parent


# ==========================================================================
# Figure 1 -- system architecture
# ==========================================================================
def architecture() -> str:
    W, H = 1180, 730
    o = []

    o.append(eyebrow(50, 44, "task-aware runtime formation", PRIMARY))
    o.append(txt(298, 44, "workflow from task text to execution or explicit decline",
                 12, MUTED))

    steps = [
        ("task text", ["natural-language query", "arrives at coordinator"], "gPrimary"),
        ("requirement profiling", ["keyword profiler maps", "task to markers R"], "gAccent"),
        ("capability discovery", ["list deployed agents", "and read A2A cards"], "gPrimary"),
        ("candidate-team search", ["minimum-cardinality set", "covering goal and R"], "gAccent"),
        ("ordering", ["prefer refiners before", "transformers for stability"], "gPrimary"),
        ("decision", ["execute formed team", "or report missing capability"], "gAccent"),
    ]

    x0, y0, w, h, gap = 34, 92, 172, 94, 14
    mids = []
    for i, (title, lines, grad) in enumerate(steps):
        x = x0 + i * (w + gap)
        mids.append((x + w / 2, y0 + h / 2))
        o.append(solid(x, y0, w, h, r=10, grad=grad))
        o.append(txt(x + w / 2, y0 + 30, title, 12.7, "#FFFFFF", "bold", "middle"))
        o.append(txt(x + w / 2, y0 + 53, lines[0], 11, "#DCEBF8", anchor="middle"))
        o.append(txt(x + w / 2, y0 + 72, lines[1], 11, "#DCEBF8", anchor="middle"))
        if i < len(steps) - 1:
            o.append(link(x + w + 4, y0 + h / 2, x + w + gap - 4, y0 + h / 2))

    o.append(note(34, 224, 1118, 72, "optimisation target",
                  ["T* = arg min_T |T|  subject to  goal ∈ A(T)  and  R ⊆ ⋃_{a ∈ T} S_a",
                   "A task is attempted only when both reachability and requirement coverage hold."],
                  PRIMARY, TINT, BORDER))

    o.append(f'<rect x="34" y="324" width="1118" height="154" rx="10" fill="{TINT}" '
             f'stroke="{BORDER}" stroke-width="1"/>')
    o.append(eyebrow(56, 350, "comparison baseline", PRIMARY))
    rows = [
        ("static composition", "team hardcoded in source", "requires edits when deployment changes", BAD_FG),
        ("task-blind formation", "team from eligibility only", "recruits unnecessary agents", WARN_FG),
        ("task-aware formation", "team from need plus marker coverage", "reports impossibility explicitly", OK_FG),
    ]
    for i, (name, a, b, c) in enumerate(rows):
        y = 378 + i * 30
        o.append(txt(56, y, name, 11.8, PRIMARY, "bold"))
        o.append(txt(268, y, a, 11.5, INK))
        o.append(txt(652, y, b, 11.5, c))

    o.append(f'<rect x="34" y="506" width="1118" height="192" rx="10" fill="{WARN_BG}" '
             f'stroke="{WARN_BD}" stroke-width="1"/>')
    o.append(eyebrow(56, 532, "failure handling in execution", PRIMARY))
    life = [
        ("discovery", 76), ("execution", 236), ("withdrawal / timeout detection", 396),
        ("re-formation", 646), ("recover or decline", 806),
    ]
    for i, (name, x) in enumerate(life):
        o.append(card(x, 548, 138 if i != 2 else 226, 48, r=9, fill="#FFFFFF"))
        o.append(txt(x + (69 if i != 2 else 113), 577, name, 11.5, PRIMARY, "bold", "middle"))
        if i < len(life) - 1:
            x2 = life[i + 1][1]
            o.append(link(x + (138 if i != 2 else 226) + 6, 572, x2 - 6, 572))
    o.append(txt(56, 624, "withdrawn process: immediate refusal; stalled process: detected at caller timeout",
                 11.5, INK))
    o.append(txt(56, 646, "re-formation resumes from produced material, then either recovers with redundancy or declines with requirement named",
                 11.5, INK))

    return svg(W, H, "\n  ".join(o))


# ==========================================================================
# Figure 2 -- same deployment, different teams
# ==========================================================================
def formation() -> str:
    W, H = 1180, 690
    o = []

    o.append(eyebrow(50, 40, "three composition strategies, one deployment", PRIMARY))
    o.append(txt(360, 40, "research · factcheck · analysis · writer available in all cases",
                 12, MUTED))

    def column(x, title, subtitle, rows, verdict, tone):
        fg, bg, bd = tone
        q = []
        q.append(solid(x, 66, 340, 54, r=10, grad="gPrimary"))
        q.append(txt(x + 170, 96, title, 14, "#FFFFFF", "bold", "middle"))
        q.append(txt(x + 170, 116, subtitle, 10.8, "#DCEBF8", anchor="middle"))
        q.append(card(x, 140, 340, 354))
        for i, (k, v) in enumerate(rows):
            y = 172 + i * 54
            q.append(txt(x + 16, y, k, 11.6, MUTED))
            q.append(txt(x + 16, y + 22, v, 12.2, INK))
            if i < len(rows) - 1:
                q.append(plain(x + 16, y + 34, x + 324, y + 34, color="#EAF0F6", width=1))
        q.append(note(x, 512, 340, 86, verdict[0], verdict[1:], fg, bg, bd))
        return q

    static_rows = [
        ("decision basis", "team fixed in source"),
        ("with analysis withdrawn", "fails at analysis call after earlier steps ran"),
        ("extra deployed agent", "ignored until code is edited"),
        ("source edits across scenarios", "42"),
        ("typical team", "research → analysis → writer"),
    ]
    blind_rows = [
        ("decision basis", "all currently eligible agents"),
        ("with analysis withdrawn", "may still report completion with inadequate team"),
        ("extra deployed agent", "included whether needed or not"),
        ("source edits across scenarios", "0"),
        ("typical team", "research → factcheck → analysis → writer"),
    ]
    aware_rows = [
        ("decision basis", "minimum team satisfying goal + R"),
        ("with analysis withdrawn", "declines computation tasks, names missing capability"),
        ("extra deployed agent", "used only when task requires its marker"),
        ("source edits across scenarios", "0"),
        ("typical team", "task-dependent (2.36 mean agents)"),
    ]

    o += column(50, "static composition", "author-defined team", static_rows,
                ["deployment-coupled", "correctness depends on keeping source",
                 "synchronised with cluster changes"], (BAD_FG, BAD_BG, BAD_BD))
    o += column(420, "task-blind formation", "eligibility without task context", blind_rows,
                ["adaptive but inefficient", "recruits unnecessary members and can",
                 "mask impossible tasks"], (WARN_FG, WARN_BG, WARN_BD))
    o += column(790, "task-aware formation", "profiles requirements before selecting", aware_rows,
                ["graceful impossibility reporting", "fails closed when required capability is absent,",
                 "rather than reporting a false success"], (OK_FG, OK_BG, OK_BD))

    o.append(f'<rect x="28" y="618" width="1124" height="52" rx="10" fill="{TINT}" '
             f'stroke="{BORDER}" stroke-width="1"/>')
    o.append(txt(50, 648, "Only the task-aware strategy combines zero source edits with selective teams and explicit declines when requirements cannot be met.",
                 12.2, INK))
    return svg(W, H, "\n  ".join(o))


# ==========================================================================
# Figure 3 -- withdrawal during execution
# ==========================================================================
def withdrawal() -> str:
    W, H = 1180, 600
    o = []

    o.append(eyebrow(50, 42, "execution lifecycle with failure handling", PRIMARY))
    o.append(txt(356, 42, "shared path for withdrawal and stalled-agent failures",
                 12, MUTED))

    o.append(solid(70, 90, 180, 54, r=10))
    o.append(txt(160, 121, "discover agents", 13, "#FFFFFF", "bold", "middle"))
    o.append(link(256, 117, 326, 117))
    o.append(solid(332, 90, 180, 54, r=10))
    o.append(txt(422, 121, "form + order team", 13, "#FFFFFF", "bold", "middle"))
    o.append(link(518, 117, 588, 117))
    o.append(solid(594, 90, 180, 54, r=10))
    o.append(txt(684, 121, "execute steps", 13, "#FFFFFF", "bold", "middle"))

    o.append(f'<rect x="828" y="90" width="282" height="54" rx="10" fill="{WARN_BG}" '
             f'stroke="{WARN_BD}" stroke-width="1"/>')
    o.append(txt(969, 111, "monitor for interruption", 12.5, WARN_FG, "bold", "middle"))
    o.append(txt(969, 129, "withdrawal or timeout", 11.5, WARN_FG, anchor="middle"))
    o.append(link(780, 117, 822, 117))

    # failure split
    o.append(f'<line x1="969" y1="144" x2="969" y2="190" stroke="{BORDER}" stroke-width="1.4" '
             f'stroke-dasharray="4 4"/>')
    o.append(card(650, 198, 254, 84, fill="#FFFFFF"))
    o.append(txt(777, 226, "withdrawn process", 12.5, PRIMARY, "bold", "middle"))
    o.append(txt(777, 248, "connection refused immediately", 11.2, INK, anchor="middle"))
    o.append(txt(777, 267, "detected in &lt; 0.01 s", 11.2, OK_FG, "bold", "middle"))

    o.append(card(936, 198, 174, 84, fill="#FFFFFF"))
    o.append(txt(1023, 226, "stalled process", 12.5, PRIMARY, "bold", "middle"))
    o.append(txt(1023, 248, "still reachable", 11.2, INK, anchor="middle"))
    o.append(txt(1023, 267, "detected at timeout", 11.2, WARN_FG, "bold", "middle"))

    o.append(f'<path d="M777,282 C777,314 690,320 690,346" fill="none" '
             f'stroke="{PRIMARY}" stroke-width="1.6" marker-end="url(#arw)"/>')
    o.append(f'<path d="M1023,282 C1023,314 870,320 870,346" fill="none" '
             f'stroke="{PRIMARY}" stroke-width="1.6" marker-end="url(#arw)"/>')

    o.append(solid(602, 352, 356, 56, r=10, grad="gAccent"))
    o.append(txt(780, 385, "re-discover and re-form from produced state", 13, "#FFFFFF",
                 "bold", "middle"))

    o.append(link(780, 414, 780, 452))
    o.append(card(434, 458, 332, 84, fill=OK_BG, stroke=OK_BD))
    o.append(txt(600, 486, "recovery path", 12.5, OK_FG, "bold", "middle"))
    o.append(txt(600, 508, "alternative capability available", 11.5, INK, anchor="middle"))
    o.append(txt(600, 527, "resume chain and complete", 11.5, INK, anchor="middle"))

    o.append(card(794, 458, 332, 84, fill=WARN_BG, stroke=WARN_BD))
    o.append(txt(960, 486, "decline path", 12.5, WARN_FG, "bold", "middle"))
    o.append(txt(960, 508, "no alternative satisfies requirement", 11.5, INK, anchor="middle"))
    o.append(txt(960, 527, "return explicit impossibility", 11.5, INK, anchor="middle"))

    o.append(f'<line x1="780" y1="452" x2="600" y2="452" stroke="{PRIMARY}" stroke-width="1.4" marker-end="url(#arw)"/>')
    o.append(f'<line x1="780" y1="452" x2="960" y2="452" stroke="{PRIMARY}" stroke-width="1.4" marker-end="url(#arw)"/>')
    return svg(W, H, "\n  ".join(o))


# ==========================================================================
# Figure 4 -- two ways an agent fails
# ==========================================================================
def failure_modes() -> str:
    W, H = 1180, 560
    o = []

    o.append(f'<line x1="590" y1="30" x2="590" y2="472" stroke="{BORDER}" '
             f'stroke-width="1" stroke-dasharray="4 5"/>')

    def column(ox, title, sub, agent_fill, agent_stroke, agent_label, rows, verdict):
        q = []
        q.append(eyebrow(ox, 48, title, PRIMARY))
        q.append(txt(ox, 70, sub, 12, MUTED))

        # the agent
        q.append(f'<rect x="{ox}" y="92" width="196" height="52" rx="9" '
                 f'fill="{agent_fill}" stroke="{agent_stroke}" stroke-width="1.4" '
                 f'stroke-dasharray="4 3"/>')
        q.append(txt(ox + 98, 117, "analysis", 13.5, agent_stroke, "bold", "middle"))
        q.append(txt(ox + 98, 135, agent_label, 10.8, agent_stroke, anchor="middle"))

        # signal rows
        for i, (label, value, tone) in enumerate(rows):
            y = 180 + i * 52
            fg, bg, bd = tone
            q.append(f'<rect x="{ox}" y="{y}" width="492" height="42" rx="8" '
                     f'fill="{bg}" stroke="{bd}" stroke-width="1"/>')
            q.append(txt(ox + 16, y + 26, label, 12.2, INK))
            q.append(txt(ox + 476, y + 26, value, 12.2, fg, "bold", anchor="end"))

        q.append(f'<rect x="{ox}" y="392" width="492" height="56" rx="8" '
                 f'fill="{TINT}" stroke="{BORDER}" stroke-width="1"/>')
        q.append(txt(ox + 16, 416, verdict[0], 12.4, PRIMARY, "bold"))
        q.append(txt(ox + 16, 436, verdict[1], 11.8, INK))
        return q

    neutral = (MUTED, "#FFFFFF", BORDER)
    o += column(
        50, "process withdrawn", "the container is killed",
        BAD_BG, BAD_FG, "process gone",
        [("TCP connection", "refused", (BAD_FG, BAD_BG, BAD_BD)),
         ("Readiness probe (fetches the card)", "fails", (BAD_FG, BAD_BG, BAD_BD)),
         ("Kubernetes response", "pod removed from service", (OK_FG, OK_BG, OK_BD)),
         ("Detected after", "< 0.01 s".replace(chr(60), "&lt;"), (OK_FG, OK_BG, OK_BD))],
        ("The failure is visible to the platform.",
         "Every signal agrees, and the caller learns immediately."))
    o.append(cross(148, 160))

    o += column(
        632, "process unresponsive", "the container runs but stops progressing",
        WARN_BG, WARN_FG, "alive, not progressing",
        [("TCP connection", "accepted", (OK_FG, OK_BG, OK_BD)),
         ("Readiness probe (fetches the card)", "passes", (BAD_FG, BAD_BG, BAD_BD)),
         ("Kubernetes response", "pod kept in service", (BAD_FG, BAD_BG, BAD_BD)),
         ("Detected after", "the caller's timeout", (WARN_FG, WARN_BG, WARN_BD))],
        ("The failure is invisible to the platform.",
         "Discovery returns it, formation selects it, no work is done."))

    o.append(f'<rect x="28" y="472" width="1124" height="68" rx="10" '
             f'fill="{WARN_BG}" stroke="{WARN_BD}" stroke-width="1"/>')
    for i, s in enumerate([
        "A probe that fetches an agent's capability card asks whether the agent can describe itself, not whether it is doing any work. In the",
        "right-hand column every health signal available to the system reports normality throughout. Detection is not a property the system",
        "has; it is a timeout the caller chose, and until it expires the stalled agent remains a candidate for selection."]):
        o.append(txt(50, 498 + i * 19, s, 12.2, INK))
    return svg(W, H, "\n  ".join(o))


# ==========================================================================
if __name__ == "__main__":
    jobs = [("figure_architecture", architecture(), 2360, 1460),
            ("figure_formation", formation(), 2360, 1380),
            ("figure_withdrawal", withdrawal(), 2360, 1200),
            ("figure_failure_modes", failure_modes(), 2360, 1120)]
    for name, src, pw, ph in jobs:
        (HERE / f"{name}.svg").write_text(src)
        cairosvg.svg2png(url=str(HERE / f"{name}.svg"),
                         write_to=str(HERE / f"{name}.png"),
                         output_width=pw, output_height=ph)
        print(f"  {name}.png  {pw}x{ph}")
