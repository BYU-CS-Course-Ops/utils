import json
import pypandoc
from pathlib import Path
from argparse import ArgumentParser
from bs4 import BeautifulSoup
import cssutils

def inline_css(html: str, css: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    sheet = cssutils.parseString(css)

    for rule in sheet:
        if rule.type != rule.STYLE_RULE:
            continue

        selector = rule.selectorText
        try:
            elements = soup.select(selector)
        except Exception:
            continue

        for element in elements:
            existing = element.get("style", "")
            inline_style = cssutils.css.CSSStyleDeclaration(cssText=existing)

            for prop in rule.style:
                inline_style.setProperty(prop.name, prop.value)

            element["style"] = inline_style.cssText

    for tag in soup.find_all("style"):
        tag.decompose()

    return str(soup)

def convert_md_to_html(file_path: Path, css_path: Path) -> str:
    content = file_path.read_text()
    css = css_path.read_text()

    # ✅ Critical: use tex_math_dollars here
    html_body = pypandoc.convert_text(
        content,
        to='html',
        format='markdown+tex_math_dollars'
    )

    # Inline styles only on the body
    inlined_body = inline_css(f"<body>{html_body}</body>", css)

    # ✅ Do NOT run BeautifulSoup on this — keep scripts intact
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <script>
        window.MathJax = {{
          tex: {{
            inlineMath: [['\\$', '\\$']],
            displayMath: [['\\$\\$', '\\$\\$']]
          }},
          svg: {{ fontCache: 'global' }}
        }};
      </script>
      <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    </head>
    {inlined_body}
    </html>
"""

    return full_html

def gradescope_results(html_content: str):
    with open("results.json", "w") as f:
        json.dump({
            "score": 0.0,
            "output": html_content,
            "output_format": "html"
        }, f, indent=2)

def main(file_path: str, css_path: str):
    html = convert_md_to_html(Path(file_path), Path(css_path))
    gradescope_results(html)

def entry():
    parser = ArgumentParser()
    parser.add_argument("--file_path", type=str, required=True)
    parser.add_argument("--css_path", type=str, default="style.css")
    args = parser.parse_args()
    main(args.file_path, args.css_path)

if __name__ == "__main__":
    entry()
