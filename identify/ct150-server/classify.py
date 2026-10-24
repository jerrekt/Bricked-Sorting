"""Bricked Sorting: 2 shape groups x 8 color-family bins = 16 bins.

SHAPE  BRICK only for a plain "Brick N x N" (or N x N x N). Anything else, or unknown, is OTHER.

COLOR  Each bin is a color FAMILY, so colors a camera confuses share a bin. The camera only has to get the
       family right, not the exact shade:
         RED      Red / Orange            BROWN    Brown / Tan (also nougat, flesh, dark orange)
         YELLOW   Yellow                  BLACK    Black / Dark Gray
         GREEN    Green / Lime            WHITE    White / Light Gray
         BLUE     Blue / Aqua             SPECIAL  purple, pink, transparent, metallic, unknown, anything else
       Gray is split by lightness (dark -> BLACK, light -> WHITE) because black vs dark gray and white vs light gray
       are the confusions; dark vs light is easy for a camera.

Drop this next to brick_server.py:  from classify import choose_shape, choose_color_bucket, get_bin_id, bin_position
"""
import re

MIN_CONF = 50.0         # shape: below this, don't trust a "Brick" ID; treat as OTHER
MIN_COLOR_CONF = None   # color: e.g. 40.0 -> if Brickognize's color confidence is below this, use SPECIAL. None = off.

COLORS = ["RED", "YELLOW", "GREEN", "BLUE", "BROWN", "BLACK", "WHITE", "SPECIAL"]   # slot order, left to right (bins 1-8)
SHAPES = ["BRICK", "OTHER"]                                                         # BRICK = bottom floor, OTHER = top floor
COLOR_LABELS = {"RED": "Red / Orange", "YELLOW": "Yellow", "GREEN": "Green / Lime", "BLUE": "Blue / Aqua",
                "BROWN": "Brown / Tan", "BLACK": "Black / Dark Gray", "WHITE": "White / Light Gray", "SPECIAL": "Special"}

_PLAIN_BRICK = re.compile(r"^brick \d+ x \d+( x \d+)?$")

def choose_shape(name, confidence=None):
    """BRICK only for a plain rectangular brick. Curved, special, modified, round, sloped,
    plates, tiles, technic, printed, 'with ...' variants and anything unknown are OTHER."""
    if not name:
        return "OTHER"
    if confidence is not None:
        c = confidence * 100 if confidence <= 1.0 else confidence
        if c < MIN_CONF:
            return "OTHER"
    n = re.sub(r"\s+", " ", name.lower().replace(",", " ")).strip()
    return "BRICK" if _PLAIN_BRICK.match(n) else "OTHER"

# Checked FIRST. Colors a camera can't read reliably, or that don't belong to a family -> SPECIAL.
_SPECIAL = re.compile(
    r"\b(pink|magenta|purple|lavender|violet|lilac|olive|sand|coral|salmon|gold|copper|bronze|silver|"
    r"trans\w*|clear|glitter|glow|chrome|pearl|metallic|opal|speckle|milky|satin)\b")
_GRAY   = re.compile(r"\b(gr[ae]y|stone)\b")
_BROWN  = re.compile(r"\b(brown|tan|nougat|flesh)\b|\bdark orange\b")
_RED    = re.compile(r"\b(red|reddish|orange)\b")
_GREEN  = re.compile(r"\b(green|lime)\b")
_BLUE   = re.compile(r"\b(blue|azure|aqua|turquoise)\b")

def choose_color_bucket(color_name, color_confidence=None):
    """Map a Brickognize color name to one of the 8 color-family bins."""
    if not color_name:
        return "SPECIAL"
    if MIN_COLOR_CONF is not None and color_confidence is not None:
        c = color_confidence * 100 if color_confidence <= 1.0 else color_confidence
        if c < MIN_COLOR_CONF:
            return "SPECIAL"
    c = color_name.lower()
    if _SPECIAL.search(c):                       return "SPECIAL"
    if _GRAY.search(c):                          # before blue/green: "Light Bluish Gray"
        return "BLACK" if ("dark" in c or "black" in c) else "WHITE"
    if "black" in c:                             return "BLACK"
    if re.search(r"\bwhite\b", c):               return "WHITE"
    if _BROWN.search(c):                         return "BROWN"      # before red: "Reddish Brown", "Dark Orange"
    if _RED.search(c):                           return "RED"
    if _GREEN.search(c):                         return "GREEN"      # before yellow: "Yellowish Green"
    if _BLUE.search(c):                          return "BLUE"
    if "yellow" in c:                            return "YELLOW"
    return "SPECIAL"

