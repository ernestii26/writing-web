import io
import os
from flask import Flask, request, send_file, render_template
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.units import mm
from reportlab.lib.colors import black, gray

app = Flask(__name__)

# 字體地圖 (範例)
FONT_MAP = {
    "隨峰體": "./fonts/THEPEAKFONTBETA_V0.ttf",
    # 其他字體...
}

# 版面設定
TOP_MARGIN = 20 * mm
BOTTOM_MARGIN = 20 * mm
SIDE_MARGIN = 15 * mm
LINE_THICKNESS = 0.5

@app.route("/")
def index_page():
    """
    主頁：顯示前端表單 (templates/index.html)
    把字體清單傳給模板，讓前端可以顯示 <select> 選單。
    """
    font_list = list(FONT_MAP.keys())
    return render_template("index.html", font_list=font_list)

@app.route("/preview", methods=["GET"])
def preview_pdf():
    """
    預覽PDF：將 PDF 以 inline 方式在 <iframe> 顯示。
    """
    user_text = request.args.get("text", "")
    rows = int(request.args.get("rows", 8))
    cols = int(request.args.get("cols", 10))
    selected_font = request.args.get("fontName", "隨峰體")
    faint_option = request.args.get("faintOption", "second_line_faint")

    pdf_buffer = generate_pdf_in_memory(
        text=user_text,
        rows=rows,
        cols=cols,
        font_name=selected_font,
        faint_option=faint_option
    )
    return send_file(pdf_buffer, mimetype="application/pdf", as_attachment=False)

@app.route("/generate_pdf", methods=["POST"])
def download_pdf():
    """
    下載PDF：以附件的形式回傳給使用者(觸發下載)。
    """
    user_text = request.form.get("text", "")
    rows = int(request.form.get("rows", 8))
    cols = int(request.form.get("cols", 10))
    selected_font = request.form.get("fontName", "隨峰體")
    faint_option = request.form.get("faintOption", "second_line_faint")

    pdf_buffer = generate_pdf_in_memory(
        text=user_text,
        rows=rows,
        cols=cols,
        font_name=selected_font,
        faint_option=faint_option
    )
    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="practice.pdf"
    )

def generate_pdf_in_memory(text, rows, cols, font_name, faint_option):
    """
    核心：把使用者的參數(字體/淡化模式等) 生成 PDF 串流。
    (只用直向 A4，不再處理 landscape)
    """
    # 1) 檢查字體檔
    if font_name not in FONT_MAP:
        raise ValueError(f"無效的字體名稱：{font_name}")
    font_path = FONT_MAP[font_name]
    if not os.path.exists(font_path):
        raise FileNotFoundError(f"找不到字體檔: {font_path}")

    # 2) 註冊字體
    pdfmetrics.registerFont(TTFont(font_name, font_path))

    # 3) 紙張大小(固定 A4)
    page_width, page_height = A4  # 直式A4

    # 4) 建立 BytesIO
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))

    # (a) 上方標題(日期)
    c.setFont(font_name, 12)
    title_y = page_height - TOP_MARGIN + 5
    c.drawRightString(page_width - SIDE_MARGIN - 30, title_y, "日期：__________")

    # (b) 計算格子大小
    usable_width = page_width - 2 * SIDE_MARGIN
    usable_height = page_height - (TOP_MARGIN + BOTTOM_MARGIN)
    max_cell_size_w = usable_width / cols
    max_cell_size_h = usable_height / rows
    cell_size = min(max_cell_size_w, max_cell_size_h)

    text_font_size = cell_size * 0.8

    # (c) 畫外框格線
    start_x = SIDE_MARGIN
    total_grid_height = rows * cell_size
    start_y = page_height - TOP_MARGIN - total_grid_height

    c.setLineWidth(LINE_THICKNESS)
    # 橫線
    for r in range(rows + 1):
        y = start_y + r * cell_size
        c.line(start_x, y, start_x + cols * cell_size, y)
    # 直線
    for cc in range(cols + 1):
        x = start_x + cc * cell_size
        c.line(x, start_y, x, start_y + rows * cell_size)

    # (d) 田字格中心虛線
    c.saveState()
    c.setLineWidth(0.4)
    c.setDash(3, 3)  # 虛線
    c.setStrokeColor(gray)
    for r in range(rows):
        for cc in range(cols):
            x1 = start_x + cc * cell_size
            y1 = start_y + r * cell_size
            x2 = x1 + cell_size
            y2 = y1 + cell_size
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            c.line(cx, y1, cx, y2)   # 垂直虛線
            c.line(x1, cy, x2, cy)   # 水平虛線
    c.restoreState()

    # (e) 填文字 (示範每一行都同樣文字)
    poem_chars = list(text)
    line_texts = [poem_chars[:] for _ in range(rows)]

    # 淡化模式決定顏色的小函式
    def get_fill_color_for_row(row_idx, total_rows):
        """
        - "second_line_faint": 第0行黑色，其餘行灰 (0.5)
        - "gradual_fade": 第0行黑色，之後從0.3到0.9
        """
        if faint_option == "second_line_faint":
            if row_idx == 0:
                return black
            else:
                return 0.5
        elif faint_option == "gradual_fade":
            if row_idx == 0:
                return black
            else:
                base_faint = 0.3
                max_faint = 0.9
                scale = (row_idx - 1) / float(max(total_rows - 1, 1))
                return base_faint + scale * (max_faint - base_faint)
        else:
            return black

    # 繪製
    for row_idx, content in enumerate(line_texts):
        c.setFont(font_name, text_font_size)
        color_val = get_fill_color_for_row(row_idx, rows)
        if isinstance(color_val, float):
            c.setFillGray(color_val)
        else:
            c.setFillColor(color_val)

        for col_idx, ch in enumerate(content):
            if col_idx >= cols:
                break
            cell_cx = start_x + col_idx * cell_size + cell_size / 2
            cell_cy = start_y + (rows - row_idx - 1) * cell_size + cell_size / 2
            c.drawCentredString(cell_cx, cell_cy - text_font_size * 0.3, ch)

    c.save()
    buffer.seek(0)
    return buffer

if __name__ == "__main__":
    app.run(debug=True)
