from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Cm
import copy

# ── 色盤 ──────────────────────────────────────────────
NAVY      = RGBColor(0x0D, 0x2B, 0x4E)   # 深藍 背景
STEEL     = RGBColor(0x1A, 0x4A, 0x7A)   # 中藍 標題欄
ACCENT    = RGBColor(0xF0, 0xA5, 0x00)   # 金黃 強調
WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
LTGRAY    = RGBColor(0xEC, 0xF0, 0xF4)   # 淺灰 交替行
MIDGRAY   = RGBColor(0xB0, 0xBE, 0xCC)
DARKTEXT  = RGBColor(0x1C, 0x1C, 0x2E)

prs = Presentation()
prs.slide_width  = Inches(13.33)
prs.slide_height = Inches(7.5)

blank_layout = prs.slide_layouts[6]   # 完全空白

# ══════════════════════════════════════════════════════
# 工具函式
# ══════════════════════════════════════════════════════
def solid_fill(shape, color):
    shape.fill.solid()
    shape.fill.fore_color.rgb = color

def add_rect(slide, l, t, w, h, color, line_color=None):
    s = slide.shapes.add_shape(1, Inches(l), Inches(t), Inches(w), Inches(h))
    solid_fill(s, color)
    if line_color:
        s.line.color.rgb = line_color
        s.line.width = Pt(0.5)
    else:
        s.line.fill.background()
    return s

def add_text(slide, text, l, t, w, h,
             size=11, bold=False, color=WHITE,
             align=PP_ALIGN.LEFT, wrap=True, italic=False):
    txb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    txb.word_wrap = wrap
    tf = txb.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    return txb

def add_multiline(slide, lines, l, t, w, h,
                  size=10, color=WHITE, leading=0.28, bold_first=False):
    """lines: list of (text, bold, color_override)"""
    txb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    txb.word_wrap = True
    tf = txb.text_frame
    tf.word_wrap = True
    for i, item in enumerate(lines):
        if isinstance(item, str):
            txt, bld, col = item, False, color
        else:
            txt = item[0]
            bld = item[1] if len(item) > 1 else False
            col = item[2] if len(item) > 2 else color
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_before = Pt(1)
        run = p.add_run()
        run.text = txt
        run.font.size = Pt(size)
        run.font.bold = bld
        run.font.color.rgb = col

# ══════════════════════════════════════════════════════
# SLIDE 1 ── 根本原因分析（第2頁 RCA）
# ══════════════════════════════════════════════════════
s1 = prs.slides.add_slide(blank_layout)

# 全背景
add_rect(s1, 0, 0, 13.33, 7.5, NAVY)

# 頂部標題欄
add_rect(s1, 0, 0, 13.33, 0.85, STEEL)

# 金色左側裝飾條
add_rect(s1, 0, 0, 0.18, 0.85, ACCENT)

# 頁碼標籤
add_rect(s1, 12.5, 0, 0.83, 0.85, ACCENT)
add_text(s1, "01 / 02", 12.5, 0, 0.83, 0.85,
         size=9, bold=True, color=NAVY, align=PP_ALIGN.CENTER)

# 主標題
add_text(s1, "根本原因分析（RCA）— 第2頁重點", 0.25, 0.08, 9.5, 0.65,
         size=19, bold=True, color=WHITE)
add_text(s1, "Drone HING Solder Joint Fracture", 0.25, 0.52, 9.5, 0.38,
         size=10, bold=False, color=MIDGRAY, italic=True)

# ── 三欄卡片 ──────────────────────────────────────────
CARD_TOP  = 1.0
CARD_H    = 5.55
COLS = [
    (0.18,  4.1),   # RC-01
    (4.45,  4.1),   # RC-02
    (8.72,  4.42),  # RC-03 + 5-Why
]

# ── RC-01 卡片 ──
add_rect(s1, 0.18, CARD_TOP, 4.1, CARD_H, STEEL, MIDGRAY)
add_rect(s1, 0.18, CARD_TOP, 4.1, 0.38, ACCENT)
add_text(s1, "RC-01  主因｜製程偏差", 0.28, CARD_TOP+0.02, 3.9, 0.36,
         size=11, bold=True, color=NAVY)

