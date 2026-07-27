# Copyright (c) 2025 Nand Yaduwanshi <NoxxOP>
# Location: Supaul, Bihar
#
# All rights reserved.
#
# This code is the intellectual property of Nand Yaduwanshi.
# You are not allowed to copy, modify, redistribute, or use this
# code for commercial or personal projects without explicit permission.
#
# Allowed:
# - Forking for personal learning
# - Submitting improvements via pull requests
#
# Not Allowed:
# - Claiming this code as your own
# - Re-uploading without credit or permission
# - Selling or using commercially
#
# Contact for permissions:
# Email: badboy809075@gmail.com
#
# ATLEAST GIVE CREDITS IF YOU STEALING :
# ELSE NO FURTHER PUBLIC THUMBNAIL UPDATES

import os
import random
import aiohttp
import aiofiles
import traceback
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
from py_yt import VideosSearch
from ShrutiMusic import app
import math

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Layout: fixed branded banner on top, dynamic "now playing" bar underneath
# ---------------------------------------------------------------------------
CANVAS_W = 1320
BANNER_H = 760
PLAYER_H = 150
CANVAS_H = BANNER_H + PLAYER_H

FONT_REGULAR_PATH = "ShrutiMusic/assets/font2.ttf"
FONT_BOLD_PATH = "ShrutiMusic/assets/font3.ttf"
DEFAULT_THUMB = "ShrutiMusic/assets/ShrutiBots.jpg"

# Save your uploaded "Sakura X Music" image at this exact path (any name is
# fine as long as you update this constant to match).
BANNER_PATH = "ShrutiMusic/assets/sakura_banner.png"

# Theme colors pulled from the banner (candy pink) so the player bar matches.
THEME_PINK = (232, 90, 130)
THEME_PINK_DARK = (60, 18, 30)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def wrap_text(draw, text, font, max_width, max_lines=1):
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        if draw.textlength(test_line, font=font) <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    lines = lines[:max_lines]
    if len(lines) == max_lines:
        last = lines[-1]
        while draw.textlength(last + "...", font=font) > max_width and len(last) > 3:
            last = last[:-1]
        lines[-1] = last + "..." if len(words) > 1 else last
    return lines


def create_circle_mask(size):
    ss = 4
    big = size * ss
    mask = Image.new("L", (big, big), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, big, big], fill=255)
    return mask.resize((size, size), Image.LANCZOS)


def load_banner_background():
    """Load the fixed branded banner, fit it into BANNER_H without stretching,
    and fill any leftover width with a soft blurred version of itself so it
    always looks full-bleed regardless of the source image's exact ratio."""
    try:
        banner = Image.open(BANNER_PATH).convert("RGBA")
    except Exception:
        # graceful fallback: plain themed gradient if the banner file is missing
        fallback = Image.new("RGBA", (CANVAS_W, BANNER_H), (255, 235, 240, 255))
        return fallback

    # blurred cover-fit fill layer (fills the full canvas edge-to-edge)
    fill_scale = max(CANVAS_W / banner.width, BANNER_H / banner.height)
    fill = banner.resize((int(banner.width * fill_scale) + 2, int(banner.height * fill_scale) + 2), Image.LANCZOS)
    fx = (fill.width - CANVAS_W) // 2
    fy = (fill.height - BANNER_H) // 2
    fill = fill.crop((fx, fy, fx + CANVAS_W, fy + BANNER_H))
    fill = fill.filter(ImageFilter.GaussianBlur(30))

    # sharp contain-fit layer (keeps the whole artwork visible, no cropping)
    contain_scale = min(CANVAS_W / banner.width, BANNER_H / banner.height)
    sharp = banner.resize((int(banner.width * contain_scale), int(banner.height * contain_scale)), Image.LANCZOS)
    sx = (CANVAS_W - sharp.width) // 2
    sy = (BANNER_H - sharp.height) // 2

    canvas = fill.copy()
    canvas.paste(sharp, (sx, sy), sharp)
    return canvas


def draw_progress_bar(draw, x, y, width, height, progress, accent_color):
    draw.rounded_rectangle([x, y, x + width, y + height], radius=height // 2,
                            fill=(255, 255, 255, 60))
    fill_w = max(height, int(width * progress))
    draw.rounded_rectangle([x, y, x + fill_w, y + height], radius=height // 2,
                            fill=(*accent_color, 235))
    knob_r = int(height * 1.5)
    cx, cy = x + fill_w, y + height // 2
    draw.ellipse([cx - knob_r, cy - knob_r, cx + knob_r, cy + knob_r], fill=(255, 255, 255, 255))
    draw.ellipse([cx - knob_r + 3, cy - knob_r + 3, cx + knob_r - 3, cy + knob_r - 3],
                 fill=(*accent_color, 255))


