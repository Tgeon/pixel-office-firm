"""Generate the firm's character spritesheet (our own art, effectively CC0).

    uv run python scripts/make_sprites.py
    → office/static/assets/agents.png   (7 chars × 2 walk frames, 16×24 each)

Column order matches office/static/index.html: tom john david amy baldy hairy theo
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

OUT = Path(__file__).resolve().parent.parent / "office" / "static" / "assets" / "agents.png"
CW, CH = 16, 24  # cell size

SKIN = (238, 195, 160)
SKIN_SHADE = (214, 168, 132)
DARK = (28, 24, 34)

# name: (shirt, shirt_shade, hair_color or None for bald, style)
CHARS = {
    "tom":   ((91, 192, 235), (66, 152, 192), (61, 43, 31), "short"),
    "john":  ((142, 224, 110), (104, 178, 78), (90, 66, 40), "side"),
    "david": ((242, 208, 82), (198, 164, 52), (40, 36, 34), "short"),
    "amy":   ((217, 119, 217), (172, 84, 172), (114, 63, 26), "pony"),
    "baldy": ((240, 163, 94), (196, 122, 60), None, "bald"),
    "hairy": ((201, 106, 106), (158, 74, 74), (74, 48, 28), "mop"),
    "theo":  ((185, 163, 245), (142, 118, 208), (34, 30, 40), "neat"),
}


def draw_char(img: Image.Image, ox: int, oy: int, spec, frame: int) -> None:
    shirt, shade, hair, style = spec

    def px(x, y, c):
        img.putpixel((ox + x, oy + y), (*c, 255))

    def box(x0, y0, x1, y1, c):
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                px(x, y, c)

    # legs (frame 0: together, frame 1: stride)
    pants = (58, 52, 72)
    if frame == 0:
        box(5, 19, 7, 22, pants); box(9, 19, 11, 22, pants)
        box(5, 23, 7, 23, DARK); box(9, 23, 11, 23, DARK)          # shoes
    else:
        box(4, 19, 6, 22, pants); box(10, 19, 12, 21, pants)
        box(3, 23, 6, 23, DARK); box(10, 22, 13, 22, DARK)
    # torso
    box(4, 11, 12, 18, shirt)
    box(4, 16, 12, 18, shade)                                       # lower shade
    # arms
    arm_dy = 1 if frame else 0
    box(2, 12 + arm_dy, 3, 17, shade); box(13, 12 - arm_dy, 14, 17, shade)
    box(2, 18, 3, 18, SKIN); box(13, 18, 14, 18, SKIN)              # hands
    # head
    box(4, 2, 12, 10, SKIN)
    box(4, 8, 12, 10, SKIN_SHADE)
    # eyes
    px(6, 6, DARK); px(7, 6, DARK); px(10, 6, DARK); px(11, 6, DARK)
    # mouth
    px(8, 9, SKIN_SHADE); px(9, 9, (176, 120, 96))
    # hair styles
    if style == "bald":
        box(4, 2, 12, 3, SKIN)
        px(5, 2, (255, 236, 214)); px(6, 2, (255, 236, 214))        # shine
    elif hair:
        box(4, 1, 12, 3, hair)                                       # cap of hair
        box(4, 4, 5, 5, hair); box(11, 4, 12, 5, hair)               # sides
        if style == "mop":
            box(3, 1, 13, 5, hair); box(3, 6, 4, 8, hair); box(12, 6, 13, 8, hair)
            box(4, 0, 12, 0, hair)
        if style == "pony":
            box(13, 3, 14, 11, hair); box(13, 12, 14, 13, hair)      # ponytail
        if style == "side":
            box(4, 1, 9, 2, hair)                                    # side part
        if style == "neat":
            box(4, 1, 12, 2, hair)
            # tie
            box(8, 11, 9, 15, (46, 40, 60)); px(8, 16, (46, 40, 60))
    # glasses for john
    if style == "side":
        for x in (5, 6, 7, 9, 10, 11):
            px(x, 5, DARK)
    return


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    sheet = Image.new("RGBA", (CW * len(CHARS), CH * 2), (0, 0, 0, 0))
    for col, spec in enumerate(CHARS.values()):
        for frame in (0, 1):
            draw_char(sheet, col * CW, frame * CH, spec, frame)
    sheet.save(OUT)
    print(f"wrote {OUT} ({sheet.size[0]}x{sheet.size[1]})")


if __name__ == "__main__":
    main()
