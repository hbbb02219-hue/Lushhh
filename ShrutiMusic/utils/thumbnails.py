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

CANVAS_W, CANVAS_H = 1320, 760

FONT_REGULAR_PATH = "ShrutiMusic/assets/font2.ttf"
FONT_BOLD_PATH = "ShrutiMusic/assets/font3.ttf"
DEFAULT_THUMB = "ShrutiMusic/assets/ShrutiBots.jpg"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def wrap_text(draw, text, font, max_width):
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

    return lines[:2]


def random_gradient():
    # Soft, candy / pastel-leaning palettes for a "cute" look, mixed with a
    # few moody ones so it never feels repetitive.
    colors = [
        [(30, 16, 55), (94, 48, 120), (44, 22, 74)],      # grape soda
        [(20, 14, 40), (70, 40, 110), (30, 20, 60)],      # violet night
        [(45, 20, 60), (140, 70, 130), (60, 25, 70)],     # bubblegum
        [(15, 25, 45), (55, 70, 130), (25, 35, 70)],      # blueberry
        [(10, 30, 40), (30, 90, 110), (15, 45, 55)],      # mint teal
        [(50, 20, 35), (150, 60, 90), (60, 25, 45)],      # rose
        [(20, 20, 30), (60, 55, 90), (30, 30, 50)],       # slate dream
        [(35, 15, 45), (110, 55, 140), (45, 20, 60)],     # orchid
        [(15, 30, 30), (40, 100, 95), (20, 50, 50)],      # seafoam
        [(40, 18, 20), (130, 65, 55), (55, 25, 25)],      # peach ember
    ]
    return random.choice(colors)


def apply_gradient(canvas, colors):
    overlay = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for y in range(CANVAS_H):
        progress = y / CANVAS_H

        if progress < 0.4:
            t = progress / 0.4
            r = int(colors[0][0] * (1 - t) + colors[1][0] * t)
            g = int(colors[0][1] * (1 - t) + colors[1][1] * t)
            b = int(colors[0][2] * (1 - t) + colors[1][2] * t)
        else:
            t = (progress - 0.4) / 0.6
            r = int(colors[1][0] * (1 - t) + colors[2][0] * t)
            g = int(colors[1][1] * (1 - t) + colors[2][1] * t)
            b = int(colors[1][2] * (1 - t) + colors[2][2] * t)

        draw.line([(0, y), (CANVAS_W, y)], fill=(r, g, b, 255))

    return Image.alpha_composite(canvas, overlay)


def add_soft_bokeh(canvas, accent_color):
    """Big soft blurred circles floating in the background — the 'cute' glow."""
    bokeh_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    bdraw = ImageDraw.Draw(bokeh_layer)

    for _ in range(random.randint(4, 7)):
        r = random.randint(60, 160)
        x = random.randint(-40, CANVAS_W + 40)
        y = random.randint(-40, CANVAS_H + 40)
        alpha = random.randint(18, 40)
        color = random.choice([accent_color, (255, 255, 255)])
        bdraw.ellipse([x - r, y - r, x + r, y + r], fill=(*color, alpha))

    bokeh_layer = bokeh_layer.filter(ImageFilter.GaussianBlur(35))
    return Image.alpha_composite(canvas, bokeh_layer)


def random_layout():
    layouts = [
        {
            'art_size': random.randint(420, 500),
            'art_x': random.randint(70, 120),
            'art_shape': random.choice(['circle', 'rounded', 'blob']),
            'text_align': 'right',
            'accent_style': random.choice(['sparkle', 'dot', 'wave']),
        },
        {
            'art_size': random.randint(400, 480),
            'art_x': CANVAS_W - random.randint(500, 600),
            'art_shape': random.choice(['circle', 'rounded', 'blob']),
            'text_align': 'left',
            'accent_style': random.choice(['sparkle', 'wave', 'none']),
        },
        {
            'art_size': random.randint(390, 470),
            'art_x': random.randint(90, 140),
            'art_shape': random.choice(['circle', 'rounded', 'hexagon']),
            'text_align': 'right',
            'accent_style': random.choice(['dot', 'sparkle', 'wave']),
        },
    ]
    return random.choice(layouts)


