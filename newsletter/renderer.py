"""
renderer.py — Markdown + tokens → HTML de e-mail (tabelas, estilos 100% inline).

Regras do HTML gerado:
  · layout em <table>; espaçamento vertical por padding de <td> (margens de <p> falham no Outlook);
  · nenhuma variável CSS, rgba() ou gradiente — só valores literais vindos dos tokens;
  · um único <style> no <head>, só para o ajuste de celular (@media), que é opcional.
"""

from __future__ import annotations
import datetime
import html as _html
import re

from .i18n import HTML_LANG
from .parser import (
    parse, Heading, Paragraph, Quote, ListBlock, Table, Image, Math, Divider,
)
from .tokens import FONT_STACKS


# ── Helpers ───────────────────────────────────────────────────────────────────

def esc(s: str) -> str:
    return _html.escape(str(s), quote=True)

def multiline(s: str) -> str:
    return esc(s).replace("\r\n", "\n").replace("\n", "<br>")

def css(**kw) -> str:
    return ";".join(f"{k.replace('_', '-')}:{v}" for k, v in kw.items() if v not in (None, ""))

def _px(v) -> str:
    return f"{int(v)}px"

def _em(v) -> str:
    return f"{round(float(v), 3):g}em"

def fam(t: dict, key: str) -> str:
    return FONT_STACKS[t[key]]

def _safe_url(u: str) -> str:
    u = u.strip().replace('"', "%22")
    return u if re.match(r"^(https?:|mailto:|tel:|#|/)", u, re.I) else "#"

def _img_url(u: str) -> str | None:
    u = u.strip().replace('"', "%22")
    return u if re.match(r"^https?://", u, re.I) else None


# ── Inline (negrito, itálico, links…) ─────────────────────────────────────────

_CODE   = re.compile(r"`([^`\n]+)`")
_MATH_B = re.compile(r"(?<!\w)\$\$(.+?)\$\$", re.S)
_MATH_I = re.compile(r"(?<!\w)\$([^\s$][^$]*?)\$")
_LINK   = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_BI     = re.compile(r"\*\*\*(.+?)\*\*\*")
_B      = re.compile(r"\*\*(.+?)\*\*")
_I      = re.compile(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)")
_S      = re.compile(r"~~(.+?)~~")


def _mathml(expr: str, display: str) -> str:
    expr = _html.unescape(expr).strip()
    try:
        from latex2mathml.converter import convert
        return convert(expr, display=display)
    except Exception:
        delim = "$$" if display == "block" else "$"
        return f"<code>{esc(delim + expr + delim)}</code>"


def inline(text: str, t: dict, *, strong: bool = True, link: tuple | None = None) -> str:
    """
    Markdown inline → HTML com estilos dos tokens.
    strong=False: negrito herda a cor do contexto (usado em títulos e cabeçalhos).
    link=(cor, sublinhado): sobrescreve o estilo de link (usado no rodapé).
    """
    link_color, underline = link or (t["link_color"], t["link_underline"])
    strong_css = css(font_weight="700", color=t["strong_color"] if strong else None)
    link_css = css(color=link_color, text_decoration="underline" if underline else "none")
    code_css = css(font_family=fam(t, "font_code"), font_size=_px(t["code_size"]),
                   background_color=t["code_bg"], color=t["code_color"], padding="1px 4px")

    held: list[str] = []

    def hold(h: str) -> str:
        held.append(h)
        return f"\x00{len(held) - 1}\x00"

    def emph(s: str) -> str:
        s = _BI.sub(lambda m: f'<strong style="{strong_css}"><em>{m[1]}</em></strong>', s)
        s = _B.sub(lambda m: f'<strong style="{strong_css}">{m[1]}</strong>', s)
        s = _I.sub(lambda m: f"<em>{m[1]}</em>", s)
        return _S.sub(lambda m: f"<s>{m[1]}</s>", s)

    s = _html.escape(text.replace("\x00", ""), quote=False)
    s = _CODE.sub(lambda m: hold(f'<code style="{code_css}">{m[1]}</code>'), s)
    s = _MATH_B.sub(lambda m: hold(_mathml(m[1], "block")), s)
    s = _MATH_I.sub(lambda m: hold(_mathml(m[1], "inline")), s)
    s = _LINK.sub(lambda m: hold(f'<a href="{_safe_url(m[2])}" style="{link_css}">{emph(m[1])}</a>'), s)
    s = emph(s)
    while "\x00" in s:
        s = re.sub(r"\x00(\d+)\x00", lambda m: held[int(m[1])], s)
    return s


