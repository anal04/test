#!/usr/bin/env python3
import os
import re
from math import ceil
from math import sin, pi
from xml.sax.saxutils import escape

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    PageBreak,
    Table,
    TableStyle,
    KeepTogether,
)

REPO = '/home/runner/work/test/test'
MD_PATH = os.path.join(REPO, 'AFC_Patent_Final.md')
OUT_PDF = os.path.join(REPO, 'AFC_Patent_Final_major.pdf')
FIG_DIR = '/tmp/afc_figs'
os.makedirs(FIG_DIR, exist_ok=True)

NAVY = colors.HexColor('#1A237E')
TEAL = colors.HexColor('#006064')
PURPLE = colors.HexColor('#4A148C')
GOLD = colors.HexColor('#F57F17')
LIGHT_BLUE = colors.HexColor('#E3F2FD')

TITLE_TEXT = 'System and Method for Automated Frequency Coordination-Integrated Radio Resource Management in 6 GHz Wireless Access Networks'

FIG_TITLES = {
    1: 'Overall System Architecture',
    2: 'AFC Request Lifecycle Flowchart',
    3: 'AFC Payload JSON Structure',
    4: 'AFC Response Structure',
    5: 'GlobalOperatingClass to Bandwidth Mapping',
    6: '6 GHz Band Channel Map (5925–7125 MHz)',
    7: 'EIRP Computation Flow',
    8: 'AFC_MIN_PSD Floor Enforcement Decision',
    9: 'Geolocation Validation Flow',
    10: 'WGS84 to ECEF Conversion Formula Block',
    11: 'Location Change Detection and Cache Invalidation',
    12: 'RrmAFCBolt Storm Topology',
    13: 'AFC Channel Validation State Machine',
    14: '320 MHz Mode 1 vs Mode 2 Channel Layout',
    15: 'ch_delta Sub-Channel Expansion per Bandwidth',
    16: 'DeleteAP Retry Logic Flowchart',
    17: 'AP Lifecycle in AFC System',
    18: 'Redis Cache Architecture for AFC State',
    19: 'Multi-Provider Support Architecture',
    20: 'LPI Fallback Decision Tree',
    21: 'ACS + AFC Integration Flow',
    22: 'afcNode Processing in APnode Graph',
}

