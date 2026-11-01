"""
Generates a styled, university-formatted HTML version of Review_3_Comprehensive_Project_Report.md
ready for direct browser viewing and 1-click print-to-PDF (Ctrl+P) formatted to 6-8 pages.
Cleans up raw LaTeX code into proper typography and includes KaTeX renderer.
"""
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD_PATH = os.path.join(BASE_DIR, "Review_3_Comprehensive_Project_Report.md")
HTML_PATH = os.path.join(BASE_DIR, "Review_3_Comprehensive_Project_Report.html")

def clean_latex_symbols(text):
    """Replaces raw LaTeX strings with clean, readable scientific typography."""
    # Replace \text{...} with just the content
    text = re.sub(r'\\text\{([^}]+)\}', r'\1', text)
    text = text.replace(r'\$', '$')
    text = text.replace(r'\_', '_')
    replacements = [
        (r'T_{recov}', 'Recovery Time (s)'),
        (r'T_recov', 'Recovery Time (s)'),
        (r'CI_{95}', '95% CI'),
        (r'p_{99}', 'p99'),
        (r'p_{95}', 'p95'),
        (r'p_{50}', 'p50'),
        (r's\^2', 's²'),
        (r'\\times', '×'),
        (r'\\pm', '±'),
        (r'\\le', '≤'),
        (r'\\ge', '≥'),
        (r'\\Delta', 'Δ'),
        (r'\\mu', 'μ'),
        (r'\\sigma', 'σ'),
        (r'\\sum', 'Sum'),
        (r'\\int', 'Integral'),
    ]
    for pattern, repl in replacements:
        text = re.sub(pattern, repl, text)
    return text

def md_table_to_html(match):
    lines = [l.strip() for l in match.group(0).strip().split("\n") if l.strip()]
    if len(lines) < 2:
        return match.group(0)
    
    header_cols = [c.strip() for c in lines[0].split("|")[1:-1]]
    body_lines = lines[2:] if "---" in lines[1] else lines[1:]
    
    html = ['<div class="table-container"><table><thead><tr>']
    for c in header_cols:
        c_clean = clean_latex_symbols(c).replace("$", "")
        html.append(f'<th>{c_clean}</th>')
    html.append('</tr></thead><tbody>')
    
    for r in body_lines:
        cols = [c.strip() for c in r.split("|")[1:-1]]
        html.append('<tr>')
        for c in cols:
            c_fmt = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', c)
            c_fmt = re.sub(r'\*(.*?)\*', r'<em>\1</em>', c_fmt)
            c_fmt = re.sub(r'`(.*?)`', r'<code>\1</code>', c_fmt)
            c_fmt = clean_latex_symbols(c_fmt).replace("$", "")
            html.append(f'<td>{c_fmt}</td>')
        html.append('</tr>')
    html.append('</tbody></table></div>')
    return "\n".join(html)