# ── Blocos do corpo: cada um devolve (espaço_acima, espaço_abaixo, html) ───────

def _txt(t: dict, **over) -> str:
    base = dict(font_family=fam(t, "font_body"), font_size=_px(t["text_size"]),
                line_height=t["text_lh"], color=t["text_color"])
    base.update(over)
    return css(**base)

_TBL = 'role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"'


def _paragraph(b: Paragraph, t: dict):
    html = (f'<p style="margin:0;padding:0;{_txt(t)};text-align:{b.align}">'
            f'{inline(b.text, t)}</p>')
    return 0, t["p_after"], html


def _heading(b: Heading, t: dict):
    n = b.level
    p = f"h{n}_"
    style = css(margin="0", padding="0", font_family=fam(t, p + "font"), font_size=_px(t[p + "size"]),
                font_weight=t[p + "weight"], font_style=t[p + "style"], line_height=t[p + "lh"],
                color=t[p + "color"], letter_spacing=_em(t[p + "spacing"]),
                text_transform=t[p + "transform"])
    tag = f"h{n + 1}"      # o <h1> é o título do banner
    inner = f'<{tag} style="{style}">{inline(b.text, t, strong=False)}</{tag}>'
    if n == 1 and t["h1_rule_width"] > 0:
        rule = f'{t["h1_rule_width"]}px solid {t["h1_rule_color"]}'
        inner = (f'<table {_TBL}><tr><td style="border-bottom:{rule};'
                 f'padding:0 0 {_px(t["h1_rule_gap"])}">{inner}</td></tr></table>')
    return t[p + "before"], t[p + "after"], inner


def _quote(b: Quote, t: dict):
    style = css(border_left=f'{t["quote_bar_w"]}px solid {t["quote_bar"]}' if t["quote_bar_w"] else None,
                background_color=t["quote_bg"],
                padding=f'{_px(t["quote_pad_y"])} {_px(t["quote_pad_x"])}',
                **{k: v for k, v in dict(
                    font_family=fam(t, "font_body"), font_size=_px(t["quote_size"]), line_height="1.6",
                    font_style=t["quote_style"], color=t["quote_color"]).items()})
    html = f'<table {_TBL}><tr><td style="{style}">{inline(b.text, t)}</td></tr></table>'
    return t["quote_before"], t["quote_after"], html


def _list(b: ListBlock, t: dict):
    tag = "ol" if b.ordered else "ul"
    style = css(margin="0", padding=f'0 0 0 {_px(t["list_indent"])}', **dict(
        font_family=fam(t, "font_body"), font_size=_px(t["text_size"]),
        line_height=t["text_lh"], color=t["list_marker"]))
    last = len(b.items) - 1
    items = "".join(
        f'<li style="margin:0 0 {_px(0 if i == last else t["list_gap"])};padding:0 0 0 4px;'
        f'color:{t["list_marker"]}"><span style="color:{t["text_color"]}">'
        f'{inline(item, t)}</span></li>'
        for i, item in enumerate(b.items))
    return t["list_before"], t["list_after"], f'<{tag} style="{style}">{items}</{tag}>'


