
#!/usr/bin/env python3
"""Generate a slow neon contribution snake with temporary cell-eating pulses."""

import json
import os
import urllib.request
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

USER = os.getenv("GITHUB_USERNAME", "raghav4444")
TOKEN = os.getenv("GITHUB_TOKEN", "")
OUT = Path("dist")
OUT.mkdir(exist_ok=True)

COLS, ROWS = 53, 7
CELL, GAP, PAD, HEADER = 12, 4, 22, 42
W = PAD * 2 + COLS * (CELL + GAP) - GAP
H = HEADER + PAD * 2 + ROWS * (CELL + GAP) - GAP

BG = (2, 8, 5)
NEON = (57, 255, 20)
CORE = (220, 255, 200)
DARK = (7, 20, 12)
LEVELS = [
    DARK, (11, 43, 18), (15, 101, 31),
    (25, 183, 53), (57, 255, 20)
]

# Slow, smooth movement
FRAMES = 371
FRAME_MS = 140
SNAKE_LEN = 8
PULSE_STEPS = 8


def contributions():
    if not TOKEN:
        raise RuntimeError("GITHUB_TOKEN is required.")

    query = """
    query($login:String!){
      user(login:$login){
        contributionsCollection{
          contributionCalendar{
            weeks{
              contributionDays{contributionCount date}
            }
          }
        }
      }
    }"""

    body = json.dumps({
        "query": query,
        "variables": {"login": USER}
    }).encode()

    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "neon-predator-snake"
        }
    )

    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.loads(response.read())

    user = data.get("data", {}).get("user")
    if data.get("errors") or not user:
        raise RuntimeError(str(data.get("errors", "GitHub user not found")))

    weeks = user["contributionsCollection"][
        "contributionCalendar"
    ]["weeks"][-COLS:]

    grid = [[0] * ROWS for _ in range(COLS)]

    for x, week in enumerate(weeks):
        for day in week["contributionDays"]:
            dt = date.fromisoformat(day["date"])
            y = (dt.weekday() + 1) % 7
            grid[x][y] = int(day["contributionCount"])

    maximum = max((n for col in grid for n in col), default=1) or 1

    return [
        [
            0 if n == 0 else min(4, 1 + int(n / maximum * 3.99))
            for n in col
        ]
        for col in grid
    ]


def route():
    # Traverse each row in alternating directions.
    return [
        (x, y)
        for y in range(ROWS)
        for x in (
            range(COLS)
            if y % 2 == 0
            else range(COLS - 1, -1, -1)
        )
    ]


def xy(x, y):
    return (
        PAD + x * (CELL + GAP),
        HEADER + PAD + y * (CELL + GAP)
    )


def blend(base, target, amount):
    amount = max(0.0, min(1.0, amount))
    return tuple(
        int(a + (b - a) * amount)
        for a, b in zip(base, target)
    )


def render(grid, points, frame):
    im = Image.new("RGBA", (W, H), BG + (255,))
    d = ImageDraw.Draw(im)

    d.text((PAD, 13), "CONTRIBUTION MATRIX",
           fill=(117, 170, 128))
    d.text((W - PAD - 96, 13), "NEON / LIVE", fill=NEON)
    d.rounded_rectangle(
        (5, 5, W - 6, H - 6),
        radius=12,
        outline=(13, 42, 22),
        width=1
    )

    # Head advances one cell at a time.
    head = frame % len(points)

    # Build a temporary energy pulse behind the head.
    # These effects fade away; original contribution data is unchanged.
    pulses = {}

    for age in range(PULSE_STEPS + 1):
        position = (head - age) % len(points)
        cell = points[position]
        strength = (1 - age / (PULSE_STEPS + 1)) ** 1.4
        pulses[cell] = max(pulses.get(cell, 0), strength)

    # Draw contribution cells and temporarily illuminate visited cells.
    for x in range(COLS):
        for y in range(ROWS):
            level = grid[x][y]
            original = LEVELS[level] if level else DARK
            energy = pulses.get((x, y), 0)

            color = blend(original, NEON, energy)
            px, py = xy(x, y)

            d.rounded_rectangle(
                (px, py, px + CELL, py + CELL),
                radius=3,
                fill=color + (255,)
            )

    # Soft glow following the snake's body.
    glow = Image.new("RGBA", im.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)

    for tail in range(SNAKE_LEN, 0, -1):
        x, y = points[(head - tail) % len(points)]
        px, py = xy(x, y)

        alpha = int(
            200 * (1 - tail / (SNAKE_LEN + 1)) ** 1.5
        )

        gd.rounded_rectangle(
            (px - 3, py - 3, px + CELL + 3, py + CELL + 3),
            radius=6,
            fill=NEON + (alpha,)
        )

    im = Image.alpha_composite(
        im, glow.filter(ImageFilter.GaussianBlur(7))
    )

    # Gradient body segments.
    d = ImageDraw.Draw(im)

    for tail in range(SNAKE_LEN, 0, -1):
        x, y = points[(head - tail) % len(points)]
        px, py = xy(x, y)

        strength = 1 - tail / (SNAKE_LEN + 2)
        color = blend((8, 65, 15), NEON, strength)

        d.rounded_rectangle(
            (px + 2, py + 2, px + CELL - 2, py + CELL - 2),
            radius=3,
            fill=color + (255,)
        )

    # Bright predator head and neon aura.
    x, y = points[head]
    px, py = xy(x, y)

    head_glow = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(head_glow).ellipse(
        (px - 9, py - 9, px + CELL + 9, py + CELL + 9),
        fill=NEON + (245,)
    )

    im = Image.alpha_composite(
        im, head_glow.filter(ImageFilter.GaussianBlur(9))
    )

    d = ImageDraw.Draw(im)
    d.rounded_rectangle(
        (px + 1, py + 1, px + CELL - 1, py + CELL - 1),
        radius=4,
        fill=CORE + (255,),
        outline=NEON + (255,),
        width=2
    )

    # Occasional tiny electric sparks.
    for k in range(3):
        if (frame + k * 3) % 13 < 2:
            sx = px + CELL // 2 + (
                (frame * (k + 2) + k * 11) % 19
            ) - 9
            sy = py + CELL // 2 + (
                (frame * (k + 3) + k * 7) % 19
            ) - 9

            d.ellipse(
                (sx, sy, sx + 2, sy + 2),
                fill=CORE + (255,)
            )

    return im.convert("RGB")


def main():
    grid = contributions()
    points = route()

    frames = [
        render(grid, points, frame)
        for frame in range(FRAMES)
    ]

    frames[0].save(
        OUT / "neon-snake.gif",
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_MS,
        loop=0,
        optimize=True,
        disposal=2
    )

    print("Generated dist/neon-snake.gif")


if __name__ == "__main__":
    main()