rc01 = [
    ("回焊峰值溫度不足", True, ACCENT),
    ("規格 245±5°C → 實測 238°C（偏低 7°C）", False, WHITE),
    ("液態區間僅 35 sec（規格 45–75 sec）", False, WHITE),
    ("冷卻速率 6.2°C/sec（規格 ≤3°C/sec）", False, WHITE),
    ("", False, WHITE),
    ("影響機制", True, ACCENT),
    ("① 焊料未完全潤濕 → HiP 假焊", False, WHITE),
    ("② 快速凝固 → 粗大 Sn 枝晶，延展性↓", False, WHITE),
    ("③ IMC 層 Cu₆Sn₅ 異常增厚至 8–12 μm", False, WHITE),
    ("   （正常 ≤3 μm）", False, MIDGRAY),
    ("④ 界面脆化 → 晶間斷裂", False, WHITE),
    ("", False, WHITE),
    ("矯正行動", True, ACCENT),
    ("• 峰值溫度調整至 248°C", False, WHITE),
    ("• TAL 延長至 60 sec", False, WHITE),
    ("• 冷卻速率限制 ≤2.5°C/sec", False, WHITE),
    ("• SPI + Profiler 即時監控，Cpk ≥ 1.33", False, WHITE),
]
add_multiline(s1, rc01, 0.28, CARD_TOP+0.44, 3.85, 5.0, size=9.5)

# ── RC-02 卡片 ──
add_rect(s1, 4.45, CARD_TOP, 4.1, CARD_H, STEEL, MIDGRAY)
add_rect(s1, 4.45, CARD_TOP, 4.1, 0.38, ACCENT)
add_text(s1, "RC-02  次因｜CTE 不匹配", 4.55, CARD_TOP+0.02, 3.9, 0.36,
         size=11, bold=True, color=NAVY)

rc02 = [
    ("熱膨脹係數差異", True, ACCENT),
    ("FR-4 PCB  →  14–17 ppm/°C", False, WHITE),
    ("鋁合金機框  →  23 ppm/°C", False, WHITE),
    ("差值 ΔCTE = 6–9 ppm/°C", False, ACCENT),
    ("", False, WHITE),
    ("應力計算", True, ACCENT),
    ("每循環（ΔT=40°C）角落焊點承受", False, WHITE),
    ("剪切應力 ±18 MPa", False, ACCENT),
    ("（角落焊球距中心最遠，應力最大）", False, MIDGRAY),
    ("", False, WHITE),
    ("Coffin-Manson 壽命預測", True, ACCENT),
    ("計算預期壽命 ~900 循環", False, WHITE),
    ("現場首次失效 850 循環  ✓ 高度吻合", False, ACCENT),
    ("", False, WHITE),
    ("矯正行動", True, ACCENT),
    ("• 換用 Rogers 4350B（CTE 11–14）", False, WHITE),
    ("• 角落焊盤 0.45→0.55 mm + Via-in-Pad", False, WHITE),
    ("• HING / 機框間加 Shore A40 矽膠墊", False, WHITE),
]
add_multiline(s1, rc02, 4.55, CARD_TOP+0.44, 3.85, 5.0, size=9.5)

# ── RC-03 + 5-Why 卡片 ──
add_rect(s1, 8.72, CARD_TOP, 4.42, CARD_H, STEEL, MIDGRAY)
add_rect(s1, 8.72, CARD_TOP, 4.42, 0.38, RGBColor(0x7B, 0x22, 0x22))
add_text(s1, "RC-03  促因｜振動耦合", 8.82, CARD_TOP+0.02, 4.2, 0.36,
         size=11, bold=True, color=WHITE)

rc03 = [
    ("振動共振機制", True, ACCENT),
    ("電機 PWM 諧波頻率（80–120 Hz）", False, WHITE),
    ("  ≈ 機臂共振頻率（~95 Hz）  →  共振", False, ACCENT),
    ("振動加速度峰值 12G（規格僅 8G）", False, WHITE),
    ("熱–振動耦合加速裂紋速率 ×2.3", False, WHITE),
    ("", False, WHITE),
    ("矯正行動", True, ACCENT),
    ("• PWM 24 kHz → 32 kHz（迴避共振）", False, WHITE),
    ("• 四角 Underfill 底膠（Loctite 3563）", False, WHITE),
]
add_multiline(s1, rc03, 8.82, CARD_TOP+0.44, 4.22, 2.6, size=9.5)

# 5-Why 子區塊
WHY_TOP = CARD_TOP + 3.18
add_rect(s1, 8.72, WHY_TOP, 4.42, 0.3, RGBColor(0x8B, 0x45, 0x13))
add_text(s1, "5-Why 流程追溯", 8.82, WHY_TOP+0.02, 4.2, 0.28,
         size=10, bold=True, color=WHITE)