def create_shape_mask(size, shape):
    # supersample for smoother edges on rounded/blob shapes
    ss = 4
    big = size * ss
    mask = Image.new("L", (big, big), 0)
    draw = ImageDraw.Draw(mask)

    if shape == 'circle':
        draw.ellipse([0, 0, big, big], fill=255)
    elif shape == 'rounded':
        radius = int(big * random.uniform(0.16, 0.26))
        draw.rounded_rectangle([0, 0, big, big], radius=radius, fill=255)
    elif shape == 'blob':
        # a gentle "squircle" — rounder & cuter than a plain rounded-rect
        radius = int(big * 0.32)
        draw.rounded_rectangle([0, 0, big, big], radius=radius, fill=255)
        draw = ImageDraw.Draw(mask)
    elif shape == 'hexagon':
        center = big // 2
        radius = big // 2 - int(big * 0.02)
        points = []
        for i in range(6):
            angle = math.pi / 3 * i - math.pi / 6
            x = center + radius * math.cos(angle)
            y = center + radius * math.sin(angle)
            points.append((x, y))
        draw.polygon(points, fill=255)
    else:
        draw.ellipse([0, 0, big, big], fill=255)

    mask = mask.resize((size, size), Image.LANCZOS)
    return mask


def random_accent_color():
    # Soft pastel / candy accents for a cuter vibe
    colors = [
        (255, 158, 200),   # candy pink
        (168, 197, 255),   # baby blue
        (255, 209, 148),   # peach
        (190, 168, 255),   # lavender
        (150, 235, 210),   # mint
        (255, 179, 186),   # blush
        (180, 225, 255),   # sky
        (255, 200, 235),   # cotton candy
        (200, 235, 160),   # soft lime
        (255, 224, 145),   # honey
    ]
    return random.choice(colors)


def add_particles(draw, accent_color):
    for _ in range(random.randint(12, 22)):
        x = random.randint(0, CANVAS_W)
        y = random.randint(0, CANVAS_H)
        size = random.randint(1, 3)
        alpha = random.randint(40, 110)
        draw.ellipse([x, y, x + size, y + size], fill=(*accent_color, alpha))