def _table(b: Table, t: dict):
    ncols = max([len(b.headers)] + [len(r) for r in b.rows] + [1])
    aligns = (b.aligns + ["left"] * ncols)[:ncols]
    size = t["table_wide_size"] if ncols >= 4 else t["table_cell_size"]
    bw = t["table_border_w"]
    border = f'{bw}px solid {t["table_border"]}' if bw else "none"
    pad = f'{_px(t["table_pad_y"])} {_px(t["table_pad_x"])}'

    def th(cell, a):
        st = css(background_color=t["table_head_bg"], color=t["table_head_color"],
                 font_family=fam(t, "font_ui"), font_size=_px(t["table_head_size"]), font_weight="700",
                 letter_spacing=_em(t["table_head_spacing"]), text_transform=t["table_head_transform"],
                 padding=pad, text_align=a, line_height="1.4")
        return f'<th align="{a}" style="{st}">{inline(cell, t, strong=False)}</th>'

    def td(cell, a, alt):
        st = css(background_color=t["table_alt_bg"] if alt else t["email_bg"], color=t["text_color"],
                 font_family=fam(t, "font_ui"), font_size=_px(size), padding=pad, text_align=a,
                 border_top=border, line_height="1.4")
        return f'<td align="{a}" style="{st}">{inline(cell, t)}</td>'

    head = ("<tr>" + "".join(th(c, aligns[i]) for i, c in enumerate((b.headers + [""] * ncols)[:ncols]))
            + "</tr>") if b.headers else ""
    body = "".join(
        "<tr>" + "".join(td(c, aligns[i], ri % 2 == 1) for i, c in enumerate((r + [""] * ncols)[:ncols]))
        + "</tr>" for ri, r in enumerate(b.rows))
    html = (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
            f'style="width:100%;border-collapse:collapse;border:{border}">{head}{body}</table>')
    return t["table_before"], t["table_after"], html


def _image(b: Image, t: dict):
    url = _img_url(b.url)
    if not url:
        return 0, 0, ""
    width = t["email_width"] - 2 * t["body_pad_x"]
    style = css(display="block", width="100%", max_width="100%", height="auto", border="0",
                outline="none", text_decoration="none",
                border_radius=_px(t["img_radius"]) if t["img_radius"] else None)
    html = f'<img src="{esc(url)}" alt="{esc(b.alt)}" width="{width}" style="{style}">'
    return t["img_before"], t["img_after"], html


def _math(b: Math, t: dict):
    return 8, 8, f'<div style="text-align:center;{_txt(t)}">{_mathml(esc(b.expr), "block")}</div>'


def _divider(b: Divider, t: dict):
    w = t["divider_weight"]
    html = (f'<table {_TBL}><tr><td height="{w}" style="height:{w}px;line-height:{w}px;font-size:{w}px;'
            f'border-top:{w}px solid {t["divider_color"]}">&nbsp;</td></tr></table>')
    return t["divider_before"], t["divider_after"], html


_RENDERERS = {
    Heading: _heading, Paragraph: _paragraph, Quote: _quote, ListBlock: _list,
    Table: _table, Image: _image, Math: _math, Divider: _divider,
}


def _body(blocks, t: dict) -> str:
    rows, prev_after = [], None
    for b in blocks:
        before, after, html = _RENDERERS[type(b)](b, t)
        if not html:
            continue
        # espaço entre blocos = maior entre "abaixo" do anterior e "acima" do atual (como margens CSS)
        top = 0 if prev_after is None else max(prev_after, before)
        rows.append(f'<tr><td style="padding:{_px(top)} 0 0 0">{html}</td></tr>')
        prev_after = after
    if not rows:
        rows = [f'<tr><td style="{_txt(t, color=t["footer_muted"])}">…</td></tr>']
    pad = f'{_px(t["body_pad_top"])} {_px(t["body_pad_x"])} {_px(t["body_pad_bottom"])}'
    return (f'<td class="px-body" style="background-color:{t["email_bg"]};padding:{pad}">'
            f'<table {_TBL}>{"".join(rows)}</table></td>')


# ── Banner (só o título) ──────────────────────────────────────────────────────

