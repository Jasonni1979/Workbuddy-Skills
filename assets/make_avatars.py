#!/usr/bin/env python3
"""生成 WorkBuddy 开放平台技能头像（512×512 PNG，品牌色 #185FA5）。"""
import math
import os

from PIL import Image, ImageDraw, ImageFilter

OUT = "/Users/wise01/WorkBuddy/2026-09-05-10-17-28/outputs/avatars"
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


# ---------- 7. multi-platform-merge：三源汇聚到一张表 ----------
def icon_merge():
    img, d = base_canvas()
    for y in (140, 236, 332):
        d.rounded_rectangle([88, y, 196, y + 60], radius=14, outline=WHITE, width=16)
        d.line([(196, y + 30), (268, 256)], fill=WHITE, width=14)
    d.rounded_rectangle([268, 168, 424, 344], radius=18, outline=WHITE, width=20)
    d.line([(268, 224), (424, 224)], fill=WHITE, width=14)
    d.line([(268, 284), (424, 284)], fill=WHITE, width=14)
    save(img, "multi-platform-merge.png")


# ---------- 8. inventory-alert：箱子 + 警示徽章 ----------
def icon_inventory():
    img, d = base_canvas()
    d.polygon([(256, 96), (400, 168), (256, 240), (112, 168)], outline=WHITE, width=20)
    d.line([(112, 168), (112, 320)], fill=WHITE, width=20)
    d.line([(400, 168), (400, 320)], fill=WHITE, width=20)
    d.line([(256, 240), (256, 392)], fill=WHITE, width=20)
    d.line([(112, 320), (256, 392)], fill=WHITE, width=20)
    d.line([(400, 320), (256, 392)], fill=WHITE, width=20)
    d.ellipse([316, 316, 452, 452], fill=WHITE)
    d.line([(384, 350), (384, 402)], fill=BRAND, width=20)
    d.ellipse([375, 416, 393, 434], fill=BRAND)
    save(img, "inventory-alert.png")


# ---------- 9. ecom-daily-report：报表 + 迷你柱状 ----------
def icon_daily():
    img, d = base_canvas()
    d.rounded_rectangle([104, 96, 408, 416], radius=28, outline=WHITE, width=22)
    d.line([(104, 168), (408, 168)], fill=WHITE, width=18)
    d.line([(148, 216), (300, 216)], fill=WHITE, width=16)
    bars = [(152, 320), (216, 272), (280, 344)]
    for x, y in bars:
        d.rounded_rectangle([x, y, x + 44, 376], radius=10, fill=WHITE)
    d.line([(330, 376), (330, 240)], fill=WHITE, width=14)
    d.polygon([(312, 252), (348, 252), (330, 224)], fill=WHITE)
    save(img, "ecom-daily-report.png")


# ---------- 10. video-script-planner：场记板 + 播放键 ----------
def icon_video():
    img, d = base_canvas()
    d.rounded_rectangle([96, 176, 416, 408], radius=24, outline=WHITE, width=22)
    d.rounded_rectangle([96, 112, 416, 172], radius=14, outline=WHITE, width=20)
    for x in (156, 226, 296, 366):
        d.line([(x, 126), (x, 158)], fill=WHITE, width=16)
    d.polygon([(224, 244), (224, 348), (316, 296)], fill=WHITE)
    save(img, "video-script-planner.png")


for fn in (icon_merge, icon_inventory, icon_daily, icon_video):
    fn()


# ---------- 行业层徽章（左上角小徽记，主体图形区分行业） ----------
def industry_badge(d):
    """行业层技能统一角标：左上角小菱形徽记，标识"行业手册"系列。"""
    d.polygon([(72, 56), (96, 80), (72, 104), (48, 80)], fill=WHITE)


# ---------- 11. beauty-ops：口红 + 星芒 ----------
def icon_beauty():
    img, d = base_canvas()
    industry_badge(d)
    d.polygon([(208, 244), (208, 200), (240, 140), (272, 200), (272, 244)], outline=WHITE, width=20)
    d.rectangle([196, 244, 284, 400], outline=WHITE, width=22)
    d.line([(196, 300), (284, 300)], fill=WHITE, width=14)
    # 星芒
    d.line([(360, 160), (360, 220)], fill=WHITE, width=12)
    d.line([(330, 190), (390, 190)], fill=WHITE, width=12)
    d.line([(396, 260), (396, 296)], fill=WHITE, width=10)
    d.line([(378, 278), (414, 278)], fill=WHITE, width=10)
    save(img, "beauty-ops.png")


# ---------- 12. fashion-ops：衣架 + 裙摆 ----------
def icon_fashion():
    img, d = base_canvas()
    industry_badge(d)
    d.arc([226, 108, 286, 168], start=180, end=20, fill=WHITE, width=16)
    d.line([(256, 138), (256, 168)], fill=WHITE, width=16)
    d.line([(256, 168), (140, 240)], fill=WHITE, width=18)
    d.line([(256, 168), (372, 240)], fill=WHITE, width=18)
    d.line([(140, 240), (372, 240)], fill=WHITE, width=18)
    d.polygon([(180, 276), (332, 276), (368, 416), (144, 416)], outline=WHITE, width=20)
    d.line([(256, 276), (256, 416)], fill=WHITE, width=12)
    save(img, "fashion-ops.png")