whys = [
    ("W1  焊點斷裂 → IMC 界面脆性開裂", False, WHITE),
    ("W2  IMC 過厚 → 峰溫不足＋冷卻過快", False, WHITE),
    ("W3  曲線偏差 → 換板後未重新確認", False, WHITE),
    ("W4  未確認 → ECN 無強制再驗證步驟", False, ACCENT),
    ("W5  流程缺漏 → SOP-SMT-003 版本過舊", False, ACCENT),
    ("", False, WHITE),
    ("根本 → 修訂 ECN 加入 Gate＋更新 SOP", True, RGBColor(0xFF, 0xD7, 0x00)),
]
add_multiline(s1, whys, 8.82, WHY_TOP+0.34, 4.22, 2.6, size=9.2)

# 底部標籤欄
add_rect(s1, 0, 7.18, 13.33, 0.32, RGBColor(0x08, 0x1A, 0x30))
add_text(s1, "FR-DRONE-HING-2026-001  |  Rev 1.0  |  2026-05-19  |  CONFIDENTIAL",
         0.2, 7.19, 13.0, 0.28, size=8, color=MIDGRAY, align=PP_ALIGN.CENTER)

# ══════════════════════════════════════════════════════
# SLIDE 2 ── 矯正行動 & 專業提問（第3頁）
# ══════════════════════════════════════════════════════
s2 = prs.slides.add_slide(blank_layout)
add_rect(s2, 0, 0, 13.33, 7.5, NAVY)
add_rect(s2, 0, 0, 13.33, 0.85, STEEL)
add_rect(s2, 0, 0, 0.18, 0.85, ACCENT)
add_rect(s2, 12.5, 0, 0.83, 0.85, ACCENT)
add_text(s2, "02 / 02", 12.5, 0, 0.83, 0.85,
         size=9, bold=True, color=NAVY, align=PP_ALIGN.CENTER)
add_text(s2, "矯正行動 & 專業技術提問（第3頁重點）", 0.25, 0.08, 9.5, 0.65,
         size=19, bold=True, color=WHITE)
add_text(s2, "Corrective Actions & Professional Q&A", 0.25, 0.52, 9.5, 0.38,
         size=10, bold=False, color=MIDGRAY, italic=True)

# ─── 左半：矯正行動矩陣 ────────────────────────────────
# 標題
add_rect(s2, 0.18, 1.0, 6.1, 0.36, ACCENT)
add_text(s2, "  矯正行動矩陣（Corrective Action Matrix）", 0.18, 1.0, 6.1, 0.36,
         size=11, bold=True, color=NAVY)

# 表格欄頭
THEAD_TOP = 1.38
add_rect(s2, 0.18, THEAD_TOP, 6.1, 0.3, RGBColor(0x1A, 0x4A, 0x7A))
for txt, lft, wid in [("類別", 0.2, 1.0), ("行動項目", 1.22, 3.3), ("負責", 4.54, 0.8), ("期限", 5.36, 0.9)]:
    add_text(s2, txt, lft, THEAD_TOP+0.02, wid, 0.28,
             size=9, bold=True, color=ACCENT, align=PP_ALIGN.CENTER)

rows = [
    ("製程", "峰值溫度 248°C、TAL 60 sec、冷卻 ≤2.5°C/sec", "SMT Eng", "D+7"),
    ("製程", "SPI + Profiler 即時監控 Cpk≥1.33 管控", "QE / MFG", "D+14"),
    ("設計", "PCB 換 Rogers 4350B，焊盤 0.55 mm + Via-in-Pad", "HW Eng", "D+30"),
    ("設計", "HING–機框間 Shore A40 矽膠解耦緩衝墊", "ME Eng", "D+21"),
    ("振動", "PWM 24→32 kHz 迴避機臂 95 Hz 共振", "FW Eng", "D+10"),
    ("振動", "四角 Underfill 底膠（Loctite 3563）", "SMT Eng", "D+14"),
    ("流程", "ECN 增加「爐溫 Profile 再驗證 Gate」", "PE / QA", "D+7"),
    ("流程", "SOP-SMT-003 更新至 Rev.4（BGA-like 要求）", "PE", "D+14"),
    ("圍堵", "隔離庫存 + 全數 X-Ray / AOI 複檢", "QA", "D+0"),
    ("預防", ">800 循環機體自動觸發預防換件警告", "MIS / SW", "D+45"),
]