def draw_sparkle(draw, x, y, size, color, alpha=220):
    """A tiny 4-point sparkle/star — cute accent."""
    draw.line([(x - size, y), (x + size, y)], fill=(*color, alpha), width=max(2, size // 6))
    draw.line([(x, y - size), (x, y + size)], fill=(*color, alpha), width=max(2, size // 6))
    small = size // 2
    draw.line([(x - small, y - small), (x + small, y + small)], fill=(*color, int(alpha * 0.6)), width=1)
    draw.line([(x - small, y + small), (x + small, y - small)], fill=(*color, int(alpha * 0.6)), width=1)


def add_accent_elements(draw, layout, accent_color):
    style = layout['accent_style']

    if style == 'sparkle':
        for _ in range(random.randint(4, 7)):
            x = random.randint(40, CANVAS_W - 40)
            y = random.randint(40, CANVAS_H - 40)
            size = random.randint(6, 16)
            draw_sparkle(draw, x, y, size, accent_color)

    elif style == 'dot':
        for _ in range(random.randint(4, 9)):
            x = random.randint(40, CANVAS_W - 40)
            y = random.randint(40, CANVAS_H - 40)
            size = random.randint(4, 9)
            draw.ellipse([x, y, x + size, y + size], fill=(*accent_color, 130))

    elif style == 'wave':
        y_start = random.randint(90, 150)
        for x in range(0, CANVAS_W, 4):
            wave_y = y_start + int(math.sin(x / 55) * 18)
            draw.ellipse([x, wave_y, x + 3, wave_y + 3], fill=(*accent_color, 90))


def add_glow_ring(canvas, x, y, size, color, blur_amount):
    ring_size = size + 40
    ring_img = Image.new("RGBA", (ring_size, ring_size), (0, 0, 0, 0))
    rdraw = ImageDraw.Draw(ring_img)

    for i in range(6):
        offset = i * 4
        alpha = 160 - (i * 24)
        rdraw.ellipse([offset, offset, ring_size - offset, ring_size - offset],
                      outline=(*color, max(alpha, 0)), width=3)

    ring_img = ring_img.filter(ImageFilter.GaussianBlur(blur_amount))
    canvas.paste(ring_img, (x - 20, y - 20), ring_img)


def add_glass_panel(canvas, x, y, w, h, radius=28, alpha=55):
    """A soft frosted-glass style backing panel behind the text block."""
    panel = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    pdraw = ImageDraw.Draw(panel)
    pdraw.rounded_rectangle([x, y, x + w, y + h], radius=radius,
                             fill=(255, 255, 255, alpha))
    panel = panel.filter(ImageFilter.GaussianBlur(2))
    return Image.alpha_composite(canvas, panel)


def draw_progress_bar(draw, x, y, width, height, progress, accent_color):
    """Cute little rounded progress/duration bar."""
    draw.rounded_rectangle([x, y, x + width, y + height], radius=height // 2,
                            fill=(255, 255, 255, 60))
    fill_w = max(height, int(width * progress))
    draw.rounded_rectangle([x, y, x + fill_w, y + height], radius=height // 2,
                            fill=(*accent_color, 230))
    knob_r = int(height * 1.6)
    cx, cy = x + fill_w, y + height // 2
    draw.ellipse([cx - knob_r, cy - knob_r, cx + knob_r, cy + knob_r],
                 fill=(255, 255, 255, 255))
    draw.ellipse([cx - knob_r + 3, cy - knob_r + 3, cx + knob_r - 3, cy + knob_r - 3],
                 fill=(*accent_color, 255))


def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


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
        canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 255))

        gradient_colors = random_gradient()
        canvas = apply_gradient(canvas, gradient_colors)

        layout = random_layout()
        accent_color = random_accent_color()

        # soft glowing bokeh circles behind everything — this is what gives
        # the "cute / dreamy" feel instead of flat particles only
        canvas = add_soft_bokeh(canvas, accent_color)

        draw = ImageDraw.Draw(canvas)
        add_particles(draw, accent_color)
        canvas = canvas.filter(ImageFilter.GaussianBlur(0.6))

        art_size = layout['art_size']
        art_x = layout['art_x']
        art_y = (CANVAS_H - art_size) // 2

        mask = create_shape_mask(art_size, layout['art_shape'])

        art_source = ImageEnhance.Contrast(base_img).enhance(1.05)
        art_source = ImageEnhance.Color(art_source).enhance(1.1)
        art = art_source.resize((art_size, art_size), Image.LANCZOS)
        art.putalpha(mask)

        # glow ring almost always on now — reads as "cute halo" around the art
        add_glow_ring(canvas, art_x, art_y, art_size, accent_color, random.randint(10, 16))

        # thin white "sticker" border ring right at the edge of the art
        border_pad = 6
        border_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        bdraw = ImageDraw.Draw(border_layer)
        border_mask = create_shape_mask(art_size + border_pad * 2, layout['art_shape'])
        border_img = Image.new("RGBA", (art_size + border_pad * 2, art_size + border_pad * 2),
                                (255, 255, 255, 235))
        border_img.putalpha(border_mask)
        canvas.paste(border_img, (art_x - border_pad, art_y - border_pad), border_img)
        canvas.paste(art, (art_x, art_y), art)

        draw = ImageDraw.Draw(canvas)
        add_accent_elements(draw, layout, accent_color)

        # ---- Branding ----
        brand_font = load_font(FONT_BOLD_PATH, random.randint(34, 44))
        brand_x = random.randint(35, 55)
        brand_y = random.randint(28, 42)

        draw.text((brand_x + 2, brand_y + 2), app.username, fill=(0, 0, 0, 150), font=brand_font)
        draw.text((brand_x, brand_y), app.username, fill=(255, 255, 255, 255), font=brand_font)

        brand_bbox = draw.textbbox((brand_x, brand_y), app.username, font=brand_font)
        brand_w = brand_bbox[2] - brand_bbox[0]
        underline_y = brand_bbox[3] + 6
        draw.line([(brand_x, underline_y), (brand_x + brand_w, underline_y)],
                  fill=(*accent_color, 220), width=3)
        # cute little sparkle right after the brand name
        draw_sparkle(draw, brand_x + brand_w + 16, brand_y + 14, 8, accent_color)

        # ---- Text block position ----
        if layout['text_align'] == 'right':
            info_x = art_x + art_size + random.randint(60, 100)
            max_text_w = CANVAS_W - info_x - 50
        else:
            info_x = random.randint(50, 100)
            max_text_w = art_x - info_x - 50

        # soft glass panel behind the info block for readability + cuteness
        panel_x = info_x - 24
        panel_y = 95
        panel_w = max_text_w + 48
        panel_h = CANVAS_H - 130
        canvas = add_glass_panel(canvas, panel_x, panel_y, panel_w, panel_h, radius=32, alpha=45)
        draw = ImageDraw.Draw(canvas)
        # redraw accents/branding on top since glass panel repainted that area only if overlapping;
        # panel sits within the text zone so branding (top-left corner) is unaffected in most layouts.

        np_options = ["NOW PLAYING", "PLAYING NOW", "ON REPEAT", "TUNE IN"]
        np_font = load_font(FONT_BOLD_PATH, random.randint(48, 64))
        np_text = random.choice(np_options)
        np_y = random.randint(130, 165)

        draw.text((info_x + 3, np_y + 3), np_text, fill=(0, 0, 0, 170), font=np_font)
        draw.text((info_x, np_y), np_text, fill=(*accent_color, 255), font=np_font)
        draw_sparkle(draw, info_x - 22, np_y + 20, 10, accent_color)

        title_font_size = random.randint(36, 46)
        title_font = load_font(FONT_BOLD_PATH, title_font_size)
        title_lines = wrap_text(draw, title, title_font, max_text_w)
        title_text = "\n".join(title_lines)
        title_y = np_y + random.randint(75, 100)

        draw.multiline_text((info_x + 2, title_y + 2), title_text,
                            fill=(0, 0, 0, 160), font=title_font,
                            spacing=random.randint(8, 14))
        draw.multiline_text((info_x, title_y), title_text,
                            fill=(255, 255, 255, 255), font=title_font,
                            spacing=random.randint(8, 14))

        meta_font = load_font(FONT_REGULAR_PATH, random.randint(26, 32))
        meta_y = title_y + random.randint(110, 145)
        line_spacing = random.randint(42, 52)

        duration_label = duration
        progress_ratio = random.uniform(0.25, 0.75)
        total_seconds = None
        if duration and ":" in str(duration):
            parts = str(duration).split(":")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                duration_label = f"{parts[0]}m {parts[1]}s"
                total_seconds = int(parts[0]) * 60 + int(parts[1])

        meta_items = [
            f"\u25B6 {views}",
            f"\u2665 {channel}",
        ]

        for idx, meta in enumerate(meta_items):
            y = meta_y + (idx * line_spacing)
            draw.text((info_x + 1, y + 1), meta, fill=(0, 0, 0, 140), font=meta_font)
            draw.text((info_x, y), meta, fill=(235, 235, 245, 255), font=meta_font)

        # ---- Cute progress bar with elapsed / total ----
        bar_y = meta_y + (len(meta_items) * line_spacing) + 18
        bar_w = max_text_w
        bar_h = 10
        draw_progress_bar(draw, info_x, bar_y, bar_w, bar_h, progress_ratio, accent_color)

        elapsed_label = "0:00"
        if total_seconds:
            elapsed_sec = int(total_seconds * progress_ratio)
            elapsed_label = f"{elapsed_sec // 60}:{elapsed_sec % 60:02d}"

        time_font = load_font(FONT_REGULAR_PATH, 22)
        draw.text((info_x, bar_y + 18), elapsed_label, fill=(230, 230, 240, 255), font=time_font)
        dur_w = draw.textlength(str(duration_label), font=time_font)
        draw.text((info_x + bar_w - dur_w, bar_y + 18), str(duration_label),
                  fill=(230, 230, 240, 255), font=time_font)

        # ---- Corner sparkle accents (replaces plain corner lines) ----
        if random.choice([True, False]):
            draw_sparkle(draw, 45, 45, random.randint(10, 16), accent_color, alpha=180)
            draw_sparkle(draw, CANVAS_W - 45, 45, random.randint(10, 16), accent_color, alpha=180)

        # ---- Rounded outer canvas corners (cute card look) ----
        rounded_mask = Image.new("L", canvas.size, 0)
        rmdraw = ImageDraw.Draw(rounded_mask)
        rmdraw.rounded_rectangle([0, 0, CANVAS_W, CANVAS_H], radius=36, fill=255)
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