# ---------- 13. luxury-ops：钻石 ----------
def icon_luxury():
    img, d = base_canvas()
    industry_badge(d)
    d.polygon([(156, 200), (256, 128), (356, 200), (256, 400)], outline=WHITE, width=22)
    d.line([(156, 200), (356, 200)], fill=WHITE, width=16)
    d.line([(216, 156), (216, 200), (256, 400)], fill=WHITE, width=12)
    d.line([(296, 156), (296, 200), (256, 400)], fill=WHITE, width=12)
    d.line([(216, 200), (256, 128)], fill=WHITE, width=12)
    d.line([(296, 200), (256, 128)], fill=WHITE, width=12)
    save(img, "luxury-ops.png")


# ---------- 14. electronics-ops：芯片 ----------
def icon_electronics():
    img, d = base_canvas()
    industry_badge(d)
    d.rounded_rectangle([168, 168, 344, 344], radius=24, outline=WHITE, width=22)
    d.rounded_rectangle([224, 224, 288, 288], radius=10, fill=WHITE)
    for t in (212, 256, 300):
        d.line([(t, 120), (t, 168)], fill=WHITE, width=14)
        d.line([(t, 344), (t, 392)], fill=WHITE, width=14)
        d.line([(120, t), (168, t)], fill=WHITE, width=14)
        d.line([(344, t), (392, t)], fill=WHITE, width=14)
    save(img, "electronics-ops.png")


# ---------- 15. sports-ops：山峰 + 攀登折线 ----------
def icon_sports():
    img, d = base_canvas()
    industry_badge(d)
    # 主峰
    d.polygon([(120, 400), (256, 150), (392, 400)], outline=WHITE, width=22)
    # 副峰（自山脊延伸出的第二条山脊线）
    d.line([(330, 288), (408, 400)], fill=WHITE, width=18)
    # 雪线
    d.line([(212, 232), (256, 262), (300, 232)], fill=WHITE, width=14)
    # 攀登折线（左下→峰顶）
    d.line([(150, 380), (200, 340), (230, 360), (280, 300)], fill=WHITE, width=12)
    # 峰顶旗
    d.line([(256, 150), (256, 96)], fill=WHITE, width=12)
    d.polygon([(256, 96), (316, 112), (256, 130)], fill=WHITE)
    save(img, "sports-ops.png")


# ---------- 16. liquor-ops：威士忌杯 + 冰块 ----------
def icon_liquor():
    img, d = base_canvas()
    industry_badge(d)
    # 杯身（上宽下窄梯形，圆角底）
    d.polygon([(176, 160), (336, 160), (316, 380), (196, 380)], outline=WHITE, width=22)
    d.line([(196, 380), (316, 380)], fill=WHITE, width=22)
    # 酒液面
    d.line([(188, 264), (324, 264)], fill=WHITE, width=16)
    # 冰块（旋转正方形）
    d.polygon([(256, 288), (296, 320), (256, 352), (216, 320)], outline=WHITE, width=14)
    # 香气线（杯口上方两道弧）
    d.arc([216, 88, 256, 128], start=200, end=340, fill=WHITE, width=12)
    d.arc([268, 76, 308, 116], start=200, end=340, fill=WHITE, width=12)
    save(img, "liquor-ops.png")


for fn in (icon_beauty, icon_fashion, icon_luxury, icon_electronics, icon_sports, icon_liquor):
    fn()


# ---------- 17. content-matrix-planner：3×3 内容九宫格 + 加号 ----------
def icon_content_matrix():
    img, d = base_canvas()
    cell, gap, x0, y0 = 88, 18, 122, 122
    for r in range(3):
        for c in range(3):
            x, y = x0 + c * (cell + gap), y0 + r * (cell + gap)
            filled = (r, c) in [(0, 1), (1, 0), (1, 2), (2, 1)]
            d.rounded_rectangle([x, y, x + cell, y + cell], radius=14,
                                fill=WHITE if filled else None, outline=WHITE, width=14)
    save(img, "content-matrix-planner.png")


# ---------- 18. cs-ticket-insight：耳麦 + 对话气泡 ----------
def icon_cs():
    img, d = base_canvas()
    # 耳麦：头带弧 + 两侧耳罩
    d.arc([156, 120, 356, 320], start=180, end=360, fill=WHITE, width=22)
    d.rounded_rectangle([136, 240, 184, 320], radius=20, fill=WHITE)
    d.rounded_rectangle([328, 240, 376, 320], radius=20, fill=WHITE)
    # 麦克风杆
    d.line([(352, 320), (352, 360), (300, 376)], fill=WHITE, width=14, joint="curve")
    # 对话气泡（左下）
    d.rounded_rectangle([112, 348, 252, 424], radius=18, outline=WHITE, width=14)
    d.polygon([(150, 424), (170, 424), (146, 448)], fill=WHITE)
    for dx in (140, 170, 200):
        d.ellipse([dx, 378, dx + 12, 390], fill=WHITE)
    save(img, "cs-ticket-insight.png")