row_colors = [STEEL, RGBColor(0x12, 0x38, 0x60)]
for i, (cat, action, owner, ddl) in enumerate(rows):
    ry = THEAD_TOP + 0.3 + i * 0.285
    add_rect(s2, 0.18, ry, 6.1, 0.285, row_colors[i % 2])
    cat_col = ACCENT if cat in ("矯正", "設計", "製程") else (
              RGBColor(0x7B,0xD4,0xFF) if cat == "振動" else
              RGBColor(0xFF,0xA5,0xA5) if cat == "圍堵" else
              RGBColor(0xA5,0xFF,0xC0) if cat == "預防" else WHITE)
    add_text(s2, cat,    0.2,  ry+0.03, 1.0,  0.26, size=8.5, bold=True,  color=cat_col, align=PP_ALIGN.CENTER)
    add_text(s2, action, 1.22, ry+0.03, 3.28, 0.26, size=8.5, bold=False, color=WHITE)
    add_text(s2, owner,  4.54, ry+0.03, 0.8,  0.26, size=8,   bold=False, color=MIDGRAY, align=PP_ALIGN.CENTER)
    add_text(s2, ddl,    5.36, ry+0.03, 0.9,  0.26, size=8.5, bold=True,  color=ACCENT,  align=PP_ALIGN.CENTER)

# ─── 右半：10大專業提問 ─────────────────────────────────
add_rect(s2, 6.48, 1.0, 6.67, 0.36, RGBColor(0x7B, 0x22, 0x22))
add_text(s2, "  10 大專業技術提問（Professional Q&A）", 6.48, 1.0, 6.67, 0.36,
         size=11, bold=True, color=WHITE)

qa_groups = [
    ("製程面", RGBColor(0xF0,0xA5,0x00), [
        "Q1  過去6個月回焊 Profile 記錄是否完整？Cpk 值為何？",
        "Q2  IMC 厚度是否有驗收標準？最後截面分析批次為何？",
        "Q3  助焊劑活性在 <240°C 下的潤濕力測試數據？",
    ]),
    ("設計面", RGBColor(0x7B,0xD4,0xFF), [
        "Q4  設計審查是否執行 CTE 計算與 FEA 熱應力仿真？",
        "Q5  角落焊盤尺寸依何標準設計？是否考量應力集中係數 Kt？",
    ]),
    ("可靠度面", RGBColor(0xA5,0xFF,0xC0), [
        "Q6  量產前是否通過 HALT / ATC 驗證？加速因子依據為何？",
        "Q7  振動測試 PSD 規格是否涵蓋 80–120 Hz 實測 12G 加速度？",
    ]),
    ("供應鏈面", RGBColor(0xFF,0xD7,0x00), [
        "Q8  失效批次 SAC305 錫球供應商批號與 CoC 能否追溯？",
        "Q9  ENIG 鍍層厚度是否量測？排除「黑墊」問題？",
    ]),
    ("系統面", RGBColor(0xFF,0xA5,0xA5), [
        "Q10 能否提供失效機體最後10次飛行數據，建立預測維護模型？",
    ]),
]

gy = 1.42
for grp_name, grp_color, qs in qa_groups:
    # 分組標題
    add_rect(s2, 6.48, gy, 6.67, 0.25, RGBColor(0x0A, 0x22, 0x40))
    add_rect(s2, 6.48, gy, 0.12, 0.25, grp_color)
    add_text(s2, f"  {grp_name}", 6.55, gy+0.02, 6.5, 0.23,
             size=9, bold=True, color=grp_color)
    gy += 0.27
    for q in qs:
        add_rect(s2, 6.48, gy, 6.67, 0.3, STEEL)
        add_text(s2, q, 6.6, gy+0.02, 6.48, 0.27, size=8.8, color=WHITE)
        gy += 0.31
    gy += 0.04

# 底部標籤欄
add_rect(s2, 0, 7.18, 13.33, 0.32, RGBColor(0x08, 0x1A, 0x30))
add_text(s2, "FR-DRONE-HING-2026-001  |  Rev 1.0  |  2026-05-19  |  CONFIDENTIAL",
         0.2, 7.19, 13.0, 0.28, size=8, color=MIDGRAY, align=PP_ALIGN.CENTER)

# ══════════════════════════════════════════════════════
prs.save("/home/user/my-project/HING_Failure_Analysis.pptx")
print("Done → HING_Failure_Analysis.pptx")
