"""SpeakStory Matte Brown Theme — design tokens and style helpers.

All UI components reference this module for consistent styling.
Premium warm palette with gradient-like accents and refined typography.
"""
from __future__ import annotations


# ── Colour Palette ──────────────────────────────────────────────────────────
BG_DARKEST  = "#1A1410"   # App background, deepest layer
BG_DARK     = "#2A2018"   # Sidebar, panels
BG_MEDIUM   = "#3D3028"   # Cards, note containers
BG_LIGHT    = "#4F4038"   # Hover states, elevated surfaces
BG_LIGHTER  = "#5F5048"   # Active / pressed states

# Premium gradient-like accent system
ACCENT            = "#C4956A"   # Primary buttons, active highlights
ACCENT_HOVER      = "#D4A57A"   # Button hover
ACCENT_DARK       = "#A47A50"   # Pressed / toggled state
ACCENT_SUBTLE     = "#3D3228"   # Accent at very low opacity for bg tints
ACCENT_GLOW       = "#E8C49A"   # Bright glow for focused elements
ACCENT_WARM       = "#B8845A"   # Warm mid-tone accent

# Surface elevation system
SURFACE_ELEVATED  = "#342A20"   # Slightly raised panels (between BG_DARK and BG_MEDIUM)
SURFACE_OVERLAY   = "#1F1A14"   # Modal overlays, tooltips

TEXT_PRIMARY   = "#F0E6DC"   # Main body text
TEXT_SECONDARY = "#A89888"   # Labels, timestamps, secondary info
TEXT_MUTED     = "#7A6A5A"   # Placeholders, disabled text
TEXT_BRIGHT    = "#FFF5EB"   # High-contrast emphasized text

SUCCESS  = "#6AAF6A"   # Recording active, success
DANGER   = "#C46A6A"   # Delete, errors
WARNING  = "#D4A54A"   # Warnings, caution
INFO     = "#6A9FC4"   # Informational highlights

BORDER       = "#4A3A2A"   # Subtle borders between sections
BORDER_LIGHT = "#5A4A3A"   # Lighter border for elevated elements
BORDER_FOCUS = "#C4956A"   # Border for focused inputs

# ── Tag Auto-Colours ────────────────────────────────────────────────────────
TAG_COLOURS = [
    "#C4956A", "#6AAF6A", "#C46A6A", "#6A9FC4", "#D4A54A",
    "#9A7ACC", "#6AC4B8", "#C47AA0", "#8AB46A", "#C49A4A",
]

def tag_colour(tag_text: str) -> str:
    """Deterministic colour for a tag based on its text hash."""
    return TAG_COLOURS[hash(tag_text) % len(TAG_COLOURS)]


# ── Typography ──────────────────────────────────────────────────────────────
FONT_FAMILY = "Segoe UI"

FONT_HERO     = (FONT_FAMILY, 32, "bold")    # Hero / splash text
FONT_TITLE    = (FONT_FAMILY, 26, "bold")    # Note title in editor
FONT_SUBTITLE = (FONT_FAMILY, 18, "bold")    # Section subtitles
FONT_HEADING  = (FONT_FAMILY, 16, "bold")    # App title / section heads
FONT_BODY     = (FONT_FAMILY, 14)            # Regular body text
FONT_BODY_BOLD = (FONT_FAMILY, 14, "bold")   # Emphasized body
FONT_SMALL    = (FONT_FAMILY, 12)            # Note card preview, tags
FONT_TINY     = (FONT_FAMILY, 10)            # Timestamps, counters
FONT_MICRO    = (FONT_FAMILY, 9)             # Very small labels
FONT_ICON     = (FONT_FAMILY, 22)            # Emoji / icon buttons
FONT_ICON_LG  = (FONT_FAMILY, 28)           # Large mic button icon
FONT_MONO     = ("Consolas", 13)             # Monospaced for code / stats

# ── Spacing ─────────────────────────────────────────────────────────────────
PAD_XS =  4
PAD_SM =  8
PAD_MD = 12
PAD_LG = 16
PAD_XL = 24
PAD_XXL = 32

# ── Dimensions ──────────────────────────────────────────────────────────────
SIDEBAR_WIDTH      = 300
SPEECH_BAR_HEIGHT  = 80
WINDOW_MIN_WIDTH   = 1050
WINDOW_MIN_HEIGHT  = 700
WINDOW_DEFAULT_W   = 1280
WINDOW_DEFAULT_H   = 850
CORNER_RADIUS      = 10
CORNER_RADIUS_SM   = 6
CORNER_RADIUS_LG   = 14

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
BTN_TOOLBAR = {
    "fg_color":       BG_MEDIUM,
    "hover_color":    BG_LIGHT,
    "text_color":     TEXT_PRIMARY,
    "corner_radius":  CORNER_RADIUS_SM,
    "font":           FONT_TINY,
}
