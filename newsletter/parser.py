"""
parser.py — Markdown → lista plana de blocos.

Títulos: #, ## e ### (níveis mais profundos valem como ###). Cada nível tem seu
próprio estilo nos tokens — não há mais detecção automática de hierarquia.

Sintaxe suportada:
  # / ## / ###           título nível 1 / 2 / 3
  **negrito** *itálico* ***ambos*** ~~tachado~~ `código` [texto](url)
  ![alt](url)            imagem (URL http/https)
  > citação              (linhas seguidas viram um bloco)
  - item / * item        lista com marcador      1. item   lista numerada
  | a | b |              tabela (linha |---|:--:| define cabeçalho e alinhamento)
  {center}...{/center}   parágrafo centralizado
  ---                    divisória
  $x$ / $$x$$            LaTeX (precisa de latex2mathml; senão aparece como código)
O texto inline (negrito, links…) é interpretado pelo renderer, que conhece os tokens.
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List, Union


@dataclass
class Heading:
    level: int
    text: str

@dataclass
class Paragraph:
    text: str
    align: str = "left"

@dataclass
class Quote:
    text: str

@dataclass
class ListBlock:
    ordered: bool
    items: List[str] = field(default_factory=list)

@dataclass
class Table:
    headers: List[str]
    rows: List[List[str]]
    aligns: List[str]            # "left" | "center" | "right" por coluna

@dataclass
class Image:
    url: str
    alt: str = ""

@dataclass
class Math:
    expr: str

@dataclass
class Divider:
    pass

Block = Union[Heading, Paragraph, Quote, ListBlock, Table, Image, Math, Divider]

_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_IMAGE   = re.compile(r"^!\[([^\]]*)\]\(([^)\s]+)\)\s*$")
_TABLE   = re.compile(r"^\|.+\|\s*$")
_OL      = re.compile(r"^\d+\.\s+(.+)")
_UL      = re.compile(r"^[-*]\s+(.+)")
_QUOTE   = re.compile(r"^>\s?(.*)")
_CENTER  = re.compile(r"^\{center\}(.*)\{/center\}$", re.DOTALL)
_RULES   = ("---", "***", "___")


def _cells(line: str) -> List[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]

def _is_sep(line: str) -> bool:
    cells = [c for c in _cells(line) if c]
    return bool(cells) and all(re.fullmatch(r":?-+:?", c) for c in cells)

def _align(cell: str) -> str:
    if cell.startswith(":") and cell.endswith(":"):
        return "center"
    return "right" if cell.endswith(":") else "left"

def _starts_block(s: str) -> bool:
    return bool(
        not s or _HEADING.match(s) or _IMAGE.match(s) or _QUOTE.match(s) or _UL.match(s)
        or _OL.match(s) or _TABLE.match(s) or _CENTER.match(s) or s in _RULES or s.startswith("$$")
    )


def parse(text: str) -> List[Block]:
    lines = text.splitlines()
    blocks: List[Block] = []
    i = 0
    while i < len(lines):
        s = lines[i].strip()

        if not s:
            i += 1
            continue

        m = _HEADING.match(s)
        if m:
            blocks.append(Heading(level=min(len(m.group(1)), 3), text=m.group(2)))
            i += 1
            continue

        if s in _RULES:
            blocks.append(Divider())
            i += 1
            continue

        m = _IMAGE.match(s)
        if m:
            blocks.append(Image(alt=m.group(1), url=m.group(2)))
            i += 1
            continue

        if s.startswith("$$"):
            inner = s[2:]
            if inner.endswith("$$") and len(inner) >= 2:
                expr = inner[:-2]
            else:
                parts = [inner] if inner else []
                i += 1
                while i < len(lines):
                    ln = lines[i].strip()
                    if ln.endswith("$$"):
                        parts.append(ln[:-2])
                        break
                    parts.append(ln)
                    i += 1
                expr = "\n".join(parts)
            blocks.append(Math(expr=expr))
            i += 1
            continue

        if _TABLE.match(s):
            rows = []
            while i < len(lines) and _TABLE.match(lines[i].strip()):
                rows.append(lines[i].strip())
                i += 1
            if len(rows) >= 2 and _is_sep(rows[1]):
                headers = _cells(rows[0])
                aligns = [_align(c) for c in _cells(rows[1])]
                body = rows[2:]
            else:
                headers, aligns = [], []
                body = [r for r in rows if not _is_sep(r)]
            blocks.append(Table(headers=headers, rows=[_cells(r) for r in body], aligns=aligns))
            continue

        if _QUOTE.match(s):
            parts = []
            while i < len(lines) and _QUOTE.match(lines[i].strip()):
                parts.append(_QUOTE.match(lines[i].strip()).group(1))
                i += 1
            blocks.append(Quote(text=" ".join(p for p in parts if p)))
            continue

        for regex, ordered in ((_UL, False), (_OL, True)):
            if regex.match(s):
                items = []
                while i < len(lines) and regex.match(lines[i].strip()):
                    items.append(regex.match(lines[i].strip()).group(1))
                    i += 1
                blocks.append(ListBlock(ordered=ordered, items=items))
                break
        else:
            m = _CENTER.match(s)
            if m:
                blocks.append(Paragraph(text=m.group(1), align="center"))
                i += 1
                continue

            parts = [s]
            i += 1
            while i < len(lines) and not _starts_block(lines[i].strip()):
                parts.append(lines[i].strip())
                i += 1
            blocks.append(Paragraph(text=" ".join(parts)))
            continue
        # bloco de lista tratado no for/break acima
    return blocks