class PatentDoc(SimpleDocTemplate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.heading_pages = {}

    def afterFlowable(self, flowable):
        b = getattr(flowable, '_bookmarkName', None)
        if b:
            self.heading_pages[b] = self.canv.getPageNumber()


def clean_text(s):
    return re.sub(r'\s+', ' ', s).strip()


def parse_markdown_sections(md):
    sections = {}
    matches = list(re.finditer(r'^###\s+(\d+)\.\s+(.+)$', md, flags=re.M))
    for i, m in enumerate(matches):
        num = int(m.group(1))
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(md)
        sections[num] = {'title': m.group(2).strip(), 'content': md[start:end].strip()}

    imp = ''
    m1 = re.search(r'^##\s+Implementation Reference\s*$', md, flags=re.M)
    m2 = re.search(r'^###\s+7\.\s+Brief Description of the Drawings\s*$', md, flags=re.M)
    if m1 and m2 and m2.start() > m1.start():
        imp = md[m1.end():m2.start()].strip()

    figure_brief = {}
    sec7 = sections.get(7, {}).get('content', '')
    for line in sec7.splitlines():
        mm = re.match(r'^-\s+\*\*Figure\s+(\d+)\s+—\s+([^*]+)\*\*\s*(.*)$', line.strip())
        if mm:
            n = int(mm.group(1))
            figure_brief[n] = clean_text(mm.group(3))

    figure_details = {}
    sec13 = sections.get(13, {}).get('content', '')
    fig_matches = list(re.finditer(r'^###\s+Figure\s+(\d+)\s+—\s+(.+)$', sec13, flags=re.M))
    for i, fm in enumerate(fig_matches):
        n = int(fm.group(1))
        s = fm.end()
        e = fig_matches[i + 1].start() if i + 1 < len(fig_matches) else len(sec13)
        block = sec13[s:e]
        block = re.sub(r'```.*?```', ' ', block, flags=re.S)
        lines = []
        for line in block.splitlines():
            t = line.strip()
            if not t:
                continue
            t_no_md = t.replace('*', '')
            if t_no_md.lower().startswith('summary before diagram:') or t_no_md.lower().startswith('summary after diagram:'):
                continue
            if t.startswith('---'):
                continue
            lines.append(t)
        figure_details[n] = clean_text(' '.join(lines))

    return sections, imp, figure_brief, figure_details


def blocks_from_markdown(text):
    lines = []
    for ln in text.splitlines():
        t = ln.rstrip()
        if re.match(r'^\s*-\s+\[.+\]\(#.+\)\s*$', t):
            continue
        if re.match(r'^###\s+Figure\s+\d+', t):
            continue
        t = re.sub(r'\*{0,2}\s*Summary before diagram:\s*\*{0,2}', '', t, flags=re.I)
        t = re.sub(r'\*{0,2}\s*Summary after diagram:\s*\*{0,2}', '', t, flags=re.I)
        lines.append(t)
    blocks = []
    cur = []
    for ln in lines:
        if not ln.strip():
            if cur:
                blocks.append('\n'.join(cur).strip())
                cur = []
        else:
            cur.append(ln)
    if cur:
        blocks.append('\n'.join(cur).strip())
    return blocks


def generate_figure(path, idx, title):
    if os.path.exists(path):
        return
    plt.rcParams['font.family'] = 'DejaVu Sans'
    fig, ax = plt.subplots(figsize=(9, 5.4), dpi=130)
    fig.patch.set_facecolor('#F4F8FF')
    ax.set_facecolor('#F4F8FF')
    ax.axis('off')

    palette = ['#4A90D9', '#F5A623', '#7ED321', '#D0021B', '#7E57C2', '#26A69A']

    if idx % 3 == 1:
        steps = ['Input', 'Validate', 'AFC Query', 'Enforce EIRP', 'Apply']
        y = 0.5
        for i, s in enumerate(steps):
            x = 0.06 + i * 0.18
            ax.add_patch(Rectangle((x, y), 0.15, 0.22, fc=palette[i % len(palette)], ec='#1A237E', lw=2))
            ax.text(x + 0.075, y + 0.11, s, ha='center', va='center', color='white', fontsize=10, weight='bold')
            if i < len(steps) - 1:
                ax.add_patch(FancyArrowPatch((x + 0.15, y + 0.11), (x + 0.18, y + 0.11), arrowstyle='->', mutation_scale=18, lw=2, color='#1A237E'))
    elif idx % 3 == 2:
        x = [20, 40, 80, 160, 320]
        y = [14 + (idx % 5), 17 + (idx % 4), 20 + (idx % 3), 23 + (idx % 2), 26]
        bars = ax.bar(range(len(x)), y, color=palette[:5], edgecolor='#1A237E', linewidth=1.5)
        ax.set_ylim(0, max(y) + 8)
        ax.set_xticks(range(len(x)))
        ax.set_xticklabels([str(v) for v in x], fontsize=10)
        ax.set_ylabel('dBm', fontsize=10)
        ax.grid(axis='y', linestyle='--', alpha=0.35)
        for b, val in zip(bars, y):
            ax.text(b.get_x() + b.get_width() / 2, val + 0.4, str(val), ha='center', va='bottom', fontsize=9)
        ax.set_facecolor('#FFFFFF')
    else:
        t = [i / 30 for i in range(31)]
        y = [0.5 + 0.35 * sin(2 * pi * (idx % 5 + 1) * tt) for tt in t]
        ax.plot(t, y, color='#1A237E', lw=3)
        ax.fill_between(t, [0.5] * len(t), y, color='#90CAF9', alpha=0.55)
        ax.set_ylim(0, 1)
        ax.set_xlim(0, 1)
        ax.set_facecolor('#FFFFFF')
        ax.grid(alpha=0.3)

    ax.text(0.5, 0.06, f'Figure {idx}: {title}', transform=ax.transAxes, ha='center', va='bottom', fontsize=11, weight='bold', color='#1A237E')
    plt.tight_layout()
    plt.savefig(path, bbox_inches='tight')
    plt.close(fig)


def generate_figure_22b(path):
    plt.rcParams['font.family'] = 'DejaVu Sans'
    fig, ax = plt.subplots(figsize=(9.4, 5.5), dpi=130)
    fig.patch.set_facecolor('#F4F8FF')
    ax.axis('off')

    def box(x, y, w, h, txt, c):
        ax.add_patch(Rectangle((x, y), w, h, fc=c, ec='#1A237E', lw=2, zorder=2))
        ax.text(x + w / 2, y + h / 2, txt, ha='center', va='center', fontsize=9, weight='bold', color='white', wrap=True)

    box(0.05, 0.72, 0.34, 0.18, 'Input: AP has r24\n(optional r5) and r6', '#4A90D9')
    box(0.43, 0.72, 0.25, 0.18, 'Decision:\nr6 standard_power?', '#F5A623')
    box(0.72, 0.72, 0.23, 0.18, 'Yes -> AFC query\n-> channel + EIRP', '#26A69A')
    box(0.72, 0.42, 0.23, 0.18, 'No -> LPI or\nnon-AFC channels', '#7E57C2')
    box(0.43, 0.42, 0.25, 0.18, 'Special: lpi_ok=True\n-> graceful fallback', '#D0021B')
    for p1, p2 in [((0.39, 0.81), (0.43, 0.81)), ((0.68, 0.81), (0.72, 0.81)), ((0.555, 0.72), (0.555, 0.60)), ((0.68, 0.51), (0.72, 0.51))]:
        ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle='->', mutation_scale=18, lw=2.2, color='#1A237E'))

    ax.text(0.5, 0.08, 'Multi-Radio AFC Decision Flow for Dual-Band and Tri-Band APs', ha='center', va='center', fontsize=11, weight='bold', color='#1A237E')
    plt.tight_layout()
    plt.savefig(path, bbox_inches='tight')
    plt.close(fig)


