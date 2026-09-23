"""
PDF Generator for CSP Map Coloring Report
Generates a PDF document based on README.md content using ReportLab,
Windows Tahoma font for Thai language, and pythainlp for line wrapping.
"""

import os
import sys
import io
import re

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from pythainlp import word_tokenize
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# 1. Register Thai Fonts
FONT_REGULAR = r"C:\Windows\Fonts\tahoma.ttf"
FONT_BOLD = r"C:\Windows\Fonts\tahomabd.ttf"

pdfmetrics.registerFont(TTFont('Tahoma', FONT_REGULAR))
pdfmetrics.registerFont(TTFont('Tahoma-Bold', FONT_BOLD))


def th(text: str) -> str:
    """Insert zero-width spaces for smooth Thai line wrapping, preserving HTML tags."""
    if not text:
        return ""
    parts = re.split(r'(<[^>]+>)', text)
    result = []
    for part in parts:
        if part.startswith('<') and part.endswith('>'):
            result.append(part)
        elif part:
            words = word_tokenize(part, engine="newmm")
            result.append("\u200b".join(words))
    return "".join(result)


def generate_graph_image(output_path: str):
    """Generate a clean visual diagram of Australia's map adjacency graph."""
    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=200)

    # Approximate visual positions corresponding to Australia map layout
    pos = {
        'WA': (1.2, 2.5),
        'NT': (2.8, 3.6),
        'SA': (2.9, 2.1),
        'Q': (4.5, 3.4),
        'NSW': (4.6, 2.0),
        'V': (4.3, 0.9),
        'T': (4.5, 0.0)
    }

    edges = [
        ('WA', 'NT'), ('WA', 'SA'),
        ('NT', 'SA'), ('NT', 'Q'),
        ('SA', 'Q'), ('SA', 'NSW'), ('SA', 'V'),
        ('Q', 'NSW'),
        ('NSW', 'V')
    ]

    # Draw edges
    for u, v in edges:
        x_vals = [pos[u][0], pos[v][0]]
        y_vals = [pos[u][1], pos[v][1]]
        ax.plot(x_vals, y_vals, color='#94A3B8', linewidth=2.2, zorder=1)

    # Draw nodes
    # Sample valid colors: WA: Red, NT: Green, SA: Blue, Q: Red, NSW: Green, V: Red, T: Red
    node_colors = {
        'WA': '#EF4444',
        'NT': '#10B981',
        'SA': '#3B82F6',
        'Q': '#EF4444',
        'NSW': '#10B981',
        'V': '#EF4444',
        'T': '#EF4444'
    }

    full_names = {
        'WA': 'Western Australia\n(WA)',
        'NT': 'Northern Territory\n(NT)',
        'SA': 'South Australia\n(SA)',
        'Q': 'Queensland\n(Q)',
        'NSW': 'New South Wales\n(NSW)',
        'V': 'Victoria\n(V)',
        'T': 'Tasmania (T)\n[Island]'
    }

    for node, (x, y) in pos.items():
        circle = plt.Circle((x, y), 0.42, color=node_colors[node], zorder=2, ec='#1E293B', lw=1.5)
        ax.add_patch(circle)
        ax.text(x, y, node, color='white', weight='bold', fontsize=12, ha='center', va='center', zorder=3)
        # Label offset
        offset_y = -0.55 if node != 'T' else -0.52
        if node == 'NT':
            offset_y = 0.52
        elif node == 'Q':
            offset_y = 0.52
        ax.text(x, y + offset_y, full_names[node], color='#1E293B', fontsize=7.5, weight='bold', ha='center', va='center')

    ax.set_xlim(0.2, 5.5)
    ax.set_ylim(-0.7, 4.4)
    ax.axis('off')
    plt.title("Australia Map Adjacency Graph (Constraint Graph)", fontsize=11, fontweight='bold', color='#1E3A8A', pad=12)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches='tight')
    plt.close()


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_header_footer(self, page_count):
        self.saveState()
        self.setFont("Tahoma", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        # Header (page > 1)
        if self._pageNumber > 1:
            self.drawString(36, 805, "CSP Map Coloring | การระบายสีแผนที่ด้วย Constraint Satisfaction Problem")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(36, 800, 559, 800)

        # Footer (all pages)
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(36, 45, 559, 45)

        self.drawString(36, 32, "Constraint Satisfaction Problem (CSP) - Australia Map Coloring")
        page_str = f"หน้า {self._pageNumber} จาก {page_count}"
        self.drawRightString(559, 32, page_str)
        self.restoreState()


def create_csp_pdf(output_pdf_path: str, graph_img_path: str):
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=46,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        fontName='Tahoma-Bold',
        fontSize=17,
        leading=23,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        fontName='Tahoma',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor('#475569'),
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        'H1',
        fontName='Tahoma-Bold',
        fontSize=12,
        leading=17,
        textColor=colors.HexColor('#1E3A8A'),
        spaceBefore=10,
        spaceAfter=5
    )

    h2_style = ParagraphStyle(
        'H2',
        fontName='Tahoma-Bold',
        fontSize=10,
        leading=15,
        textColor=colors.HexColor('#0369A1'),
        spaceBefore=7,
        spaceAfter=3
    )

    body_style = ParagraphStyle(
        'Body',
        fontName='Tahoma',
        fontSize=8.5,
        leading=13,
        textColor=colors.HexColor('#1E293B'),
        spaceAfter=4
    )

    bullet_style = ParagraphStyle(
        'Bullet',
        fontName='Tahoma',
        fontSize=8.5,
        leading=13,
        textColor=colors.HexColor('#1E293B'),
        leftIndent=12,
        spaceAfter=2
    )

    callout_style = ParagraphStyle(
        'Callout',
        fontName='Tahoma',
        fontSize=8.5,
        leading=13,
        textColor=colors.HexColor('#1E3A8A')
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        fontName='Courier',
        fontSize=7.5,
        leading=10.5,
        textColor=colors.HexColor('#0F172A')
    )

    story = []

    # Title Banner
    badge = Paragraph(f"<font color='#2563EB'><b>ARTIFICIAL INTELLIGENCE | CONSTRAINT SATISFACTION PROBLEM</b></font>", subtitle_style)
    title = Paragraph(th("การระบายสีแผนที่ด้วย Constraint Satisfaction Problem (CSP) - Map Coloring"), title_style)
    sub = Paragraph(th("เอกสารสรุปทฤษฎี โครงสร้างปัญหา อัลกอริทึม และการจำลองขั้นตอนตามสไลด์เรียน (Australia Map Coloring)"), subtitle_style)

    story.append(badge)
    story.append(title)
    story.append(sub)
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563EB'), spaceAfter=10))

    # Section 1: Problem Formulation
    story.append(Paragraph(th("1. โจทย์ปัญหาการระบายสีแผนที่ (Problem Formulation)"), h1_style))
    p1 = th("เป้าหมายของการระบายสีแผนที่คือการหาชุดของสีเพื่อระบายให้กับทุกรัฐในประเทศออสเตรเลีย โดยมีเงื่อนไขสำคัญที่สุดคือ:")
    story.append(Paragraph(p1, body_style))

    # Highlight Callout
    callout_text = Paragraph(th("<b>กฎข้อจำกัดหลัก (Fundamental Rule):</b> \"รัฐหรือภูมิภาคที่มีพรมแดนติดกัน จะต้องใช้สีที่ไม่ซ้ำกันเด็ดขาด (Adjacent regions must have different colors)\""), callout_style)
    callout_table = Table([[callout_text]], colWidths=[523])
    callout_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EFF6FF')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#93C5FD')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(callout_table)
    story.append(Spacer(1, 6))

    # Graph Image
    if os.path.exists(graph_img_path):
        img = Image(graph_img_path, width=340, height=204)
        story.append(img)
        story.append(Spacer(1, 6))

    # Section 2: CSP Formulation
    story.append(Paragraph(th("2. โครงสร้าง CSP ของการระบายสี (CSP Formulation)"), h1_style))
    story.append(Paragraph(th("ในเชิงโครงสร้าง ปัญหา Constraint Satisfaction Problem ประกอบด้วย 3 องค์ประกอบหลัก (X, D, C):"), body_style))

    csp_comp_data = [
        [Paragraph(th("<b>องค์ประกอบ</b>"), body_style), Paragraph(th("<b>รายละเอียดในโจทย์ระบายสีแผนที่ออสเตรเลีย</b>"), body_style)],
        [Paragraph(th("<b>ตัวแปร (Variables - X)</b>"), body_style), Paragraph(th("รัฐทั้งหมด 7 รัฐ ได้แก่ WA, NT, SA, Q, NSW, V, และ T (รัฐ Tasmania [T] เป็นเกาะ ไม่มีพรมแดนติดกับรัฐอื่น)"), body_style)],
        [Paragraph(th("<b>โดเมน (Domains - D)</b>"), body_style), Paragraph(th("สีที่สามารถเลือกใช้ระบายได้ 3 สี: {Red, Green, Blue} สำหรับทุกรัฐ"), body_style)],
        [Paragraph(th("<b>ข้อจำกัด (Constraints - C)</b>"), body_style), Paragraph(th("Binary Constraints ในรูป Xi != Xj สำหรับรัฐที่ติดกันทั้ง 9 คู่:<br/>• WA != NT, WA != SA | NT != SA, NT != Q | SA != Q, SA != NSW, SA != V | Q != NSW | NSW != V"), body_style)],
    ]
    t_csp = Table(csp_comp_data, colWidths=[140, 383])
    t_csp.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_csp)
    story.append(Spacer(1, 6))

    # Section 3: Algorithms
    story.append(Paragraph(th("3. อัลกอริทึมที่ใช้ในการระบายสี (Coloring Algorithms)"), h1_style))

    story.append(Paragraph(th("3.1 Backtracking Search (การค้นหาแบบย้อนรอยตามสไลด์ 12–13)"), h2_style))
    story.append(Paragraph(th("ใช้อัลกอริทึม Depth-First Search (DFS) ร่วมกับการย้อนรอย (Backtrack): เมื่อเลือกรัฐที่ยังไม่ระบายสี จะทดลองกำหนดสีและตรวจความขัดแย้งกับรัฐติดกัน (is_consistent) หากขัดแย้งหรือเจอทางตันจะทำการ <b>ถอยกลับ (Backtrack)</b> เพื่อลองสีถัดไป"), body_style))
    story.append(Spacer(1, 4))

    story.append(Paragraph(th("3.2 Minimum Remaining Values (MRV) Heuristic (สไลด์หน้า 5, 13)"), h2_style))
    story.append(Paragraph(th("กลยุทธ์ <b>\"Fail-First\"</b>: เลือกรัฐที่เหลือจำนวนสีที่ถูกต้อง (Legal Values) น้อยที่สุดก่อน เพื่อช่วยตัดกิ่งการค้นหาที่ไม่สำเร็จให้เร็วที่สุด"), body_style))
    story.append(Spacer(1, 4))

    story.append(Paragraph(th("3.3 Forward Checking & การจำลองตามสไลด์หน้า 14–22"), h2_style))
    story.append(Paragraph(th("เมื่อระบายสีให้รัฐใด จะตัดสีนั้นออกจากเพื่อนบ้านทันที หากเพื่อนบ้านใด <b>โดเมนกลายเป็นค่าว่าง (Domain Wipe-out)</b> จะสั่ง Backtrack ทันที"), body_style))
    story.append(Spacer(1, 4))

    # Step by Step Table
    fc_steps = [
        [Paragraph(th("<b>สไลด์</b>"), body_style), Paragraph(th("<b>การระบายสี</b>"), body_style), Paragraph(th("<b>ผลกระทบต่อโดเมนเพื่อนบ้าน</b>"), body_style), Paragraph(th("<b>สถานะ</b>"), body_style)],
        [Paragraph("Slide 14", body_style), Paragraph(th("เริ่มต้น"), body_style), Paragraph(th("ทุกรัฐมีโดเมนเริ่มต้น = [Red, Green, Blue]"), body_style), Paragraph(th("ปกติ"), body_style)],
        [Paragraph("Slide 15", body_style), Paragraph(th("กำหนด <b>WA = Red</b>"), body_style), Paragraph(th("ตัด Red ออกจาก NT, SA -> เหลือ [Green, Blue]"), body_style), Paragraph(th("ผ่าน (OK)"), body_style)],
        [Paragraph("Slide 16", body_style), Paragraph(th("กำหนด <b>Q = Green</b>"), body_style), Paragraph(th("ตัด Green ออกจาก NT, SA (เหลือแค่ [Blue]) และ NSW (เหลือ [Red, Blue])"), body_style), Paragraph(th("ผ่าน (OK)"), body_style)],
        [Paragraph("Slide 17", body_style), Paragraph(th("พยายามกำหนด <b>V = Blue</b>"), body_style), Paragraph(th("ตัด Blue ออกจาก NSW (เหลือ [Red]) และ SA <b>(เหลือ [] ว่างเปล่า!)</b>"), body_style), Paragraph(th("<font color='#DC2626'><b>พบความขัดแย้ง</b></font>"), body_style)],
        [Paragraph("Slide 18-22", body_style), Paragraph(th("<b>Domain Wipe-Out!</b>"), body_style), Paragraph(th("SA ติดกับ WA(Red), Q(Green), V(Blue) ทำให้ <b>SA ไม่มีสีเหลือ</b>"), body_style), Paragraph(th("<font color='#DC2626'><b>Backtrack ทันที!</b></font>"), body_style)],
    ]
    t_fc = Table(fc_steps, colWidths=[60, 110, 260, 93])
    t_fc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F8FAFC')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('BACKGROUND', (0,4), (-1,5), colors.HexColor('#FEF2F2')),
    ]))
    story.append(t_fc)
    story.append(Spacer(1, 6))

    # Section 4: Execution & Results
    story.append(Paragraph(th("4. ผลลัพธ์การรันโปรแกรม (Execution & Results)"), h1_style))
    story.append(Paragraph(th("รันโปรแกรมด้วยคำสั่ง <code>python map_coloring_csp.py</code> โดยได้คำตอบการระบายสี (Valid Solution):"), body_style))

    res_data = [
        [Paragraph(th("<b>รัฐ (State)</b>"), body_style), Paragraph(th("<b>สีที่ได้รับ (Color)</b>"), body_style), Paragraph(th("<b>การตรวจสอบเงื่อนไขพรมแดน</b>"), body_style)],
        [Paragraph("Western Australia (WA)", body_style), Paragraph(th("<font color='#DC2626'><b>Red</b></font>"), body_style), Paragraph(th("ไม่ซ้ำกับ NT(Green), SA(Blue)"), body_style)],
        [Paragraph("Northern Territory (NT)", body_style), Paragraph(th("<font color='#16A34A'><b>Green</b></font>"), body_style), Paragraph(th("ไม่ซ้ำกับ WA(Red), SA(Blue), Q(Red)"), body_style)],
        [Paragraph("South Australia (SA)", body_style), Paragraph(th("<font color='#2563EB'><b>Blue</b></font>"), body_style), Paragraph(th("ไม่ซ้ำกับ WA(Red), NT(Green), Q(Red), NSW(Green), V(Red)"), body_style)],
        [Paragraph("Queensland (Q)", body_style), Paragraph(th("<font color='#DC2626'><b>Red</b></font>"), body_style), Paragraph(th("ไม่ซ้ำกับ NT(Green), SA(Blue), NSW(Green)"), body_style)],
        [Paragraph("New South Wales (NSW)", body_style), Paragraph(th("<font color='#16A34A'><b>Green</b></font>"), body_style), Paragraph(th("ไม่ซ้ำกับ Q(Red), SA(Blue), V(Red)"), body_style)],
        [Paragraph("Victoria (V)", body_style), Paragraph(th("<font color='#DC2626'><b>Red</b></font>"), body_style), Paragraph(th("ไม่ซ้ำกับ SA(Blue), NSW(Green)"), body_style)],
        [Paragraph("Tasmania (T)", body_style), Paragraph(th("<font color='#DC2626'><b>Red</b></font>"), body_style), Paragraph(th("เกาะไม่มีเพื่อนบ้าน (ระบายสีใดก็ได้)"), body_style)],
    ]
    t_res = Table(res_data, colWidths=[140, 110, 273])
    t_res.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_res)
    story.append(Spacer(1, 6))

    # Summary box
    summary_p = Paragraph(th("<b>สรุปผลลัพธ์ (Summary):</b> อัลกอริทึมสามารถระบายสีแผนที่ออสเตรเลียครบทั้ง 7 รัฐโดยใช้เพียง 3 สี (Red, Green, Blue) และเป็นไปตามเงื่อนไขข้อจำกัดทุกประการ (Valid: True, Violations: 0) ตรงตามทฤษฎีและเนื้อหาในสไลด์เรียน 100%"), callout_style)
    summary_box = Table([[summary_p]], colWidths=[523])
    summary_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F0FDF4')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#86EFAC')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(summary_box)

    doc.build(story, canvasmaker=NumberedCanvas)


if __name__ == "__main__":
    out_dir = r"c:\Users\MSI-1\Desktop\Will be burn\ปี4\CSP_Map_Coloring"
    graph_path = os.path.join(out_dir, "australia_map_graph.png")
    pdf_path = os.path.join(out_dir, "CSP_Map_Coloring_Report.pdf")

    print("Generating graph image...")
    generate_graph_image(graph_path)

    print("Generating PDF report...")
    create_csp_pdf(pdf_path, graph_path)

    print(f"PDF successfully generated at: {pdf_path}")
