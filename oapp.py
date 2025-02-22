import io
import os
from flask import Flask, request, send_file, render_template
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.units import mm
from reportlab.lib.colors import black, gray

app = Flask(__name__)

# ====== 你的字體檔設定 (請改成實際檔名或路徑) ======
FONT_NAME = "SuiFengTi"
FONT_FILE = "THEPEAKFONTBETA_V0.TTF"

# 版面相關
TOP_MARGIN = 20 * mm
BOTTOM_MARGIN = 20 * mm
SIDE_MARGIN = 15 * mm
LINE_THICKNESS = 0.5
FAINT_COLOR = 0.7  # 淡色

@app.route("/")
def index_page():
    """
    主頁：顯示前端表單 (templates/index.html)
    """
    return render_template("index.html")

@app.route("/preview", methods=["GET"])
def preview_pdf():
    """
    預覽用：GET 方式接收參數，在瀏覽器內 inline 顯示 PDF (用 <iframe> 來嵌入)。
    """
    user_text = request.args.get("text", "")
    orientation = request.args.get("orientation", "portrait")
    rows = int(request.args.get("rows", 8))
    cols = int(request.args.get("cols", 10))

    # 生成 PDF，as_attachment=False => inline 顯示
    pdf_buffer = generate_pdf_in_memory(user_text, orientation, rows, cols)

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=False  # 不下載，讓瀏覽器直接在 <iframe> 或新分頁打開
    )

@app.route("/generate_pdf", methods=["POST"])
def download_pdf():
    """
    下載用：POST 方式接收參數，產生 PDF 後當檔案下載。
    """
    user_text = request.form.get("text", "")
    orientation = request.form.get("orientation", "portrait")
    rows = int(request.form.get("rows", 8))
    cols = int(request.form.get("cols", 10))

    pdf_buffer = generate_pdf_in_memory(user_text, orientation, rows, cols)

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,         # 強制當附件下載
        download_name="practice.pdf"
    )

def generate_pdf_in_memory(text, orientation, rows, cols):
    """
    核心：把文字、紙張方向、行數、列數等資訊，動態生產一個 PDF Byte 流。
    """
    # 1) 檢查字體
    if not os.path.exists(FONT_FILE):
        raise FileNotFoundError(f"找不到字體檔: {FONT_FILE}")
    pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_FILE))

    # 2) 設定紙張大小 (直式 or 橫式)
    if orientation == "landscape":
        page_size = landscape(A4)
    else:
        page_size = A4
    page_width, page_height = page_size

    # 3) 建立一個 BytesIO 來暫存 PDF
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=page_size)

    # (a) 先畫上方「日期：______」標題列
    c.setFont(FONT_NAME, 12)
    title_y = page_height - TOP_MARGIN + 5
    c.drawRightString(page_width - SIDE_MARGIN - 30, title_y, "日期：_______")

    # (b) 計算格子大小，避免超出邊緣
    usable_width = page_width - 2*SIDE_MARGIN
    usable_height = page_height - (TOP_MARGIN + BOTTOM_MARGIN)
    max_cell_size_w = usable_width / cols
    max_cell_size_h = usable_height / rows
    cell_size = min(max_cell_size_w, max_cell_size_h)

    # 字體大小 (這裡設定為格子大小的 0.8 倍)
    text_font_size = cell_size * 0.8

    # (c) 繪製外框格線
    start_x = SIDE_MARGIN
    total_grid_height = rows * cell_size
    start_y = page_height - TOP_MARGIN - total_grid_height

    c.setLineWidth(LINE_THICKNESS)
    # 橫線
    for r in range(rows+1):
        y = start_y + r*cell_size
        c.line(start_x, y, start_x + cols*cell_size, y)
    # 直線
    for cc in range(cols+1):
        x = start_x + cc*cell_size
        c.line(x, start_y, x, start_y + rows*cell_size)

    # (d) 田字格中心虛線
    c.saveState()
    c.setLineWidth(0.4)
    c.setDash(3,3)  # 虛線
    c.setStrokeColor(gray)
    for r in range(rows):
        for cc in range(cols):
            x1 = start_x + cc*cell_size
            y1 = start_y + r*cell_size
            x2 = x1 + cell_size
            y2 = y1 + cell_size
            cx = (x1 + x2)/2
            cy = (y1 + y2)/2
            # 垂直虛線
            c.line(cx, y1, cx, y2)
            # 水平虛線
            c.line(x1, cy, x2, cy)
    c.restoreState()

    # (e) 放入文字
    # 這裡簡易示範：第一行黑、第二行淡、之後空白
    poem_chars = list(text)
    line_texts = [poem_chars, poem_chars]  # 前兩行放字
    for _ in range(rows - 2):
        line_texts.append([])              # 後面行空白

    for row_idx, content in enumerate(line_texts):
        if row_idx >= rows:
            break
        # 第一行黑，其餘行淡
        if row_idx == 0:
            c.setFillColor(black)
        else:
            c.setFillGray(FAINT_COLOR)
        c.setFont(FONT_NAME, text_font_size)

        for col_idx, ch in enumerate(content):
            if col_idx >= cols:
                break
            cell_cx = start_x + col_idx*cell_size + cell_size/2
            cell_cy = start_y + (rows - row_idx - 1)*cell_size + cell_size/2
            c.drawCentredString(cell_cx, cell_cy - text_font_size*0.3, ch)

    # (f) 收尾，回傳記憶體檔案
    c.save()
    buffer.seek(0)
    return buffer

# Flask 主程式入口
if __name__ == "__main__":
    app.run(debug=True)
