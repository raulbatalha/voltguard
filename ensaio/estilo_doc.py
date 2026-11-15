"""Procedimento de Ensaio e Demonstracao VoltGuard (VG-PE-05 Rev. B)."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table,
                                TableStyle, KeepTogether, PageBreak)

F = "/usr/share/fonts/truetype/liberation/"
for n, f in [("Serif", "LiberationSerif-Regular"), ("Serif-B", "LiberationSerif-Bold"),
             ("Serif-I", "LiberationSerif-Italic"), ("Sans", "LiberationSans-Regular"),
             ("Sans-B", "LiberationSans-Bold")]:
    pdfmetrics.registerFont(TTFont(n, F + f + ".ttf"))
from reportlab.lib.fonts import addMapping
addMapping("Serif", 0, 0, "Serif"); addMapping("Serif", 1, 0, "Serif-B"); addMapping("Serif", 0, 1, "Serif-I")

S = {
    "corpo": ParagraphStyle("corpo", fontName="Serif", fontSize=10.5, leading=14.2, alignment=TA_JUSTIFY, spaceAfter=5),
    "item": ParagraphStyle("item", fontName="Serif", fontSize=10.5, leading=14.2, alignment=TA_JUSTIFY,
                           leftIndent=9 * mm, firstLineIndent=-6 * mm, spaceAfter=3),
    "h1": ParagraphStyle("h1", fontName="Sans-B", fontSize=12, leading=15, spaceBefore=10, spaceAfter=5, keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName="Sans-B", fontSize=10.5, leading=13.5, spaceBefore=7, spaceAfter=3, keepWithNext=1),
    "tab": ParagraphStyle("tab", fontName="Serif", fontSize=9, leading=11),
    "tabc": ParagraphStyle("tabc", fontName="Serif", fontSize=9, leading=11, alignment=TA_CENTER),
    "tabh": ParagraphStyle("tabh", fontName="Sans-B", fontSize=8.5, leading=10.5),
    "cod": ParagraphStyle("cod", fontName="Courier", fontSize=9, leading=11.5, leftIndent=9 * mm,
                          backColor=colors.HexColor("#f2f2f2"), borderPadding=(3, 4, 3, 4), spaceBefore=3, spaceAfter=7),
    "capa1": ParagraphStyle("c1", fontName="Sans-B", fontSize=22, leading=27, alignment=TA_CENTER),
    "capa2": ParagraphStyle("c2", fontName="Sans-B", fontSize=14, leading=18, alignment=TA_CENTER),
    "capa3": ParagraphStyle("c3", fontName="Serif", fontSize=11, leading=15, alignment=TA_CENTER),
}

story = []
P = lambda t, s="corpo": story.append(Paragraph(t, S[s]))
H1 = lambda t: story.append(Paragraph(t, S["h1"]))
H2 = lambda t: story.append(Paragraph(t, S["h2"]))
I = lambda n, t: story.append(Paragraph(f"{n}&nbsp;&nbsp;{t}", S["item"]))
COD = lambda t: story.append(Paragraph(t.replace("\n", "<br/>").replace(" ", "&nbsp;"), S["cod"]))


def TAB(cab, linhas, larg, altura=None, centro=()):
    dados = [[Paragraph(c, S["tabh"]) for c in cab]]
    for l in linhas:
        dados.append([Paragraph(str(c), S["tabc"] if j in centro else S["tab"]) for j, c in enumerate(l)])
    t = Table(dados, colWidths=[w * mm for w in larg], rowHeights=None if altura is None else [None] + [altura * mm] * len(linhas),
              repeatRows=1)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e3e3e3")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    story.append(t)
    story.append(Spacer(1, 5))


def ESPACO(h=4): story.append(Spacer(1, h))

# ================================ PAGINACAO ================================
class Doc(BaseDocTemplate):
    def __init__(self, fn):
        super().__init__(fn, pagesize=A4, leftMargin=25 * mm, rightMargin=20 * mm, topMargin=25 * mm, bottomMargin=22 * mm,
                         title=TITULO_PDF, author="Projeto VoltGuard")
        fr = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="f")
        self.addPageTemplates([PageTemplate(id="p", frames=[fr], onPage=self.moldura)])

    def moldura(self, c, d):
        if d.page == 1: return
        c.saveState()
        c.setFont("Sans", 8)
        W, H = A4
        c.line(25 * mm, H - 18 * mm, W - 20 * mm, H - 18 * mm)
        c.drawString(25 * mm, H - 16 * mm, TITULO_CAB)
        c.drawRightString(W - 20 * mm, H - 16 * mm, CODIGO_CAB)
        c.line(25 * mm, 15 * mm, W - 20 * mm, 15 * mm)
        c.drawRightString(W - 20 * mm, 11 * mm, f"Página {d.page}")
        c.restoreState()