def draw_sparkle(draw, x, y, size, color, alpha=220):
    draw.line([(x - size, y), (x + size, y)], fill=(*color, alpha), width=max(2, size // 6))
    draw.line([(x, y - size), (x, y + size)], fill=(*color, alpha), width=max(2, size // 6))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def gen_thumb(videoid: str):
    url = f"https://www.youtube.com/watch?v={videoid}"
    thumb_path = None

    try:
        results = VideosSearch(url, limit=1)
        result = (await results.next())["result"][0]

        title = result.get("title", "Unknown Title")
        duration = result.get("duration", "Unknown")
        thumburl = result["thumbnails"][0]["url"].split("?")[0]
        views = result.get("viewCount", {}).get("short", "Unknown Views")
        channel = result.get("channel", {}).get("name", "Unknown Channel")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(thumburl) as resp:
                    if resp.status == 200:
                        thumb_path = CACHE_DIR / f"thumb{videoid}.png"
                        async with aiofiles.open(thumb_path, "wb") as f:
                            await f.write(await resp.read())
        except Exception:
            pass

        if thumb_path and thumb_path.exists():
            base_img = Image.open(thumb_path).convert("RGBA")
        else:
            base_img = Image.open(DEFAULT_THUMB).convert("RGBA")

    except Exception as e:
        print(f"[gen_thumb Error - Using Default] {e}")
        try:
            base_img = Image.open(DEFAULT_THUMB).convert("RGBA")
            title = "ShrutiMusic"
            duration = "Unknown"
            views = "Unknown Views"
            channel = "ShrutiBots"
        except Exception:
            traceback.print_exc()
            return None

    try:
        # ---- top section: fixed Sakura X Music banner (always the same) ----
        banner_bg = load_banner_background()
        canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), THEME_PINK_DARK + (255,))
        canvas.paste(banner_bg, (0, 0), banner_bg)

        # ---- bottom section: dynamic "now playing" player bar ----
        draw = ImageDraw.Draw(canvas)
        bar_x, bar_y = 0, BANNER_H
        draw.rectangle([bar_x, bar_y, CANVAS_W, CANVAS_H], fill=(*THEME_PINK_DARK, 255))

        # soft pink glow line separating banner from the player bar
        draw.rectangle([0, bar_y, CANVAS_W, bar_y + 3], fill=(*THEME_PINK, 200))

        pad = 22
        art_size = PLAYER_H - pad * 2
        art_x = pad
        art_y = bar_y + pad

        mask = create_circle_mask(art_size)
        art = base_img.resize((art_size, art_size), Image.LANCZOS)
        art.putalpha(mask)

        # glow ring behind album art
        ring = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        rdraw = ImageDraw.Draw(ring)
        rdraw.ellipse([art_x - 6, art_y - 6, art_x + art_size + 6, art_y + art_size + 6],
                     outline=(*THEME_PINK, 200), width=3)
        ring = ring.filter(ImageFilter.GaussianBlur(2))
        canvas = Image.alpha_composite(canvas, ring)
        canvas.paste(art, (art_x, art_y), art)

        draw = ImageDraw.Draw(canvas)

        text_x = art_x + art_size + 26
        max_text_w = CANVAS_W - text_x - 220  # leave room for the timer on the right

        title_font = load_font(FONT_BOLD_PATH, 30)
        title_lines = wrap_text(draw, title, title_font, max_text_w, max_lines=1)
        title_y = bar_y + 24
        draw.text((text_x + 1, title_y + 1), title_lines[0], fill=(0, 0, 0, 160), font=title_font)
        draw.text((text_x, title_y), title_lines[0], fill=(255, 255, 255, 255), font=title_font)

        meta_font = load_font(FONT_REGULAR_PATH, 22)
        meta_text = f"{channel}  \u2022  {views}"
        meta_y = title_y + 40
        draw.text((text_x, meta_y), meta_text, fill=(230, 200, 210, 255), font=meta_font)

        # progress bar + timer
        duration_label = duration
        progress_ratio = random.uniform(0.2, 0.7)
        total_seconds = None
        if duration and ":" in str(duration):
            parts = str(duration).split(":")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                duration_label = f"{int(parts[0]):d}:{parts[1]}"
                total_seconds = int(parts[0]) * 60 + int(parts[1])

        bar_y2 = bar_y + PLAYER_H - 40
        bar_w = max_text_w
        draw_progress_bar(draw, text_x, bar_y2, bar_w, 8, progress_ratio, THEME_PINK)

        elapsed_label = "0:00"
        if total_seconds:
            e = int(total_seconds * progress_ratio)
            elapsed_label = f"{e // 60}:{e % 60:02d}"

        time_font = load_font(FONT_REGULAR_PATH, 20)
        draw.text((text_x, bar_y2 + 14), elapsed_label, fill=(235, 235, 240, 255), font=time_font)
        dur_w = draw.textlength(str(duration_label), font=time_font)
        draw.text((text_x + bar_w - dur_w, bar_y2 + 14), str(duration_label),
                  fill=(235, 235, 240, 255), font=time_font)

        # little "LIVE / NOW PLAYING" pill on the right of the player bar
        pill_text = "\u266a  PLAYING"
        pill_font = load_font(FONT_BOLD_PATH, 22)
        pill_w = draw.textlength(pill_text, font=pill_font) + 36
        pill_x = CANVAS_W - pill_w - 30
        pill_y = bar_y + 24
        draw.rounded_rectangle([pill_x, pill_y, pill_x + pill_w, pill_y + 40],
                               radius=20, fill=(*THEME_PINK, 230))
        draw.text((pill_x + 18, pill_y + 8), pill_text, fill=(255, 255, 255, 255), font=pill_font)

        # ---- rounded outer canvas corners (card look) ----
        rounded_mask = Image.new("L", canvas.size, 0)
        ImageDraw.Draw(rounded_mask).rounded_rectangle([0, 0, CANVAS_W, CANVAS_H], radius=30, fill=255)
        final = Image.new("RGBA", canvas.size, (0, 0, 0, 255))
        final.paste(canvas, (0, 0), rounded_mask)

        out = CACHE_DIR / f"{videoid}_final.png"
        final.convert("RGB").save(out, quality=95, optimize=True)

        if thumb_path and thumb_path.exists():
            try:
                os.remove(thumb_path)
            except Exception:
                pass

        return str(out)

    except Exception as e:
        print(f"[gen_thumb Processing Error] {e}")
        traceback.print_exc()
        return None
