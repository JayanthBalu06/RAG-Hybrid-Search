import io
from pathlib import Path

from bs4 import BeautifulSoup
import pdfplumber
import markdown as md_lib


def normalize(filename: str, content: bytes) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return _from_pdf(content)
    elif ext in (".html", ".htm"):
        return _from_html(content)
    elif ext == ".md":
        return _from_markdown(content)
    elif ext == ".txt":
        return content.decode("utf-8", errors="replace").strip()
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def _from_pdf(content: bytes) -> str:
    pages = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text.strip())
    return "\n\n".join(pages)


def _from_html(content: bytes) -> str:
    soup = BeautifulSoup(content, "lxml")
    for tag in soup(["script", "style", "head"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


def _from_markdown(content: bytes) -> str:
    raw = content.decode("utf-8", errors="replace")
    html = md_lib.markdown(raw)
    soup = BeautifulSoup(html, "lxml")
    return soup.get_text(separator="\n", strip=True)
