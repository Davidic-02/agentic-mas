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

    # request -> coordinator
    o.append(card(468, 24, 244, 40, r=20, fill="#FFFFFF"))
    o.append(txt(590, 50, "user question", 13.5, INK, anchor="middle"))
    o.append(link(590, 64, 590, 92))

    o.append(solid(300, 98, 580, 92, r=11))
    o.append(txt(590, 128, "coordinator", 17, "#FFFFFF", "bold", "middle"))
    o.append(txt(590, 152, "discovers deployed agents · reads their cards",
                 12.5, "#C6DBEE", anchor="middle"))
    o.append(txt(590, 172, "profiles the task · derives the team and its order",
                 12.5, "#C6DBEE", anchor="middle"))

    # k8s api
    o.append(f'<line x1="300" y1="144" x2="212" y2="144" stroke="{PRIMARY_2}" '
             f'stroke-width="1.4" stroke-dasharray="4 3" stroke-linecap="round" '
             f'marker-end="url(#arw)"/>')
    o.append(card(28, 120, 178, 50, fill=TINT, stroke="#BFD6EA"))
    o.append(txt(117, 141, "Kubernetes API", 12.5, PRIMARY, "bold", "middle"))
    o.append(txt(117, 158, "list Services by label", 11, MUTED, anchor="middle"))

    # A2A rail
    o.append(f'<rect x="28" y="212" width="1124" height="34" rx="8" fill="{TINT}" '
             f'stroke="{BORDER}" stroke-width="1"/>')
    o.append(f'<rect x="28" y="212" width="4" height="34" rx="2" fill="{PRIMARY}"/>')
    o.append(txt(50, 234, "A2A", 13, PRIMARY, "bold"))
    o.append(txt(96, 234, "agent ↔ agent  ·  capability cards at a well-known "
                 "endpoint  ·  tasks over JSON-RPC", 12, MUTED))

    # agents
    agents = [
        ("research", "query → findings", ""),
        ("factcheck", "findings → findings", "satisfies verification"),
        ("analysis", "findings → conclusions", "satisfies computation"),
        ("compute", "findings → conclusions", "satisfies computation"),
        ("writer", "findings → report", ""),
    ]
    x, wid, gap = 34, 212, 10
    centres = []
    for i, (name, flow, sat) in enumerate(agents):
        cx = x + i * (wid + gap)
        centres.append(cx + wid / 2)
        o.append(card(cx, 272, wid, 88))
        o.append(txt(cx + wid / 2, 300, name, 14.5, PRIMARY, "bold", "middle"))
        o.append(txt(cx + wid / 2, 322, flow, 11.8, INK, anchor="middle"))
        o.append(txt(cx + wid / 2, 343, sat or "·", 11, ACCENT if sat else BORDER,
                     anchor="middle"))

    for c in centres:
        o.append(plain(c, 360, c, 392))

    # MCP rail
    o.append(f'<rect x="28" y="392" width="1124" height="34" rx="8" fill="{TINT}" '
             f'stroke="{BORDER}" stroke-width="1"/>')
    o.append(f'<rect x="28" y="392" width="4" height="34" rx="2" fill="{PRIMARY}"/>')
    o.append(txt(50, 414, "MCP", 13, PRIMARY, "bold"))
    o.append(txt(96, 414, "agent ↔ tool  ·  each agent discovers the available "
                 "tools from the server at start-up", 12, MUTED))

    # mcp server
    o.append(link(590, 426, 590, 450))
    o.append(solid(378, 456, 424, 80, r=11, grad="gAccent"))
    o.append(txt(590, 484, "MCP server", 15, "#FFFFFF", "bold", "middle"))
    o.append(txt(590, 506, "search_documents  ·  calculate", 12.2, "#DCEBF8",
                 anchor="middle"))
    o.append(txt(590, 525, "no agent imports a tool function directly", 11,
                 "#B9D4EC", anchor="middle"))
    o.append(link(590, 536, 590, 562))
    o.append(card(452, 568, 276, 38, r=19))
    o.append(txt(590, 592, "document corpus", 12.5, INK, anchor="middle"))

    # cloud-native band
    o.append(f'<rect x="28" y="632" width="1124" height="76" rx="10" fill="{TINT}" '
             f'stroke="{BORDER}" stroke-width="1"/>')
    o.append(f'<rect x="28" y="632" width="4" height="76" rx="2" fill="{PRIMARY}"/>')
    o.append(eyebrow(50, 656, "cloud-native layer", PRIMARY))
    o.append(txt(196, 656, "every agent above is an independently deployed workload",
                 12, MUTED))
    chips = [("Deployment", "one per agent role"), ("Service", "stable, balanced"),
             ("Readiness probe", "fetches the agent card"), ("Replicas", "scaled per agent"),
             ("Label", "a2a.agent/enabled")]
    cw, cg = 208, 10
    for i, (h, s) in enumerate(chips):
        cx = 50 + i * (cw + cg)
        o.append(card(cx, 666, cw, 32, r=7, fill="#FFFFFF", lift=None))
        o.append(txt(cx + cw / 2, 680, h, 11.5, PRIMARY, "bold", "middle"))
        o.append(txt(cx + cw / 2, 693, s, 10.5, MUTED, anchor="middle"))

    return svg(W, H, "\n  ".join(o))