def convert_md_to_html():
    with open(MD_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Unescape escaped dollar signs for normal currency display
    content = content.replace(r'\$', '$')

    # Clean display math blocks
    content = re.sub(r'\$\$(.*?)\$\$', lambda m: f'<div class="math-block"><strong>{clean_latex_symbols(m.group(1)).replace("$", "")}</strong></div>', content, flags=re.DOTALL)
    
    # Clean inline math
    content = re.sub(r'\$([^\$]+)\$', lambda m: clean_latex_symbols(m.group(1)), content)

    # Process Tables
    table_regex = re.compile(r'(\|[^\n]+\|\n\|[\s\:\-\|]+\|\n(?:\|[^\n]+\|\n?)+)', re.MULTILINE)
    content = table_regex.sub(md_table_to_html, content)

    # Process Headers
    content = re.sub(r'^# (.*?)$', r'<h1 class="doc-title">\1</h1>', content, flags=re.MULTILINE)
    content = re.sub(r'^## (.*?)$', r'<h2 class="section-title">\1</h2>', content, flags=re.MULTILINE)
    content = re.sub(r'^### (.*?)$', r'<h3 class="subsection-title">\1</h3>', content, flags=re.MULTILINE)
    content = re.sub(r'^#### (.*?)$', r'<h4 class="subsubsection-title">\1</h4>', content, flags=re.MULTILINE)

    # Bold and Italics
    content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
    content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)
    content = re.sub(r'`(.*?)`', r'<code>\1</code>', content)

    # Checklists and Lists
    content = re.sub(r'^- \[x\] (.*?)$', r'<li class="checklist-item checked"><span class="check-box">✓</span> \1</li>', content, flags=re.MULTILINE)
    content = re.sub(r'^- (.*?)$', r'<li>\1</li>', content, flags=re.MULTILINE)

    # Code blocks
    content = re.sub(r'```(.*?)```', r'<pre><code>\1</code></pre>', content, flags=re.DOTALL)

    # Dividers
    content = re.sub(r'^---$', r'<hr class="divider">', content, flags=re.MULTILINE)

    # Paragraphs
    paragraphs = content.split("\n\n")
    processed_p = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        if p.startswith("<h") or p.startswith("<div") or p.startswith("<table") or p.startswith("<pre") or p.startswith("<hr") or p.startswith("<li"):
            processed_p.append(p)
        else:
            processed_p.append(f'<p>{p}</p>')

    body_html = "\n\n".join(processed_p)

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Review 3 Comprehensive Project Report - Project P8</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Merriweather:ital,wght@0,300;0,400;0,700;1,300&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
        
        @page {{
            size: A4;
            margin: 18mm 16mm 18mm 16mm;
            @bottom-right {{
                content: counter(page);
                font-family: 'Inter', sans-serif;
                font-size: 8.5pt;
                color: #666;
            }}
        }}

        body {{
            font-family: 'Merriweather', Georgia, serif;
            font-size: 10pt;
            line-height: 1.6;
            color: #1e293b;
            background-color: #f8fafc;
            margin: 0;
            padding: 25px;
        }}

        .report-wrapper {{
            max-width: 900px;
            margin: 0 auto;
            background: #ffffff;
            padding: 45px 60px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.06);
            border-radius: 8px;
        }}

        .doc-title {{
            font-family: 'Inter', sans-serif;
            font-size: 18pt;
            font-weight: 800;
            text-align: center;
            color: #0f172a;
            margin-bottom: 20px;
            letter-spacing: -0.3px;
            line-height: 1.3;
            text-transform: uppercase;
            border-bottom: 3px solid #2563eb;
            padding-bottom: 12px;
        }}

        .section-title {{
            font-family: 'Inter', sans-serif;
            font-size: 12.5pt;
            font-weight: 700;
            color: #1e3a8a;
            border-bottom: 1.5px solid #cbd5e1;
            padding-bottom: 4px;
            margin-top: 28px;
            margin-bottom: 10px;
            page-break-after: avoid;
            text-transform: uppercase;
            letter-spacing: 0.2px;
        }}

        .subsection-title {{
            font-family: 'Inter', sans-serif;
            font-size: 10.5pt;
            font-weight: 600;
            color: #334155;
            margin-top: 18px;
            margin-bottom: 6px;
            page-break-after: avoid;
        }}

        .subsubsection-title {{
            font-family: 'Inter', sans-serif;
            font-size: 9.5pt;
            font-weight: 600;
            color: #475569;
            margin-top: 12px;
            margin-bottom: 4px;
        }}

        p {{
            margin-top: 0;
            margin-bottom: 10px;
            text-align: justify;
            text-justify: inter-word;
        }}

        .table-container {{
            width: 100%;
            overflow-x: auto;
            margin: 14px 0;
            page-break-inside: avoid;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-family: 'Inter', sans-serif;
            font-size: 8.5pt;
            margin: 8px 0;
        }}

        th, td {{
            border: 1px solid #cbd5e1;
            padding: 6px 9px;
            text-align: left;
        }}

        th {{
            background-color: #f1f5f9;
            color: #0f172a;
            font-weight: 600;
        }}

        tr:nth-child(even) {{
            background-color: #f8fafc;
        }}

        code {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 8pt;
            background-color: #f1f5f9;
            padding: 2px 4px;
            border-radius: 4px;
            color: #0f172a;
            border: 1px solid #e2e8f0;
        }}

        pre {{
            background-color: #0f172a;
            color: #f8fafc;
            padding: 12px 16px;
            border-radius: 6px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 8pt;
            line-height: 1.4;
            overflow-x: auto;
            margin: 14px 0;
            page-break-inside: avoid;
        }}

        pre code {{
            background: transparent;
            color: inherit;
            border: none;
            padding: 0;
        }}

        .divider {{
            border: 0;
            height: 1px;
            background: #e2e8f0;
            margin: 20px 0;
        }}

        .math-block {{
            background-color: #f8fafc;
            border-left: 3px solid #2563eb;
            padding: 8px 14px;
            margin: 10px 0;
            font-family: 'JetBrains Mono', monospace;
            font-size: 9pt;
            color: #0f172a;
        }}

        .checklist-item {{
            list-style: none;
            font-family: 'Inter', sans-serif;
            font-size: 9pt;
            margin: 5px 0;
        }}

        .check-box {{
            color: #10b981;
            font-weight: bold;
            margin-right: 6px;
        }}

        .print-btn {{
            position: fixed;
            top: 20px;
            right: 25px;
            background: #2563eb;
            color: #ffffff;
            font-family: 'Inter', sans-serif;
            font-size: 11pt;
            font-weight: 600;
            padding: 9px 16px;
            border-radius: 8px;
            border: none;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
            transition: all 0.2s;
            z-index: 999;
        }}

        .print-btn:hover {{
            background: #1d4ed8;
            transform: translateY(-1px);
        }}

        @media print {{
            body {{
                background-color: #ffffff;
                padding: 0;
            }}
            .report-wrapper {{
                box-shadow: none;
                padding: 0;
                max-width: 100%;
            }}
            .print-btn {{
                display: none;
            }}
            .section-title {{
                page-break-after: avoid;
            }}
            table, pre {{
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>

    <button class="print-btn" onclick="window.print()">🖨️ Print / Save as PDF (Ctrl+P)</button>

    <div class="report-wrapper">
        {body_html}
    </div>

</body>
</html>
"""

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"Report generated successfully: {HTML_PATH}")

if __name__ == "__main__":
    convert_md_to_html()
