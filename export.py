import io
import os
import pandas as pd
from flask import send_file
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

EXPORT_DIR = os.path.join("uploads", "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)

def export_csv(content, save_as=None):
    if not content:
        return "No data provided", 400

    if 'table_data' in content:
        df = pd.DataFrame(content['table_data'])
    elif 'chart_data' in content:
        df = pd.DataFrame(content['chart_data'])
    elif 'summary' in content:
        df = pd.DataFrame([{"Summary": content['summary']}])
    else:
        return "No valid data to export", 400

    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)

    if save_as:
        file_path = os.path.join(EXPORT_DIR, save_as)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(output.getvalue())
        return file_path

    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='export.csv'
    )

def export_excel(content, save_as=None):
    if not content:
        return "No data provided", 400

    if 'table_data' in content:
        df = pd.DataFrame(content['table_data'])
    elif 'chart_data' in content:
        df = pd.DataFrame(content['chart_data'])
    elif 'summary' in content:
        df = pd.DataFrame([{"Summary": content['summary']}])
    else:
        return "No valid data to export", 400

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Export')
    output.seek(0)

    if save_as:
        file_path = os.path.join(EXPORT_DIR, save_as)
        with open(file_path, "wb") as f:
            f.write(output.getvalue())
        return file_path

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='export.xlsx'
    )

def export_pdf(content, save_as=None):
    if not content:
        return "No data provided", 400

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    y = height - 50
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Exported Data")
    y -= 30
    p.setFont("Helvetica", 12)

    if 'summary' in content:
        lines = content['summary'].split('\n')
        for line in lines:
            p.drawString(50, y, line)
            y -= 15
            if y < 50:
                p.showPage()
                y = height - 50

    def draw_table(data, y_start):
        col_width = 150
        row_height = 20
        y_pos = y_start
        keys = data[0].keys()

        for idx, col in enumerate(keys):
            p.drawString(50 + idx * col_width, y_pos, col)
        y_pos -= row_height

        for row in data:
            for idx, val in enumerate(row.values()):
                p.drawString(50 + idx * col_width, y_pos, str(val))
            y_pos -= row_height
            if y_pos < 50:
                p.showPage()
                y_pos = height - 50
        return y_pos

    if 'table_data' in content:
        y = draw_table(content['table_data'], y)
    elif 'chart_data' in content:
        y = draw_table(content['chart_data'], y)

    p.save()
    buffer.seek(0)

    if save_as:
        file_path = os.path.join(EXPORT_DIR, save_as)
        with open(file_path, "wb") as f:
            f.write(buffer.getvalue())
        return file_path

    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name='export.pdf'
    )