# ==========================================================================
# Figure 2 -- same deployment, different teams
# ==========================================================================
def formation() -> str:
    W, H = 1180, 690
    o = []

    o.append(f'<rect x="28" y="24" width="1124" height="158" rx="10" fill="{TINT}" '
             f'stroke="{BORDER}" stroke-width="1"/>')
    o.append(f'<rect x="28" y="24" width="4" height="158" rx="2" fill="{PRIMARY}"/>')
    o.append(eyebrow(50, 50, "deployed in the cluster", PRIMARY))
    o.append(txt(268, 50, "identical for both tasks — four agents, discovered by label",
                 12, MUTED))

    chips = [("research", "query", "findings", None),
             ("factcheck", "findings", "findings", "verification"),
             ("analysis", "findings", "conclusions", "computation"),
             ("writer", "findings", "report", None)]
    cw, gap = 262, 14
    for i, (n, c, pr, s) in enumerate(chips):
        cx = 50 + i * (cw + gap)
        o.append(card(cx, 64, cw, 102, fill="#FFFFFF"))
        o.append(txt(cx + cw / 2, 90, n, 15, PRIMARY, "bold", "middle"))
        o.append(txt(cx + cw / 2, 112, f"consumes  {c}", 11.8, INK, anchor="middle"))
        o.append(txt(cx + cw / 2, 130, f"produces  {pr}", 11.8, INK, anchor="middle"))
        o.append(txt(cx + cw / 2, 152, f"satisfies  {s}" if s else "·",
                     11, ACCENT if s else BORDER, anchor="middle"))

    o.append(f'<line x1="590" y1="212" x2="590" y2="654" stroke="{BORDER}" '
             f'stroke-width="1" stroke-dasharray="4 5"/>')

    def panel(ox, tag, question, req, chain, unused, foot):
        q = []
        q.append(eyebrow(ox, 240, tag, PRIMARY))
        q.append(txt(ox, 268, question, 13.5, INK))
        q.append(f'<rect x="{ox}" y="286" width="492" height="36" rx="8" '
                 f'fill="{TINT}" stroke="{BORDER}" stroke-width="1"/>')
        q.append(txt(ox + 16, 309, "requirements raised", 11.8, MUTED))
        q.append(txt(ox + 168, 309, req, 12.2, PRIMARY if req != "none" else MUTED,
                     "bold"))
        # chain
        bx = ox
        for j, (nm, hl) in enumerate(chain):
            wdt = 132
            q.append(solid(bx, 352, wdt, 44, r=9,
                           grad="gAccent" if hl else "gPrimary"))
            q.append(txt(bx + wdt / 2, 379, nm, 13.5, "#FFFFFF", "bold", "middle"))
            if j < len(chain) - 1:
                q.append(link(bx + wdt + 6, 374, bx + wdt + 40, 374))
            bx += wdt + 46
        q.append(txt(bx - 34, 379, "→  report", 12.5, PRIMARY, "bold"))
        if any(h for _, h in chain):
            hx = ox + (132 + 46) * [h for _, h in chain].index(True) + 66
            q.append(txt(hx, 414, "recruited to satisfy the requirement", 10.8,
                         ACCENT, anchor="middle"))
        # unused
        q.append(txt(ox, 452, "not recruited", 11.5, MUTED))
        for k, nm in enumerate(unused):
            ux = ox + k * 150
            q.append(f'<rect x="{ux}" y="464" width="136" height="36" rx="8" '
                     f'fill="none" stroke="{BORDER}" stroke-width="1.2" '
                     f'stroke-dasharray="4 4"/>')
            q.append(txt(ux + 68, 487, nm, 12.5, MUTED, anchor="middle"))
        q.append(note(ox, 524, 492, 66, foot[0], foot[1:], PRIMARY, TINT, BORDER))
        return q

    o += panel(50, "task A", "“How many probe types does Kubernetes have?”",
               "none", [("research", False), ("writer", False)],
               ["factcheck", "analysis"],
               ["Team of 2", "Precision 1.00 against the required set",
                "{research, writer}. Two model calls, not four."])
    o += panel(632, "task B", "“How many failure modes per category on average?”",
               "computation",
               [("research", False), ("analysis", True), ("writer", False)],
               ["factcheck"],
               ["Team of 3", "Precision 1.00 against the required set",
                "{research, analysis, writer}."])

    o.append(f'<rect x="28" y="612" width="1124" height="60" rx="10" '
             f'fill="{WARN_BG}" stroke="{WARN_BD}" stroke-width="1"/>')
    o.append(txt(50, 636, "Nothing in the coordinator changed between the panels, "
                 "and nothing in the cluster changed. The team differs because the task differs.",
                 12.5, INK))
    o.append(txt(50, 656, "Under task-blind formation both panels yield "
                 "research → factcheck → analysis → writer, irrespective of need.",
                 12.5, INK))
    return svg(W, H, "\n  ".join(o))