# ---------- 19. return-rate-clinic：退货回环箭头 + 听诊十字 ----------
def icon_return():
    img, d = base_canvas()
    c = (256, 244)
    # 回环箭头（270° 弧 + 箭头）
    d.arc([c[0] - 118, c[1] - 118, c[0] + 118, c[1] + 118], start=300, end=240, fill=WHITE, width=24)
    arrowhead(d, c, 118, 240, 34, WHITE)
    # 中心十字（诊断）
    d.rounded_rectangle([c[0] - 20, c[1] - 56, c[0] + 20, c[1] + 56], radius=10, fill=WHITE)
    d.rounded_rectangle([c[0] - 56, c[1] - 20, c[0] + 56, c[1] + 20], radius=10, fill=WHITE)
    save(img, "return-rate-clinic.png")


# ---------- 20. private-domain-sop：双人 + 对话气泡 ----------
def icon_private():
    img, d = base_canvas()
    # 两人（左大右小）
    d.ellipse([150, 170, 230, 250], outline=WHITE, width=18)
    d.arc([130, 260, 250, 380], start=180, end=360, fill=WHITE, width=18)
    d.line([(130, 320), (130, 380)], fill=WHITE, width=18)
    d.line([(250, 320), (250, 380)], fill=WHITE, width=18)
    d.ellipse([286, 200, 346, 260], outline=WHITE, width=14)
    d.arc([270, 270, 362, 366], start=180, end=360, fill=WHITE, width=14)
    # 右上对话气泡
    d.rounded_rectangle([356, 110, 452, 178], radius=16, fill=WHITE)
    d.polygon([(380, 178), (404, 178), (376, 206)], fill=WHITE)
    for dx in (378, 402, 426):
        d.ellipse([dx, 136, dx + 10, 146], fill=BRAND)
    save(img, "private-domain-sop.png")


# ---------- 21. member-oneid-merge：多源汇聚到 ID 徽章 ----------
def icon_oneid():
    img, d = base_canvas()
    # 左侧三个源节点
    for y in (140, 240, 340):
        d.rounded_rectangle([96, y - 26, 176, y + 26], radius=12, outline=WHITE, width=14)
        d.line([(176, y), (252, 244)], fill=WHITE, width=10)
    # 中央 ID 徽章
    d.ellipse([252, 176, 388, 312], fill=WHITE)
    d.ellipse([296, 208, 344, 256], fill=BRAND)
    d.arc([284, 244, 356, 300], start=180, end=360, fill=BRAND, width=14)
    # 右侧输出单线 + 右向箭头
    d.line([(388, 244), (440, 244)], fill=WHITE, width=14)
    d.polygon([(464, 244), (436, 228), (436, 260)], fill=WHITE)
    save(img, "member-oneid-merge.png")


# ---------- 22. price-governance：价签 + 盾牌对勾 ----------
def icon_price():
    img, d = base_canvas()
    # 价签（旋转 45° 的方牌 + 挂孔）
    d.polygon([(150, 250), (250, 150), (370, 270), (270, 370)], outline=WHITE, width=20)
    d.ellipse([232, 176, 268, 212], outline=WHITE, width=12)
    d.line([(206, 258), (262, 314)], fill=WHITE, width=12)
    # 盾牌（右上）
    d.polygon([(388, 120), (452, 144), (452, 200), (420, 240), (388, 200)], outline=WHITE, width=14)
    d.line([(404, 176), (416, 192), (438, 158)], fill=WHITE, width=12, joint="curve")
    save(img, "price-governance.png")


# ---------- 23. channel-health-score：雷达图 ----------
def icon_channel():
    img, d = base_canvas()
    import math as m
    c = (256, 256)
    R = 140
    # 六边形网格两圈
    for rr in (R, R * 0.55):
        pts = [(c[0] + rr * m.cos(m.radians(a)), c[1] + rr * m.sin(m.radians(a)))
               for a in range(-90, 270, 60)]
        d.polygon(pts, outline=WHITE, width=10)
    # 轴线
    for a in range(-90, 270, 60):
        d.line([c, (c[0] + R * m.cos(m.radians(a)), c[1] + R * m.sin(m.radians(a)))],
               fill=WHITE, width=6)
    # 数据多边形（不规则，填充半透明感用描边+顶点圆）
    vals = [0.9, 0.55, 0.75, 0.45, 0.85, 0.6]
    dpts = [(c[0] + R * v * m.cos(m.radians(a)), c[1] + R * v * m.sin(m.radians(a)))
            for a, v in zip(range(-90, 270, 60), vals)]
    d.polygon(dpts, outline=WHITE, width=16)
    for p in dpts:
        d.ellipse([p[0] - 9, p[1] - 9, p[0] + 9, p[1] + 9], fill=WHITE)
    save(img, "channel-health-score.png")


for fn in (icon_content_matrix, icon_cs, icon_return, icon_private, icon_oneid, icon_price, icon_channel):
    fn()
print("\n输出目录:", OUT)
