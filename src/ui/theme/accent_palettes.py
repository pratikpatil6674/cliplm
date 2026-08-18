from __future__ import annotations


ACCENT_PALETTES = {
    "Blue": {
        "dark": "#6ea2ff",
        "dark_hover": "#8ab5ff",
        "dark_soft": "#203553",
        "dark_border": "#34527b",
        "light": "#316bce",
        "light_hover": "#285eb9",
        "light_soft": "#e4edfb",
        "light_border": "#9fb9dc",
        "light_surface": "#5279ad",
        "light_hover_surface": "#f1f6fc",
    },
    "Lime": {
        "dark": "#d6ff62",
        "dark_hover": "#e4ff91",
        "dark_soft": "#1d2b21",
        "dark_border": "#52694e",
        "light": "#779c2a",
        "light_hover": "#688c20",
        "light_soft": "#e7f0d7",
        "light_border": "#bdd29b",
    },
    "Sky": {
        "dark": "#67d4ff",
        "dark_hover": "#9de4ff",
        "dark_soft": "#172831",
        "dark_border": "#31586a",
        "light": "#2185aa",
        "light_hover": "#196f90",
        "light_soft": "#e0f2fa",
        "light_border": "#acd7e8",
    },
    "Violet": {
        "dark": "#bda8ff",
        "dark_hover": "#d1c3ff",
        "dark_soft": "#251f34",
        "dark_border": "#50436d",
        "light": "#7358b7",
        "light_hover": "#61479f",
        "light_soft": "#eeeafd",
        "light_border": "#cfc3ef",
    },
    "Coral": {
        "dark": "#ff8c78",
        "dark_hover": "#ffb09f",
        "dark_soft": "#301e1a",
        "dark_border": "#633b33",
        "light": "#ca5f4b",
        "light_hover": "#b44e3c",
        "light_soft": "#fae8e4",
        "light_border": "#eabbb1",
    },
    "Amber": {
        "dark": "#ffc95c",
        "dark_hover": "#ffda8b",
        "dark_soft": "#2d2517",
        "dark_border": "#604d28",
        "light": "#a97116",
        "light_hover": "#925e0d",
        "light_soft": "#faf0d8",
        "light_border": "#e4cd93",
    },
    "Rose": {
        "dark": "#ff8fbc",
        "dark_hover": "#ffb4d2",
        "dark_soft": "#301d26",
        "dark_border": "#64394b",
        "light": "#b95079",
        "light_hover": "#a33e66",
        "light_soft": "#f9e7ef",
        "light_border": "#e7b7ca",
    },
}


THEME_OPTIONS = tuple(
    (name, name.casefold()) for name in ACCENT_PALETTES
)


_LIGHT_BASE = {
    "background": "#f4f6f1",
    "sidebar": "#e8ede7",
    "surface": "#ffffff",
    "surface_alt": "#f8faf7",
    "raised": "#edf2e9",
    "text": "#26312a",
    "strong": "#18211b",
    "muted": "#6f7c73",
    "border": "#d1dad2",
    "border_strong": "#9caaa0",
    "scrollbar": "#bdc8bf",
    "scrollbar_hover": "#98a69b",
}

_DARK_BASE = {
    "background": "#171e1a",
    "sidebar": "#1c2720",
    "surface": "#1a241e",
    "surface_alt": "#131b16",
    "raised": "#202b24",
    "text": "#dce3de",
    "strong": "#f5f7f5",
    "muted": "#91a098",
    "border": "#344139",
    "border_strong": "#596b60",
    "scrollbar": "#405047",
    "scrollbar_hover": "#607168",
}

_BLUE_LIGHT_BASE = {
    "background": "#f3f6f9",
    "sidebar": "#f8fafc",
    "surface": "#ffffff",
    "surface_alt": "#f9fbfd",
    "raised": "#edf2f7",
    "text": "#263448",
    "strong": "#1d2938",
    "muted": "#667487",
    "border": "#d8e0e9",
    "border_strong": "#afbdcc",
    "scrollbar": "#c0cbd8",
    "scrollbar_hover": "#98a9bc",
}

_NEUTRAL_DARK_BASE = {
    "background": "#101317",
    "sidebar": "#171b20",
    "surface": "#15191e",
    "surface_alt": "#1d232a",
    "raised": "#1b2026",
    "text": "#dfe4ea",
    "strong": "#f6f8fa",
    "muted": "#939da8",
    "border": "#303841",
    "border_strong": "#505b66",
    "scrollbar": "#3d4650",
    "scrollbar_hover": "#596571",
}


def _mix_colors(base: str, tint: str, amount: float) -> str:
    base_rgb = tuple(int(base[index:index + 2], 16) for index in (1, 3, 5))
    tint_rgb = tuple(int(tint[index:index + 2], 16) for index in (1, 3, 5))
    mixed = tuple(
        round(base_value * (1 - amount) + tint_value * amount)
        for base_value, tint_value in zip(base_rgb, tint_rgb)
    )
    return "#" + "".join(f"{channel:02x}" for channel in mixed)


def build_palette(accent_name: str, dark_mode: bool) -> dict[str, str]:
    display_name = next(
        (
            name
            for name in ACCENT_PALETTES
            if name.casefold() == accent_name.casefold()
        ),
        "Blue",
    )
    accent = ACCENT_PALETTES[display_name]
    prefix = "dark" if dark_mode else "light"
    palette = dict(_NEUTRAL_DARK_BASE if dark_mode else _BLUE_LIGHT_BASE)
    primary = accent[prefix]
    if dark_mode:
        palette["background"] = _mix_colors(
            palette["background"], primary, 0.08
        )
        palette["sidebar"] = _mix_colors(
            palette["sidebar"], primary, 0.12
        )
        palette["surface"] = _mix_colors(
            palette["surface"], primary, 0.07
        )
        palette["surface_alt"] = _mix_colors(
            palette["surface_alt"], primary, 0.10
        )
        palette["raised"] = _mix_colors(
            palette["raised"], primary, 0.08
        )
        palette["border"] = _mix_colors(
            palette["border"], primary, 0.06
        )
        palette["border_strong"] = accent["dark_border"]
    else:
        surface_tint = accent.get("light_surface", primary)
        palette["background"] = _mix_colors(
            palette["background"], surface_tint, 0.055
        )
        palette["sidebar"] = _mix_colors(
            palette["sidebar"], surface_tint, 0.10
        )
        palette["surface"] = _mix_colors(
            palette["surface"], surface_tint, 0.035
        )
        palette["surface_alt"] = _mix_colors(
            palette["surface_alt"], surface_tint, 0.08
        )
        palette["surface_alt"] = accent.get(
            "light_hover_surface", palette["surface_alt"]
        )
        palette["raised"] = _mix_colors(
            palette["raised"], surface_tint, 0.06
        )
        palette["border"] = _mix_colors(
            palette["border"], surface_tint, 0.04
        )
        palette["border_strong"] = accent["light_border"]
    palette.update(
        {
            "accent": primary,
            "accent_hover": accent[f"{prefix}_hover"],
            "accent_text": "#111711" if dark_mode else "#ffffff",
            "soft": accent[f"{prefix}_soft"],
            "soft_text": primary,
            "accent_border": accent[f"{prefix}_border"],
        }
    )
    return palette
