from docx import Document
from docx.shared import Pt
import re


def markdown_to_docx(markdown_text, output_path, title="Contract Analysis Report"):
    """
    Converts a markdown-ish LLM output (headers, bold, tables, bullet points)
    into a formatted Word document.
    """
    doc = Document()

    # Title
    doc.add_heading(title, level=0)

    lines = markdown_text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if not line:
            i += 1
            continue

        # Markdown table detection: a line starting with "|"
        if line.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            _add_table_from_markdown(doc, table_lines)
            continue

        # Headers (##, ###, etc.)
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            text = line.lstrip("#").strip()
            doc.add_heading(text, level=min(level, 4))
            i += 1
            continue

        # Bold section headers like **Key takeaways**
        if line.startswith("**") and line.endswith("**") and line.count("**") == 2:
            text = line.strip("*")
            heading = doc.add_paragraph()
            run = heading.add_run(text)
            run.bold = True
            run.font.size = Pt(13)
            i += 1
            continue

        # Numbered or bulleted list items
        if re.match(r"^(\d+\.|-|\*)\s", line):
            text = re.sub(r"^(\d+\.|-|\*)\s", "", line)
            text = _strip_inline_markdown(text)
            doc.add_paragraph(text, style="List Bullet")
            i += 1
            continue

        # Regular paragraph
        text = _strip_inline_markdown(line)
        doc.add_paragraph(text)
        i += 1

    doc.save(output_path)
    print(f"Document saved to: {output_path}")


def _strip_inline_markdown(text):
    """Removes ** bold ** and <br> markers, since python-docx needs separate run styling
    for true bold - for simplicity here we just strip the markers and keep plain text."""
    text = text.replace("<br>", " ")
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    return text


def _add_table_from_markdown(doc, table_lines):
    """
    Converts markdown table lines (| col1 | col2 |) into a real Word table.
    Skips the markdown separator line (|---|---|).
    """
    rows = []
    for line in table_lines:
        # Skip separator rows like |---|---|
        if re.match(r"^\|[\s\-:|]+\|$", line):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        cells = [_strip_inline_markdown(c) for c in cells]
        rows.append(cells)

    if not rows:
        return

    num_cols = len(rows[0])
    table = doc.add_table(rows=1, cols=num_cols)
    table.style = "Light Grid Accent 1"

    # Header row
    for j, cell_text in enumerate(rows[0]):
        table.rows[0].cells[j].text = cell_text

    # Data rows
    for row_data in rows[1:]:
        row_cells = table.add_row().cells
        for j, cell_text in enumerate(row_data):
            if j < len(row_cells):
                row_cells[j].text = cell_text

    doc.add_paragraph()  # spacing after table


if __name__ == "__main__":
    sample_markdown = """**Termination clauses – summary**

| Contract | Trigger | Notice Period |
|---|---|---|
| Contract A | Material breach | 30 days |
| Contract B | Convenience | 90 days |

**Key takeaways**

1. Material breach is the most common trigger.
2. Most contracts allow a 30-day cure period.
"""
    markdown_to_docx(sample_markdown, "test_output.docx")