# -*- coding: utf-8 -*-
"""
示範：A4 直式 (portrait)，自動計算可用空間，決定 CELL_SIZE。
     讓格子不會超出紙張邊緣。
"""
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4  # 改為直式 A4
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.units import mm
from reportlab.lib.colors import black, gray

# 字體設定
FONT_NAME = "SuiFengTi"
# 請把下面路徑改成你的實際字體路徑
FONT_FILE = "/mnt/c/USERS/USER/APPDATA/LOCAL/MICROSOFT/WINDOWS/FONTS/THEPEAKFONTBETA_V0.TTF"

# A4 直式 (width, height)
PAGE_WIDTH, PAGE_HEIGHT = A4

# 可微調參數
TOP_MARGIN = 20 * mm
BOTTOM_MARGIN = 20 * mm
SIDE_MARGIN = 15 * mm
TITLE_FONT_SIZE = 12

GRID_ROWS = 15          # 總行數 (可依需求調整)
GRID_COLS = 10         # 每行格數
DESIRED_CELL_SIZE = 25 * mm  # 理想的格子大小，如果排不下會自動縮小
CELL_TO_FONT_RATIO = 0.8     # 字體大小與格子大小的比率，(0.8 = 80% of cell_size)

LINE_THICKNESS = 0.5
FAINT_COLOR = 0.7      # 淡字 (0=黑, 1=白)

def draw_title_info(c):
    """
    在 PDF 最上方，畫出「日期：___」欄位 (只留日期)
    """
    c.setFont(FONT_NAME, TITLE_FONT_SIZE)
    title_y = PAGE_HEIGHT - TOP_MARGIN + 5
    c.drawRightString(PAGE_WIDTH - SIDE_MARGIN - 30, title_y, "日期：_____")

def draw_grid_and_text(c, text_lines, cell_size, text_font_size):
    """
    繪製格子(含田字格、中心虛線) + 填入文字。
    """
    # 計算表格左下角座標
    total_grid_height = GRID_ROWS * cell_size
    start_x = SIDE_MARGIN
    start_y = PAGE_HEIGHT - TOP_MARGIN - total_grid_height

    # 1) 畫外框(實線)
    c.setLineWidth(LINE_THICKNESS)
    # 橫線
    for row in range(GRID_ROWS + 1):
        y = start_y + row * cell_size
        c.line(start_x, y, start_x + GRID_COLS * cell_size, y)
    # 直線
    for col in range(GRID_COLS + 1):
        x = start_x + col * cell_size
        c.line(x, start_y, x, start_y + GRID_ROWS * cell_size)

    # 2) 田字格中心線(虛線)
    c.saveState()
    c.setLineWidth(0.4)
    c.setDash(3, 3)  # (線長3, 空3) => 虛線
    c.setStrokeColor(gray)  # 中心線用灰色

    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            x1 = start_x + col * cell_size
            y1 = start_y + row * cell_size
            x2 = x1 + cell_size
            y2 = y1 + cell_size
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            # 垂直虛線
            c.line(cx, y1, cx, y2)
            # 水平虛線
            c.line(x1, cy, x2, cy)

    c.restoreState()

    # 3) 填文字 (第一行黑，其餘行淡)
    for row_idx, line_text in enumerate(text_lines):
        if row_idx == 0:
            c.setFillColor(black)
        else:
            c.setFillGray(FAINT_COLOR)

        c.setFont(FONT_NAME, text_font_size)

        for col_idx, char in enumerate(line_text):
            if col_idx >= GRID_COLS:
                break
            # 田字格中心
            cell_center_x = start_x + col_idx * cell_size + (cell_size / 2)
            cell_center_y = start_y + (GRID_ROWS - row_idx - 1) * cell_size + (cell_size / 2)
            # 繪製字 (略微往上調)
            c.drawCentredString(cell_center_x, cell_center_y - (text_font_size * 0.3), char)

def create_practice_pdf(output_file="practice_suifengti_portrait.pdf"):
    """
    主程式入口：生成 A4 直式的練字紙。
    """
    # 檢查字體檔
    if not os.path.exists(FONT_FILE):
        raise FileNotFoundError(f"找不到字體檔 {FONT_FILE}")

    pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_FILE))

    # ----------------------------
    # 1) 計算「最大可用 cell_size」
    # ----------------------------
    usable_width = PAGE_WIDTH - 2 * SIDE_MARGIN
    usable_height = PAGE_HEIGHT - (TOP_MARGIN + BOTTOM_MARGIN)

    # 讓所有列/行都排得下
    max_cell_size_by_width = usable_width / GRID_COLS
    max_cell_size_by_height = usable_height / GRID_ROWS
    max_cell_size = min(max_cell_size_by_width, max_cell_size_by_height)

    # 如果理想值 DESIRED_CELL_SIZE 太大，就會自動縮小至 max_cell_size
    cell_size = min(DESIRED_CELL_SIZE, max_cell_size)

    # 文字大小：相對於 cell_size
    text_font_size = cell_size * CELL_TO_FONT_RATIO

    # ----------------------------
    # 2) 準備文字
    # ----------------------------
    poem = (
        "青山橫北郭，白水繞東城。"
        "此地一為別，孤蓬萬里征。"
        "浮雲遊子意，落日故人情。"
        "揮手自茲去，蕭蕭班馬鳴。"
    )
    poem_chars = list(poem)
    # 想要：第一行黑，第二行淡，之後幾行空白
    text_lines = [poem_chars for _ in range(GRID_ROWS)]
    # text_lines = [
    #     poem_chars,  # 第一行(黑)
    #     poem_chars,  # 第二行(淡)
    #     poem_chars,          # 第三行(空)
    #     [],          # 第四行(空)
    #     [],          # 第五行(空)
    #     [],          # 第六行(空)
    #     [],          # 第七行(空)
    #     [],          # 第八行(空)
    # ]

    # ----------------------------
    # 3) 開始繪製 PDF
    # ----------------------------
    c = canvas.Canvas(output_file, pagesize=A4)  # A4 直式

    # 標題欄位 (日期)
    draw_title_info(c)
    # 繪製格子 + 文字
    draw_grid_and_text(c, text_lines, cell_size, text_font_size)

    c.save()
    print(f"已成功生成：{output_file}")


if __name__ == "__main__":
    create_practice_pdf()