# ==========================================================================
# Figure 3 -- withdrawal during execution
# ==========================================================================
def withdrawal() -> str:
    W, H = 1180, 600
    o = []

    o.append(eyebrow(414, 40, "fixed plan", PRIMARY))
    o.append(txt(414, 60, "computed once, then followed", 11.8, MUTED, anchor="middle"))
    o.append(eyebrow(852, 40, "re-forming", PRIMARY))
    o.append(txt(852, 60, "re-derived from what remains", 11.8, MUTED, anchor="middle"))
    o.append(plain(196, 76, 1152, 76))
    o.append(f'<line x1="634" y1="76" x2="634" y2="578" stroke="{BORDER}" '
             f'stroke-width="1" stroke-dasharray="4 5"/>')

    def chain(ox, oy, nodes):
        q, bx = [], ox
        for nm, state in nodes:
            w = 118
            if state == "live":
                q.append(solid(bx, oy, w, 40, r=9))
                q.append(txt(bx + w / 2, oy + 25, nm, 12.8, "#FFFFFF", "bold", "middle"))
            elif state == "dead":
                q.append(f'<rect x="{bx}" y="{oy}" width="{w}" height="40" rx="9" '
                         f'fill="{BAD_BG}" stroke="{BAD_FG}" stroke-width="1.3" '
                         f'stroke-dasharray="4 3"/>')
                q.append(txt(bx + w / 2, oy + 25, nm, 12.5, BAD_FG, anchor="middle"))
                q.append(cross(bx + w / 2, oy + 58))
            elif state == "alt":
                q.append(solid(bx, oy, w, 40, r=9, grad="gAccent"))
                q.append(txt(bx + w / 2, oy + 25, nm, 12.8, "#FFFFFF", "bold", "middle"))
            else:
                q.append(f'<rect x="{bx}" y="{oy}" width="{w}" height="40" rx="9" '
                         f'fill="none" stroke="{BORDER}" stroke-width="1.2" '
                         f'stroke-dasharray="4 4"/>')
                q.append(txt(bx + w / 2, oy + 25, nm, 12.5, MUTED, anchor="middle"))
            bx += w + 34
        return q, bx

    # row labels
    o.append(eyebrow(32, 136, "case 1", PRIMARY))
    for i, s in enumerate(["withdrawn agent is the", "only satisfier of a", "raised requirement"]):
        o.append(txt(32, 160 + i * 18, s, 12.3, INK))
    o.append(txt(32, 232, "deployed: research, factcheck,", 11, MUTED))
    o.append(txt(32, 247, "analysis, writer", 11, MUTED))

    c, _ = chain(210, 104, [("research", "live"), ("analysis", "dead"), ("writer", "ghost")])
    o += c
    o.append(plain(328, 124, 358, 124))
    o.append(plain(480, 124, 510, 124))
    o.append(note(210, 186, 396, 74, "aborted at analysis",
                  ["the call fails; execution stops with no answer",
                   "and no statement of what went wrong"], BAD_FG, BAD_BG, BAD_BD))

    c, _ = chain(658, 104, [("research", "live"), ("analysis", "dead")])
    o += c
    o.append(plain(776, 124, 806, 124))
    o.append(txt(940, 128, "re-form → no path exists", 12, MUTED))
    o.append(note(658, 186, 494, 74, "declined, not attempted",
                  ["“no deployed agent satisfies [computation],",
                   "which this task requires”"], WARN_FG, WARN_BG, WARN_BD))

    o.append(plain(196, 288, 1152, 288, color="#EAF0F6"))

    o.append(eyebrow(32, 346, "case 2", PRIMARY))
    for i, s in enumerate(["a second agent", "satisfies the same", "requirement"]):
        o.append(txt(32, 370 + i * 18, s, 12.3, INK))
    o.append(txt(32, 442, "deployed: as above,", 11, MUTED))
    o.append(txt(32, 457, "plus compute", 11, MUTED))

    c, _ = chain(210, 314, [("research", "live"), ("analysis", "dead"), ("writer", "ghost")])
    o += c
    o.append(plain(328, 334, 358, 334))
    o.append(plain(480, 334, 510, 334))
    o.append(note(210, 396, 396, 74, "aborted at analysis",
                  ["an agent able to do the work is running and",
                   "idle, but the plan cannot be revised to reach it"],
                  BAD_FG, BAD_BG, BAD_BD))

    c, _ = chain(658, 314, [("research", "live"), ("analysis", "dead")])
    o += c
    o.append(plain(776, 334, 806, 334))
    o.append(f'<path d="M932,330 C946,330 942,306 956,306" fill="none" '
             f'stroke="{PRIMARY_2}" stroke-width="1.6" stroke-linecap="round" '
             f'marker-end="url(#arw)"/>')
    o.append(solid(968, 286, 96, 40, r=9, grad="gAccent"))
    o.append(txt(1016, 311, "compute", 12.5, "#FFFFFF", "bold", "middle"))
    o.append(link(1064, 306, 1082, 306))
    o.append(solid(1088, 286, 64, 40, r=9))
    o.append(txt(1120, 311, "writer", 12.5, "#FFFFFF", "bold", "middle"))
    o.append(note(658, 396, 494, 74, "recovered and completed",
                  ["re-formed as compute → writer; the research step",
                   "is not repeated — formation resumes from what is held"],
                  OK_FG, OK_BG, OK_BD))

    o.append(f'<rect x="28" y="496" width="1124" height="82" rx="10" fill="{TINT}" '
             f'stroke="{BORDER}" stroke-width="1"/>')
    for i, s in enumerate([
        "Recovery depends on capability-level redundancy, not on the re-forming mechanism alone. Because task-aware formation admits an agent",
        "only when something requires it, every member of a formed team is load-bearing: the precision that makes the team efficient also leaves it",
        "without slack. Detection is immediate only for a withdrawn process; an unresponsive one would wait for a timeout."]):
        o.append(txt(50, 522 + i * 20, s, 12.3, INK))
    return svg(W, H, "\n  ".join(o))


# ==========================================================================
if __name__ == "__main__":
    jobs = [("figure_architecture", architecture(), 2360, 1460),
            ("figure_formation", formation(), 2360, 1380),
            ("figure_withdrawal", withdrawal(), 2360, 1200)]
    for name, src, pw, ph in jobs:
        (HERE / f"{name}.svg").write_text(src)
        cairosvg.svg2png(url=str(HERE / f"{name}.svg"),
                         write_to=str(HERE / f"{name}.png"),
                         output_width=pw, output_height=ph)
        print(f"  {name}.png  {pw}x{ph}")
