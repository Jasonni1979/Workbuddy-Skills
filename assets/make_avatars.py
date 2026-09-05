#!/usr/bin/env python3
"""生成 WorkBuddy 开放平台技能头像（512×512 PNG，品牌色 #185FA5）。"""
import math
import os

from PIL import Image, ImageDraw, ImageFilter

OUT = os.environ.get("AVATAR_OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "avatars"))
os.makedirs(OUT, exist_ok=True)

S = 512
BRAND = (24, 95, 165)        # #185FA5
BRAND_DARK = (14, 62, 112)
WHITE = (255, 255, 255)


def base_canvas():
    """品牌色渐变背景 + 柔和光斑。"""
    img = Image.new("RGB", (S, S), BRAND)
    px = img.load()
    for y in range(S):
        t = y / S
        r = int(BRAND[0] * (1 - t * 0.42) + BRAND_DARK[0] * t * 0.42)
        g = int(BRAND[1] * (1 - t * 0.42) + BRAND_DARK[1] * t * 0.42)
        b = int(BRAND[2] * (1 - t * 0.42) + BRAND_DARK[2] * t * 0.42)
        for x in range(S):
            px[x, y] = (r, g, b)
    # 右上角柔光
    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([S * 0.42, -S * 0.34, S * 1.28, S * 0.52], fill=(255, 255, 255, 46))
    glow = glow.filter(ImageFilter.GaussianBlur(48))
    img = Image.alpha_composite(img.convert("RGBA"), glow)
    return img, ImageDraw.Draw(img)


def ring(d, box, width, fill=WHITE, alpha_img=None):
    d.ellipse(box, outline=fill, width=width)


def arrowhead(d, c, r, theta_deg, size, color):
    """在圆 c 半径 r、角度 theta 处画沿角度增大方向(顺时针)的箭头。"""
    th = math.radians(theta_deg)
    pos = (c[0] + r * math.cos(th), c[1] + r * math.sin(th))
    dirv = (-math.sin(th), math.cos(th))
    perp = (math.cos(th), math.sin(th))
    tip = (pos[0] + dirv[0] * size, pos[1] + dirv[1] * size)
    b1 = (pos[0] + perp[0] * size * 0.75 - dirv[0] * size * 0.35,
          pos[1] + perp[1] * size * 0.75 - dirv[1] * size * 0.35)
    b2 = (pos[0] - perp[0] * size * 0.75 - dirv[0] * size * 0.35,
          pos[1] - perp[1] * size * 0.75 - dirv[1] * size * 0.35)
    d.polygon([tip, b1, b2], fill=color)


def save(img, name):
    path = os.path.join(OUT, name)
    img.convert("RGB").save(path, "PNG", optimize=True)
    kb = os.path.getsize(path) / 1024
    print(f"{name:34s} 512x512  {kb:6.1f} KB")


# ---------- 1. crm-analytics：分层漏斗 + 数据点 ----------
def icon_crm():
    img, d = base_canvas()
    cx, top = 256, 128
    layers = [(210, 74), (160, 74), (110, 74)]
    y = top
    for i, (w, h) in enumerate(layers):
        d.rounded_rectangle([cx - w, y, cx + w, y + h], radius=16,
                            fill=WHITE if i == 0 else None,
                            outline=WHITE, width=18)
        y += h + 26
    d.polygon([(cx - 60, y + 6), (cx + 60, y + 6), (cx, y + 66)], outline=WHITE, width=18)
    save(img, "crm-analytics.png")


# ---------- 2. promo-review：上升折线 + 峰值旗 ----------
def icon_promo():
    img, d = base_canvas()
    pts = [(96, 372), (180, 300), (256, 330), (340, 220), (420, 148)]
    d.line(pts, fill=WHITE, width=26, joint="curve")
    for x, y in pts:
        d.ellipse([x - 17, y - 17, x + 17, y + 17], fill=WHITE)
    # 峰值旗
    d.line([(420, 148), (420, 88)], fill=WHITE, width=14)
    d.polygon([(424, 88), (482, 106), (424, 124)], fill=WHITE)
    # 基线
    d.line([(80, 404), (436, 404)], fill=(255, 255, 255), width=12)
    save(img, "promo-review.png")


# ---------- 3. ad-compliance-check：盾牌 + 对勾 ----------
def icon_compliance():
    img, d = base_canvas()
    shield = [(256, 104), (386, 152), (386, 268), (256, 412), (126, 268), (126, 152)]
    d.polygon(shield, outline=WHITE, width=24)
    d.line([(196, 254), (240, 300), (326, 206)], fill=WHITE, width=30, joint="curve")
    save(img, "ad-compliance-check.png")


# ---------- 4. competitor-review：对比柱 + 放大镜 ----------
def icon_competitor():
    img, d = base_canvas()
    bars = [(120, 300, 60), (206, 232, 60), (292, 340, 60)]
    for x, y, w in bars:
        d.rounded_rectangle([x, y, x + w, 400], radius=14, outline=WHITE, width=18)
    d.line([(96, 424), (424, 424)], fill=WHITE, width=14)
    # 放大镜（右上）
    d.ellipse([322, 106, 430, 214], outline=WHITE, width=20)
    d.line([(412, 196), (456, 240)], fill=WHITE, width=22)
    save(img, "competitor-review.png")


# ---------- 5. review-insight：对话气泡 + 星标 ----------
def icon_review():
    img, d = base_canvas()
    d.rounded_rectangle([92, 116, 420, 330], radius=52, outline=WHITE, width=24)
    d.polygon([(180, 326), (180, 404), (258, 330)], outline=WHITE, width=24)
    # 内部三行文本条 + 星标
    d.line([(148, 186), (300, 186)], fill=WHITE, width=18)
    d.line([(148, 238), (364, 238)], fill=WHITE, width=18)
    cx, cy, r = 348, 292, 30
    star = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.44
        star.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    d.polygon(star, fill=WHITE)
    save(img, "review-insight.png")


# ---------- 6. member-lifecycle-calendar：日历 + 循环箭头 ----------
def icon_calendar():
    img, d = base_canvas()
    d.rounded_rectangle([104, 132, 408, 400], radius=32, outline=WHITE, width=22)
    d.line([(104, 214), (408, 214)], fill=WHITE, width=20)
    d.line([(176, 104), (176, 164)], fill=WHITE, width=20)
    d.line([(336, 104), (336, 164)], fill=WHITE, width=20)
    # 网格点
    for gx in (172, 256, 340):
        for gy in (268, 340):
            d.rounded_rectangle([gx - 20, gy - 20, gx + 20, gy + 20], radius=8, fill=WHITE)
    # 循环箭头徽章（右下角白底圆 + 品牌色箭头）
    d.ellipse([324, 324, 460, 460], fill=WHITE)
    d.arc([352, 352, 432, 432], start=-60, end=200, fill=BRAND, width=18)
    arrowhead(d, (392, 392), 40, 200, 22, BRAND)
    save(img, "member-lifecycle-calendar.png")


for fn in (icon_crm, icon_promo, icon_compliance, icon_competitor, icon_review, icon_calendar):
    fn()
print("\n输出目录:", OUT)
