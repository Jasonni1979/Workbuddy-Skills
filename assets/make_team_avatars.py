#!/usr/bin/env python3
"""生成品牌客户运营专家团头像（5 张，512×512 PNG，品牌色 #185FA5）。

角色隐喻（区别于技能图标：用「人物半身像+职能符号」表达团队成员）：
- 主理人 凯队长：人物 + 指挥枢纽光环
- 数析：人物 + 折线图
- 会运营：人物 + 会员双心
- 种草：人物 + 内容嫩芽
- 渠道官：人物 + 渠道网络盾
"""
import math
import os

from PIL import Image, ImageDraw, ImageFilter

OUT = "/Users/wise01/WorkBuddy/2026-09-05-10-17-28/outputs/avatars"
os.makedirs(OUT, exist_ok=True)

S = 512
BRAND = (24, 95, 165)        # #185FA5
BRAND_DARK = (14, 62, 112)
WHITE = (255, 255, 255)
GOLD = (255, 196, 87)        # 主理人点缀色


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
    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([S * 0.42, -S * 0.34, S * 1.28, S * 0.52], fill=(255, 255, 255, 46))
    glow = glow.filter(ImageFilter.GaussianBlur(48))
    img = Image.alpha_composite(img.convert("RGBA"), glow)
    return img, ImageDraw.Draw(img)


def person(d, cx=256, head_cy=180, head_r=62, body_top=268, body_w=150,
           color=WHITE, outline=None, width=0):
    """简约人物半身像：圆头 + 圆角梯形身。"""
    fill = color
    d.ellipse([cx - head_r, head_cy - head_r, cx + head_r, head_cy + head_r],
              fill=fill, outline=outline, width=width)
    d.rounded_rectangle(
        [cx - body_w, body_top, cx + body_w, body_top + 240],
        radius=body_w * 0.9, fill=fill, outline=outline, width=width)


def save(img, name):
    path = os.path.join(OUT, name)
    img.convert("RGB").save(path, "PNG", optimize=True)
    kb = os.path.getsize(path) / 1024
    print(f"{name:40s} 512x512  {kb:6.1f} KB")


# ---------- 1. 主理人 凯队长：人物 + 指挥枢纽光环 + 金色徽记 ----------
def icon_lead():
    img, d = base_canvas()
    # 外圈指挥光环（虚线感：用多段圆弧）
    for i in range(12):
        a0 = i * 30 + 4
        a1 = i * 30 + 22
        d.arc([70, 70, 442, 442], start=a0, end=a1, fill=WHITE, width=10)
    # 四个枢纽节点（团队四成员方位）
    for ang in (45, 135, 225, 315):
        th = math.radians(ang)
        nx, ny = 256 + 186 * math.cos(th), 256 + 186 * math.sin(th)
        d.ellipse([nx - 22, ny - 22, nx + 22, ny + 22], fill=WHITE)
    # 中心人物
    person(d, cx=256, head_cy=196, head_r=58, body_top=276, body_w=132, color=WHITE)
    # 金色领结徽记（主理人标识）
    d.polygon([(256, 300), (232, 286), (232, 314)], fill=GOLD)
    d.polygon([(256, 300), (280, 286), (280, 314)], fill=GOLD)
    d.ellipse([248, 292, 264, 308], fill=GOLD)
    save(img, "brand-ops-team.png")


# ---------- 2. 数析：人物 + 折线图面板 ----------
def icon_data():
    img, d = base_canvas()
    # 左侧人物
    person(d, cx=170, head_cy=200, head_r=56, body_top=278, body_w=118, color=WHITE)
    # 右侧数据面板
    d.rounded_rectangle([268, 150, 452, 330], radius=20, outline=WHITE, width=14)
    pts = [(292, 296), (330, 258), (366, 276), (400, 214), (432, 184)]
    d.line(pts, fill=WHITE, width=12, joint="curve")
    for p in pts:
        d.ellipse([p[0] - 9, p[1] - 9, p[0] + 9, p[1] + 9], fill=WHITE)
    # 底部基线
    d.line([(288, 310), (436, 310)], fill=WHITE, width=8)
    save(img, "brand-ops-data-analyst.png")


# ---------- 3. 会运营：人物 + 胸前会员心形徽章 + 环绕关系环 ----------
def icon_member():
    img, d = base_canvas()
    person(d, cx=256, head_cy=186, head_r=58, body_top=266, body_w=136, color=WHITE)

    def heart(d, cx, cy, r, color):
        d.ellipse([cx - r, cy - r * 0.9, cx, cy + r * 0.2], fill=color)
        d.ellipse([cx, cy - r * 0.9, cx + r, cy + r * 0.2], fill=color)
        d.polygon([(cx - r * 0.98, cy - r * 0.1), (cx + r * 0.98, cy - r * 0.1),
                   (cx, cy + r * 1.25)], fill=color)

    # 胸前心形徽章（会员资产），品牌蓝心嵌套白心
    heart(d, 256, 330, 52, BRAND)
    heart(d, 256, 330, 34, WHITE)
    # 左右关系环（品牌↔会员双向），避开头部
    d.arc([96, 210, 216, 330], start=120, end=250, fill=WHITE, width=10)
    d.arc([296, 210, 416, 330], start=290, end=60, fill=WHITE, width=10)
    save(img, "brand-ops-member-expert.png")


# ---------- 4. 种草：人物 + 头顶嫩芽 + 身侧星点传播 ----------
def icon_content():
    img, d = base_canvas()
    person(d, cx=256, head_cy=212, head_r=58, body_top=290, body_w=134, color=WHITE)
    # 头顶嫩芽（种草=培育内容）：茎 + 两片对称叶
    d.line([(256, 154), (256, 104)], fill=WHITE, width=12)
    d.pieslice([200, 62, 262, 124], start=180, end=330, fill=WHITE)
    d.pieslice([250, 62, 312, 124], start=210, end=360, fill=WHITE)
    # 身侧传播星点（内容扩散），不再用头顶波纹
    for sx, sy, r in ((120, 180, 12), (96, 250, 8), (392, 180, 12), (416, 250, 8),
                      (140, 330, 7), (372, 330, 7)):
        d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=WHITE)
    save(img, "brand-ops-content-expert.png")


# ---------- 5. 渠道官：人物 + 渠道网络盾 ----------
def icon_channel():
    img, d = base_canvas()
    person(d, cx=210, head_cy=200, head_r=54, body_top=276, body_w=112, color=WHITE)
    # 右侧盾牌（治理守护）
    shield = [(330, 140), (440, 140), (440, 250), (385, 320), (330, 250)]
    d.polygon(shield, outline=WHITE, width=14)
    # 盾内渠道网络：中心节点 + 三渠道节点
    d.ellipse([373, 196, 397, 220], fill=WHITE)
    for nx, ny in ((352, 168), (418, 168), (385, 262)):
        d.line([(385, 208), (nx, ny)], fill=WHITE, width=8)
        d.ellipse([nx - 11, ny - 11, nx + 11, ny + 11], fill=WHITE)
    save(img, "brand-ops-channel-expert.png")


if __name__ == "__main__":
    icon_lead()
    icon_data()
    icon_member()
    icon_content()
    icon_channel()
    print("5 team avatars done")