def _banner(t: dict) -> str:
    def row(inner: str, top: int = 0) -> str:
        return (f'<tr><td align="center" style="padding:{_px(top)} 0 0 0;text-align:center">'
                f'{inner}</td></tr>')

    rows = []
    gap = 0
    if t["eyebrow"].strip():
        rows.append(row(
            f'<div style="{css(font_family=fam(t, "font_ui"), font_size=_px(t["banner_eyebrow_size"]), font_weight=t["banner_eyebrow_weight"], color=t["banner_eyebrow_color"], letter_spacing=_em(t["banner_eyebrow_spacing"]), text_transform="uppercase", line_height="1.5")}">'
            f'{esc(t["eyebrow"])}</div>'))
        gap = t["banner_eyebrow_gap"]

    title_style = css(margin="0", padding="0", font_family=fam(t, "banner_title_font"),
                      font_size=_px(t["banner_title_size"]), font_weight=t["banner_title_weight"],
                      font_style=t["banner_title_style"], color=t["banner_title_color"],
                      letter_spacing=_em(t["banner_title_spacing"]),
                      text_transform=t["banner_title_transform"], line_height=t["banner_title_lh"])
    rows.append(row(f'<h1 class="banner-title" style="{title_style}">{esc(t["title"])}</h1>', gap))

    rh = t["banner_rule_height"]
    if rh > 0 and t["banner_rule_width"] > 0:
        rows.append(row(
            f'<table role="presentation" align="center" width="{t["banner_rule_width"]}" cellpadding="0" '
            f'cellspacing="0" border="0" style="width:{_px(t["banner_rule_width"])}"><tr>'
            f'<td height="{rh}" bgcolor="{t["banner_rule_color"]}" style="height:{rh}px;line-height:{rh}px;'
            f'font-size:{rh}px;background-color:{t["banner_rule_color"]}">&nbsp;</td></tr></table>',
            t["banner_rule_gap_top"]))

    if t["tagline"].strip():
        rows.append(row(
            f'<div style="{css(font_family=fam(t, "banner_tagline_font"), font_size=_px(t["banner_tagline_size"]), font_style=t["banner_tagline_style"], color=t["banner_tagline_color"], line_height="1.5")}">'
            f'{esc(t["tagline"])}</div>', t["banner_rule_gap_bottom"]))

    if t["edition"].strip():
        pill = css(background_color=t["banner_edition_bg"], color=t["banner_edition_color"],
                   font_family=fam(t, "font_ui"), font_size=_px(t["banner_edition_size"]),
                   font_weight="700", letter_spacing=_em(t["banner_edition_spacing"]),
                   text_transform="uppercase", padding="7px 14px", line_height="1",
                   border_radius="99px")
        rows.append(row(
            f'<table role="presentation" align="center" cellpadding="0" cellspacing="0" border="0"><tr>'
            f'<td bgcolor="{t["banner_edition_bg"]}" style="{pill}">{esc(t["edition"])}</td></tr></table>',
            t["banner_edition_gap"]))

    pad = f'{_px(t["banner_pad_top"])} 32px {_px(t["banner_pad_bottom"])}'
    return (f'<td class="px-banner" align="center" bgcolor="{t["banner_bg"]}" '
            f'style="background-color:{t["banner_bg"]};padding:{pad};text-align:center">'
            f'<table {_TBL}>{"".join(rows)}</table></td>')


# ── Rodapé ────────────────────────────────────────────────────────────────────