def get_bin_id(shape, color_bucket):
    return f"{shape}_{color_bucket}"             # e.g. BRICK_RED, OTHER_SPECIAL (16 total)

def bin_position(bin_id):
    """(floor, slot) for the motor code. floor 0 = bottom (bricks), 1 = top (other). slot 0-7 = left to right."""
    shape, color = bin_id.split("_", 1)
    return SHAPES.index(shape), COLORS.index(color)

if __name__ == "__main__":
    tests = [
        ("Brick 2 x 4", 85, "Red", "BRICK_RED"), ("Brick 1 x 1", 90, "Dark Blue", "BRICK_BLUE"),
        ("Brick 1 x 2 x 5", 80, "Bright Light Yellow", "BRICK_YELLOW"), ("Brick 2 x 4", 40, "Red", "OTHER_RED"),
        ("Brick Curved 1 x 4 x 1 1/3 No Studs", 90, "White", "OTHER_WHITE"),
        ("Brick Special 1 x 2 with 2 Studs on 1 Side", 90, "Light Bluish Gray", "OTHER_WHITE"),   # light gray -> WHITE family
        ("Brick, Modified 1 x 2 with Studs on 1 Side", 90, "Black", "OTHER_BLACK"),
        ("Brick 2 x 4 with Pattern", 90, "Green", "OTHER_GREEN"), ("Brick Round 2 x 2", 90, "Reddish Brown", "OTHER_BROWN"),
        ("Plate 2 x 4", 90, "Orange", "OTHER_RED"), ("Tile 1 x 2", 90, "Trans-Clear", "OTHER_SPECIAL"),
        ("Slope 45 2 x 2", 90, "Dark Purple", "OTHER_SPECIAL"), ("Technic Brick 1 x 2 with Holes", 90, "Dark Bluish Gray", "OTHER_BLACK"),
        ("Brick 1 x 6", 90, "Lime", "BRICK_GREEN"), ("Brick 2 x 3", 90, "Bright Light Orange", "BRICK_RED"),
        ("Brick 1 x 2", 90, "Medium Stone Gray", "BRICK_WHITE"), ("Brick 2 x 2", 90, "Trans-Red", "BRICK_SPECIAL"),
        ("Brick 2 x 4", 90, "Dark Red", "BRICK_RED"), ("Brick 1 x 3", 90, "Bright Green", "BRICK_GREEN"),
        ("Brick 1 x 2", 90, "Tan", "BRICK_BROWN"), ("Brick 1 x 2", 90, "Dark Orange", "BRICK_BROWN"),
        ("Brick 1 x 2", 90, "Medium Nougat", "BRICK_BROWN"), ("Brick 2 x 2", 90, "Bright Pink", "BRICK_SPECIAL"),
        ("Brick 2 x 2", 90, "Light Aqua", "BRICK_BLUE"), ("Brick 1 x 2", 90, "Dark Gray", "BRICK_BLACK"),
        ("Brick 1 x 1", 90, "Yellowish Green", "BRICK_GREEN"), ("Brick 1 x 2", 90, "Sand Green", "BRICK_SPECIAL"),
        ("Brick 1 x 2", 90, "Flat Silver", "BRICK_SPECIAL"), ("Brick 1 x 2", 90, "Pearl Dark Gray", "BRICK_SPECIAL"),
        ("Brick 2 x 4", 90, "Dark Bluish Gray", "BRICK_BLACK"), ("Brick 2 x 4", 90, "Bright Light Blue", "BRICK_BLUE"),
        (None, None, None, "OTHER_SPECIAL"),
    ]
    bad = 0
    for name, conf, color, want in tests:
        got = get_bin_id(choose_shape(name, conf), choose_color_bucket(color))
        ok = got == want; bad += not ok
        print(("ok  " if ok else "FAIL"), f"{str(name):45s} {str(color):20s} -> {got}" + ("" if ok else f"  (wanted {want})"))
    assert len({get_bin_id(s, c) for s in SHAPES for c in COLORS}) == 16
    MIN_COLOR_CONF = 40.0                                   # optional color-confidence gate
    gate = (choose_color_bucket("Red", 20), choose_color_bucket("Red", 80), choose_color_bucket("Red", None))
    ok = gate == ("SPECIAL", "RED", "RED"); bad += not ok
    print(("ok  " if ok else "FAIL"), "color-confidence gate:", gate)
    MIN_COLOR_CONF = None
    print("positions:", bin_position("BRICK_RED"), bin_position("OTHER_SPECIAL"))
    print("ALL PASS" if not bad else f"{bad} FAILED")