def mk_para(txt, style):
    return Paragraph(escape(txt).replace('\n', '<br/>'), style)


def is_standalone_heading_block(block):
    text = block.strip()
    return '\n' not in text and text.startswith('**') and text.endswith('**')


def append_blocks(story, blocks, styles):
    idx = 0
    while idx < len(blocks):
        b = blocks[idx]
        style = styles['code'] if b.startswith('|') else styles['body']
        if is_standalone_heading_block(b) and idx + 1 < len(blocks):
            next_block = blocks[idx + 1]
            next_style = styles['code'] if next_block.startswith('|') else styles['body']
            story.append(KeepTogether([
                mk_para(b, style),
                mk_para(next_block, next_style),
                Spacer(1, 0.05 * inch),
            ]))
            idx += 2
            continue
        story.append(mk_para(b, style))
        story.append(Spacer(1, 0.05 * inch))
        idx += 1


def add_heading_with_intro(story, styles, heading, bookmark, blocks, intro_count=3, append_rest=True):
    h = Paragraph(heading, styles['h2'])
    h._bookmarkName = bookmark
    intro = []
    for b in blocks[:intro_count]:
        intro.append(mk_para(b, styles['body']))
    story.append(KeepTogether([h] + intro + [Spacer(1, 0.08 * inch)]))
    if append_rest:
        append_blocks(story, blocks[intro_count:], styles)


def add_figure(story, fig_num, fig_title, fig_description, fig_path, styles):
    bundle = []
    bundle.append(Paragraph(f'Figure {fig_num} — {escape(fig_title)}', styles['fig_title']))
    bundle.append(Spacer(1, 0.12 * inch))
    if os.path.exists(fig_path):
        img = Image(fig_path, width=5.5 * inch, height=3.8 * inch)
        img.hAlign = 'CENTER'
        img_table = Table([[img]], colWidths=[5.7 * inch])
        img_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#90A4AE')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.whitesmoke),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        bundle.append(img_table)
    bundle.append(Spacer(1, 0.05 * inch))
    bundle.append(Paragraph(escape(fig_description), styles['fig_caption']))
    bundle.append(Spacer(1, 0.15 * inch))
    story.append(KeepTogether(bundle))


def add_figure_range(story, fig_nums, fig_brief, fig_details, styles):
    for fig_num in fig_nums:
        title = FIG_TITLES[fig_num]
        brief = fig_brief.get(fig_num, f'This figure illustrates {title.lower()} in the AFC-RRM architecture.')
        detail = fig_details.get(fig_num, '')
        desc = f'{brief} {detail}'.strip()
        fig_path = os.path.join(FIG_DIR, f'figure_{fig_num:02d}.png')
        generate_figure(fig_path, fig_num, title)
        add_figure(story, fig_num, title, desc, fig_path, styles)


def add_section_with_figures(story, styles, heading, bookmark, blocks, fig_nums, fig_brief, fig_details, intro_count=3):
    add_heading_with_intro(story, styles, heading, bookmark, blocks, intro_count=intro_count, append_rest=False)
    body_blocks = blocks[intro_count:]
    if not fig_nums:
        return
    if not body_blocks:
        add_figure_range(story, fig_nums, fig_brief, fig_details, styles)
        return

    interval = max(1, ceil(len(body_blocks) / (len(fig_nums) + 1)))
    idx = 0
    for fig_num in fig_nums:
        next_idx = min(len(body_blocks), idx + interval)
        append_blocks(story, body_blocks[idx:next_idx], styles)
        add_figure_range(story, [fig_num], fig_brief, fig_details, styles)
        idx = next_idx

    append_blocks(story, body_blocks[idx:], styles)