def _footer(t: dict) -> str:
    ui = fam(t, "font_ui")
    strong = t["footer_strong"]
    link_a = (strong, True)

    def row(inner: str, top: int = 0) -> str:
        return (f'<tr><td align="center" style="padding:{_px(top)} 0 0 0;text-align:center">'
                f'{inner}</td></tr>')

    def rule() -> str:
        return row(f'<table {_TBL}><tr><td height="1" style="height:1px;line-height:1px;font-size:1px;'
                   f'border-top:1px solid {t["footer_rule"]}">&nbsp;</td></tr></table>', t["footer_gap"])

    def label(text: str) -> str:
        return (f'<div style="{css(font_family=ui, font_size=_px(t["footer_label_size"]), font_weight="700", color=t["footer_accent"], letter_spacing=_em(t["footer_label_spacing"]), text_transform="uppercase", line_height="1", padding="0 0 12px 0")}">'
                f'{esc(text)}</div>')

    body_css = css(font_family=ui, font_size=_px(t["footer_text_size"]), line_height="1.7", color=t["footer_text"])
    gap = t["footer_gap"]
    rows = []

    # Frase de dúvidas
    if t["invite"].strip():
        rows.append(row(
            f'<div style="{css(font_family=fam(t, "font_title"), font_size=_px(t["footer_invite_size"]), font_style=t["footer_invite_style"], line_height="1.55", color=strong)}">'
            f'{multiline(t["invite"])}</div>'))

    # Contato
    contact = []
    site, mail = t["site_label"].strip(), t["email"].strip()
    if t["center_name"].strip():
        name = esc(t["center_name"])
        if t["site_url"].strip():
            name = f'<a href="{_safe_url(t["site_url"])}" style="color:{strong};text-decoration:none">{name}</a>'
        contact.append(f'<div style="{body_css};color:{strong};font-weight:700">{name}</div>')
    links = []
    if site:
        links.append(f'<a href="{_safe_url(t["site_url"] or "#")}" style="color:{strong};text-decoration:none">{esc(site)}</a>')
    if mail:
        links.append(f'<a href="mailto:{esc(mail)}" style="color:{strong};text-decoration:none">{esc(mail)}</a>')
    if links:
        contact.append(f'<div style="{body_css}">{" &nbsp;·&nbsp; ".join(links)}</div>')
    if contact:
        rows.append(row(label(t["lbl_contact"]) + "".join(contact), gap if rows else 0))

    # Editorial (coluna única; cada linha é um [Nome](link))
    names = [ln.strip() for ln in t["editorial"].splitlines() if ln.strip()]
    if names:
        if rows:
            rows.append(rule())
        lines = "<br>".join(inline(n, t, strong=False, link=link_a) for n in names)
        block = (label(t["lbl_editorial"])
                 + f'<div style="{css(font_family=ui, font_size=_px(t["footer_text_size"]), line_height=t["footer_names_lh"], color=t["footer_text"])}">{lines}</div>')
        if t["method_url"].strip() and t["method_label"].strip():
            block += (f'<div style="padding:10px 0 0 0;font-family:{ui};font-size:{_px(t["footer_method_size"])}">'
                      f'<a href="{_safe_url(t["method_url"])}" style="color:{t["footer_muted"]};'
                      f'text-decoration:underline">{esc(t["method_label"])}</a></div>')
        rows.append(row(block, gap))

    # Logos
    logos = []
    h = t["footer_logo_height"]
    for url_key, link_key, alt_key in (("ceg_logo_url", "ceg_link", "center_name"),
                                       ("unb_logo_url", "unb_link", "unb_name")):
        src = _img_url(t[url_key]) if t["show_logos"] else None
        if src:
            img = (f'<img src="{esc(src)}" alt="{esc(t[alt_key])}" height="{h}" '
                   f'style="display:block;height:{h}px;width:auto;border:0;outline:none">')
            if t[link_key].strip():
                img = f'<a href="{_safe_url(t[link_key])}" style="text-decoration:none;border:0">{img}</a>'
            logos.append(img)
    if logos:
        if rows:
            rows.append(rule())
        sep = (f'<td style="width:1px;border-left:1px solid {t["footer_rule"]};font-size:1px;line-height:1px">'
               f'&nbsp;</td>')
        g = _px(t["footer_logo_gap"])
        cells = [f'<td style="padding:0 {g if len(logos) > 1 and i == 0 else 0} 0 '
                 f'{g if i == 1 else 0}">{img}</td>' for i, img in enumerate(logos)]
        inner = sep.join(cells) if len(cells) > 1 else cells[0]
        rows.append(row(
            f'<table role="presentation" align="center" cellpadding="0" cellspacing="0" border="0">'
            f'<tr>{inner}</tr></table>', gap))

    # Endereço e direitos
    small = lambda size, text, top: row(
        f'<div style="{css(font_family=ui, font_size=_px(size), line_height="1.65", color=t["footer_muted"])}">{multiline(text)}</div>', top)
    if t["address"].strip():
        rows.append(small(t["footer_addr_size"], t["address"], 22 if logos else gap))
    if t["legal"].strip():
        rows.append(small(t["footer_legal_size"], t["legal"].replace("{year}", str(datetime.date.today().year)), 14))

    pad = f'{_px(t["footer_pad_y"])} {_px(t["footer_pad_x"])}'
    return (f'<td class="px-footer" bgcolor="{t["footer_bg"]}" '
            f'style="background-color:{t["footer_bg"]};padding:{pad}">'
            f'<table {_TBL}>{"".join(rows)}</table></td>')


