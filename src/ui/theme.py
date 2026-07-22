"""SpeakStory Matte Brown Theme — design tokens and style helpers.

All UI components reference this module for consistent styling.
"""
from __future__ import annotations


# ── Colour Palette ──────────────────────────────────────────────────────────
BG_DARKEST  = "#1A1410"   # App background, deepest layer
BG_DARK     = "#2A2018"   # Sidebar, panels
BG_MEDIUM   = "#3D3028"   # Cards, note containers
BG_LIGHT    = "#4F4038"   # Hover states, elevated surfaces
BG_LIGHTER  = "#5F5048"   # Active / pressed states

ACCENT        = "#C4956A"   # Primary buttons, active highlights
ACCENT_HOVER  = "#D4A57A"   # Button hover
ACCENT_DARK   = "#A47A50"   # Pressed / toggled state
ACCENT_SUBTLE = "#3D3228"   # Accent at very low opacity for bg tints

TEXT_PRIMARY   = "#F0E6DC"   # Main body text
TEXT_SECONDARY = "#A89888"   # Labels, timestamps, secondary info
TEXT_MUTED     = "#7A6A5A"   # Placeholders, disabled text

SUCCESS  = "#6AAF6A"   # Recording active, success
DANGER   = "#C46A6A"   # Delete, errors
WARNING  = "#D4A54A"   # Warnings, caution

BORDER       = "#4A3A2A"   # Subtle borders between sections
BORDER_LIGHT = "#5A4A3A"   # Lighter border for elevated elements

# ── Typography ──────────────────────────────────────────────────────────────
FONT_FAMILY = "Segoe UI"

FONT_TITLE   = (FONT_FAMILY, 26, "bold")    # Note title in editor
FONT_HEADING = (FONT_FAMILY, 16, "bold")    # App title / section heads
FONT_BODY    = (FONT_FAMILY, 14)            # Regular body text
FONT_BODY_BOLD = (FONT_FAMILY, 14, "bold")  # Emphasized body
FONT_SMALL   = (FONT_FAMILY, 12)            # Note card preview, tags
FONT_TINY    = (FONT_FAMILY, 10)            # Timestamps, counters
FONT_ICON    = (FONT_FAMILY, 22)            # Emoji / icon buttons
FONT_ICON_LG = (FONT_FAMILY, 28)           # Large mic button icon

# ── Spacing ─────────────────────────────────────────────────────────────────
PAD_XS =  4
PAD_SM =  8
PAD_MD = 12
PAD_LG = 16
PAD_XL = 24

# ── Dimensions ──────────────────────────────────────────────────────────────
SIDEBAR_WIDTH      = 280
SPEECH_BAR_HEIGHT  = 72
WINDOW_MIN_WIDTH   = 1050
WINDOW_MIN_HEIGHT  = 700
WINDOW_DEFAULT_W   = 1200
WINDOW_DEFAULT_H   = 800
CORNER_RADIUS      = 10
CORNER_RADIUS_SM   = 6

# ── Widget-level style dicts (for passing to CTk constructors) ──────────────
CARD_NORMAL  = {"fg_color": BG_MEDIUM,  "corner_radius": CORNER_RADIUS_SM}
CARD_HOVER   = {"fg_color": BG_LIGHT}
CARD_ACTIVE  = {"fg_color": ACCENT_SUBTLE}

BTN_PRIMARY = {
    "fg_color":       ACCENT,
    "hover_color":    ACCENT_HOVER,
    "text_color":     BG_DARKEST,
    "corner_radius":  CORNER_RADIUS_SM,
    "font":           FONT_BODY_BOLD,
}
BTN_GHOST = {
    "fg_color":       "transparent",
    "hover_color":    BG_LIGHT,
    "text_color":     TEXT_SECONDARY,
    "corner_radius":  CORNER_RADIUS_SM,
    "font":           FONT_BODY,
}
BTN_DANGER = {
    "fg_color":       DANGER,
    "hover_color":    "#D47A7A",
    "text_color":     TEXT_PRIMARY,
    "corner_radius":  CORNER_RADIUS_SM,
    "font":           FONT_BODY,
}
