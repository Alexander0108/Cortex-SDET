"""
Shared CLI rendering utilities for Cortex-SDET.

Single source of truth for terminal "box" borders. All menus across the
project (main hub, API/SQL/Data-Driven CLIs, language & provider pickers)
use these functions so the right border is always a straight vertical line
regardless of terminal/font/emoji rendering.
"""

import unicodedata


def disp_width(s):
    """
    Estimates the on-screen display width of a string.
    Wide CJK / emoji characters take 2 columns; Variation Selectors and
    ZWJ take 0; regional-indicator pairs (flags) render as one wide glyph.
    """
    w = 0
    ri_pair = False  # regional indicator pair (flag) tracking
    for ch in s:
        o = ord(ch)
        # Variation selector / ZWJ take no column space on their own
        if 0xFE00 <= o <= 0xFE0F or o == 0x200D:
            continue
        # Regional indicators (flags) — a pair renders as one wide glyph
        if 0x1F1E6 <= o <= 0x1F1FF:
            if ri_pair:
                ri_pair = False  # second half of the pair: width already counted
                continue
            ri_pair = True
            w += 2
            continue
        ri_pair = False
        # Wide CJK + common emoji blocks + a few unambiguous extras
        if (unicodedata.east_asian_width(ch) in ("W", "F")
                or 0x1F000 <= o <= 0x1FAFF
                or 0x2600 <= o <= 0x27BF
                or o == 0x2139
                or o == 0x2B50   # ⭐
                or o == 0x2728):  # ✨
            w += 2
        else:
            w += 1
    return w


def render_line(text, total=74):
    """
    Renders one content line inside the box borders, with padding computed
    from the real display width (emoji/CJK = 2 columns). Guarantees a
    straight right edge regardless of font/terminal.
    """
    pad = total - disp_width(text) - 4  # │ + space + space + │
    if pad < 0:
        pad = 0
    return "│ " + text + " " * pad + " │"


def render_box(lines, total=74):
    """
    Renders a full bordered box around the given content lines.
    Returns a single string (no trailing newline).
    """
    out = ["┌" + "─" * (total - 2) + "┐"]
    for line in lines:
        out.append(render_line(line, total))
    out.append("└" + "─" * (total - 2) + "┘")
    return "\n".join(out)