# ── Documento ─────────────────────────────────────────────────────────────────

def _responsive(t: dict) -> str:
    w, m = t["email_width"], t["mobile_pad_x"]
    return (f"@media only screen and (max-width:{w}px){{"
            f".px-body,.px-footer{{padding-left:{m}px!important;padding-right:{m}px!important}}"
            f".px-banner{{padding-left:{m}px!important;padding-right:{m}px!important}}"
            f".banner-title{{font-size:{t['banner_title_size_mobile']}px!important}}}}")


def render(md: str, t: dict) -> str:
    """Documento HTML completo (pronto para abrir no navegador ou ir dentro do .eml)."""
    w = t["email_width"]
    title = esc(t["eml_subject"].strip() or t["title"])
    return (
        f'<!DOCTYPE html>\n<html lang="{HTML_LANG[t["lang"]]}">\n<head>\n'
        f'<meta charset="UTF-8">\n'
        f'<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        f'<meta name="color-scheme" content="light only">\n'
        f'<meta name="supported-color-schemes" content="light only">\n'
        f'<title>{title}</title>\n<style>{_responsive(t)}</style>\n</head>\n'
        f'<body style="margin:0;padding:0;background-color:{t["page_bg"]}">\n'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
        f'bgcolor="{t["page_bg"]}" style="background-color:{t["page_bg"]}"><tr>'
        f'<td align="center" style="padding:{_px(t["page_pad_y"])} 12px">\n'
        f'<table role="presentation" width="{w}" cellpadding="0" cellspacing="0" border="0" '
        f'style="width:100%;max-width:{w}px;background-color:{t["email_bg"]}">\n'
        f'<tr>{_banner(t)}</tr>\n<tr>{_body(parse(md), t)}</tr>\n<tr>{_footer(t)}</tr>\n'
        f'</table>\n</td></tr></table>\n</body>\n</html>\n'
    )


def to_plain(md: str, t: dict) -> str:
    """Versão em texto simples (parte text/plain do .eml)."""
    s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r"\1 (\2)", md)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", s)
    s = re.sub(r"^#{1,6}\s+", "", s, flags=re.M)
    s = re.sub(r"\*\*\*|\*\*|\*|~~|`", "", s).replace("{center}", "").replace("{/center}", "")
    editorial = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", t["editorial"]).strip()
    footer = [t["invite"], t["center_name"], t["site_url"], t["email"], editorial,
              t["address"], t["legal"].replace("{year}", str(datetime.date.today().year))]
    head = "\n".join(x for x in (t["title"], t["tagline"]) if x.strip())
    return head + "\n\n" + s.strip() + "\n\n--\n" + "\n\n".join(x.strip() for x in footer if x.strip()) + "\n"