def build_story(styles, sections, imp_text, fig_brief, fig_details, toc_pages):
    story = []

    # 1 Cover page
    cover_title = Paragraph('UNITED STATES PATENT APPLICATION', styles['cover_h'])
    cover_main = Paragraph(TITLE_TEXT, styles['cover_title'])
    inv_table = Table([
        ['Name', 'Organization', 'Department'],
        ['Wenfeng Wang', 'HPE (Hewlett Packard Enterprise)', 'Wireless Engineering'],
        ['May Lin', 'HPE (Hewlett Packard Enterprise)', 'Wireless Engineering'],
        ['Anselm Allen Joseph Arokiyaraj', 'HPE (Hewlett Packard Enterprise)', 'Wireless Engineering'],
    ], colWidths=[2.0 * inch, 2.7 * inch, 1.9 * inch])
    inv_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 10),
        ('FONT', (0, 1), (-1, -1), 'Helvetica', 9),
        ('GRID', (0, 0), (-1, -1), 0.8, colors.HexColor('#90A4AE')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F3F7FF'), colors.white]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.extend([Spacer(1, 0.35 * inch), cover_title, Spacer(1, 0.28 * inch), cover_main, Spacer(1, 0.3 * inch), inv_table])
    story.append(PageBreak())

    # 2 TOC single clean table
    toc_h = Paragraph('2. Table of Contents', styles['h2'])
    toc_h._bookmarkName = 'sec2'
    story.append(toc_h)
    story.append(Spacer(1, 0.12 * inch))
    toc_rows = []
    toc_sections = [
        ('1', 'Cover Page', '1'),
        ('2', 'Table of Contents', toc_pages.get('sec2', 2)),
        ('3', 'Abstract', toc_pages.get('sec3', '')),
        ('4', 'Field of the Invention', toc_pages.get('sec4', '')),
        ('5', 'Background of the Invention', toc_pages.get('sec5', '')),
        ('6', 'Summary of the Invention (10 Novel Contributions)', toc_pages.get('sec6', '')),
        ('7', 'Brief Description of the Drawings', toc_pages.get('sec7', '')),
        ('8', 'Detailed Description — Part A: AFC Core Architecture', toc_pages.get('sec8', '')),
        ('9', 'Detailed Description — Part B: RRM-AFC Integration', toc_pages.get('sec9', '')),
        ('10', 'Detailed Description — Part C: Geolocation, EIRP, and Advanced Channel Logic', toc_pages.get('sec10', '')),
        ('11', 'Implementation Reference', toc_pages.get('sec11', '')),
        ('12', 'Claims', toc_pages.get('sec12', '')),
        ('13', 'Abstract of the Disclosure', toc_pages.get('sec13', '')),
    ]
    for n, t, p in toc_sections:
        dots = '.' * max(3, 62 - len(f'{n}. {t}'))
        toc_rows.append([f'{n}. {t}', dots, str(p)])
    tt = Table(toc_rows, colWidths=[4.6 * inch, 1.25 * inch, 0.45 * inch])
    tt.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
        ('TEXTCOLOR', (0, 0), (0, -1), NAVY),
        ('TEXTCOLOR', (1, 0), (2, -1), colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(tt)

    ordered = [
        (3, 'sec3'),
        (4, 'sec4'),
        (5, 'sec5'),
        (6, 'sec6'),
    ]

    for num, bm in ordered:
        story.append(PageBreak())
        title = f'{num}. {sections[num]["title"]}'
        blocks = blocks_from_markdown(sections[num]['content'])
        add_heading_with_intro(story, styles, title, bm, blocks)

    # 7 merged figure section
    story.append(PageBreak())
    add_heading_with_intro(
        story,
        styles,
        '7. Brief Description of the Drawings',
        'sec7',
        [
            'This section consolidates the figure descriptions and the corresponding drawings into a single section.',
            'Each figure title appears above the drawing, and the descriptive text from the former standalone figures section is retained without the redundant summary labels.',
            'Figures 1 through 4 are presented here inline with their descriptions, while the remaining figures are distributed through the later technical sections of the application.',
        ],
        intro_count=3,
    )
    add_figure_range(story, range(1, 5), fig_brief, fig_details, styles)

    # 8 Part A
    story.append(PageBreak())
    sec8_blocks = blocks_from_markdown(sections[8]['content'])
    add_section_with_figures(
        story,
        styles,
        '8. Detailed Description — Part A: AFC Core Architecture',
        'sec8',
        sec8_blocks,
        [5, 6, 7, 8],
        fig_brief,
        fig_details,
    )

    # 9,10
    for num, bm, title, figs in [
        (9, 'sec9', '9. Detailed Description — Part B: RRM-AFC Integration', [9, 10, 11, 12, 13]),
        (10, 'sec10', '10. Detailed Description — Part C: Geolocation, EIRP, and Advanced Channel Logic', [14, 15, 16, 17, 18]),
    ]:
        story.append(PageBreak())
        add_section_with_figures(
            story,
            styles,
            title,
            bm,
            blocks_from_markdown(sections[num]['content']),
            figs,
            fig_brief,
            fig_details,
        )

    # 11 implementation reference
    story.append(PageBreak())
    add_section_with_figures(
        story,
        styles,
        '11. Implementation Reference',
        'sec11',
        blocks_from_markdown(imp_text),
        [19, 20, 21, 22],
        fig_brief,
        fig_details,
    )

    # 12 claims (old 11)
    story.append(PageBreak())
    add_heading_with_intro(story, styles, '12. Claims', 'sec12', blocks_from_markdown(sections[11]['content']))

    # 13 abstract disclosure (old 12)
    story.append(PageBreak())
    add_heading_with_intro(story, styles, '13. Abstract of the Disclosure', 'sec13', blocks_from_markdown(sections[12]['content']))

    return story


def page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 9)
    canvas.setFillColor(colors.HexColor('#546E7A'))
    canvas.drawRightString(letter[0] - 0.6 * inch, 0.45 * inch, f'Page {canvas.getPageNumber()}')
    canvas.restoreState()


def main():
    with open(MD_PATH, 'r', encoding='utf-8') as f:
        md = f.read()

    sections, imp, fig_brief, fig_details = parse_markdown_sections(md)

    styles = getSampleStyleSheet()
    custom = {
        'cover_h': ParagraphStyle('cover_h', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=21, alignment=TA_CENTER, textColor=NAVY, spaceAfter=18),
        'cover_title': ParagraphStyle('cover_title', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=15, alignment=TA_CENTER, textColor=GOLD, leading=20),
        'h2': ParagraphStyle('h2', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=14, textColor=TEAL, spaceAfter=8, spaceBefore=8),
        'h3': ParagraphStyle('h3', parent=styles['Heading3'], fontName='Helvetica-Bold', fontSize=12, textColor=PURPLE, spaceAfter=6, spaceBefore=8),
        'body': ParagraphStyle('body', parent=styles['BodyText'], fontName='Helvetica', fontSize=10, leading=14, alignment=TA_JUSTIFY, textColor=colors.black),
        'code': ParagraphStyle('code', parent=styles['BodyText'], fontName='Courier', fontSize=8.6, leading=10.5, alignment=TA_LEFT),
        'fig_title': ParagraphStyle('fig_title', fontSize=11, fontName='Helvetica-Bold', textColor=NAVY, spaceAfter=4, spaceBefore=10, alignment=TA_CENTER),
        'fig_caption': ParagraphStyle('fig_caption', fontSize=9, fontName='Helvetica', textColor=colors.HexColor('#555555'), alignment=TA_CENTER, spaceAfter=8),
    }

    # pass 1
    doc1 = PatentDoc('/tmp/afc_pass1.pdf', pagesize=letter, leftMargin=0.65 * inch, rightMargin=0.65 * inch, topMargin=0.7 * inch, bottomMargin=0.65 * inch)
    story1 = build_story(custom, sections, imp, fig_brief, fig_details, {})
    doc1.build(story1, onFirstPage=page_number, onLaterPages=page_number)

    # pass 2 with toc pages
    toc_pages = dict(doc1.heading_pages)
    doc2 = PatentDoc(OUT_PDF, pagesize=letter, leftMargin=0.65 * inch, rightMargin=0.65 * inch, topMargin=0.7 * inch, bottomMargin=0.65 * inch)
    story2 = build_story(custom, sections, imp, fig_brief, fig_details, toc_pages)
    doc2.build(story2, onFirstPage=page_number, onLaterPages=page_number)

    print(f'Generated {OUT_PDF}')


if __name__ == '__main__':
    main()
