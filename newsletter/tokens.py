"""
tokens.py — Fonte única de verdade de TUDO que se controla no visual e no conteúdo fixo.

Cada Token tem: chave, grupo, rótulo, valor padrão e tipo. O app Streamlit gera os
controles a partir desta lista; o renderer lê os valores resolvidos (dict plano).

Escopos:
  visual  — aparência (cores, tamanhos, espaços, fontes), igual em todos os idiomas
  common  — conteúdo que não muda de idioma (título, links, logos, editorial…)
  text    — textos fixos por idioma (ver i18n.py); o valor muda conforme o idioma ativo
"""

from __future__ import annotations
import re
from dataclasses import dataclass

from .i18n import LANGS, TEXTS

# Somente fontes padrão de e-mail (nome → pilha CSS)
FONT_STACKS = {
    "Arial":           "Arial, Helvetica, sans-serif",
    "Helvetica":       "Helvetica, Arial, sans-serif",
    "Verdana":         "Verdana, Geneva, sans-serif",
    "Tahoma":          "Tahoma, Geneva, sans-serif",
    "Trebuchet MS":    "'Trebuchet MS', Helvetica, sans-serif",
    "Georgia":         "Georgia, 'Times New Roman', serif",
    "Times New Roman": "'Times New Roman', Times, serif",
    "Courier New":     "'Courier New', Courier, monospace",
}
FONTS = tuple(FONT_STACKS)
WEIGHTS = ("400", "700")
STYLES = ("normal", "italic")
TRANSFORMS = ("none", "uppercase", "capitalize")


@dataclass(frozen=True)
class Token:
    key: str
    group: str
    label: str
    default: object
    kind: str                     # color | int | float | text | area | select | bool
    lo: float | None = None
    hi: float | None = None
    step: float | None = None
    options: tuple = ()
    scope: str = "visual"
    help: str = ""


TOKENS: list[Token] = []


def _t(group, kind, key, label, default, lo=None, hi=None, step=None,
       options=(), scope="visual", help=""):
    TOKENS.append(Token(key, group, label, default, kind, lo, hi, step, options, scope, help))


def _color(g, key, label, default, **kw):  _t(g, "color", key, label, default, **kw)
def _int(g, key, label, default, lo, hi, **kw):  _t(g, "int", key, label, default, lo, hi, 1, **kw)
def _float(g, key, label, default, lo, hi, step=0.05, **kw):  _t(g, "float", key, label, default, lo, hi, step, **kw)
def _sel(g, key, label, default, options, **kw):  _t(g, "select", key, label, default, options=options, **kw)


# ══ Conteúdo por idioma ═══════════════════════════════════════════════════════
G = "Textos do idioma"
_t(G, "text", "eyebrow",       "Linha acima do título", "", scope="text")
_t(G, "text", "tagline",       "Tagline", "", scope="text")
_t(G, "text", "edition",       "Selo da edição", "", scope="text", help="Deixe vazio para omitir o selo.")
_t(G, "area", "invite",        "Frase de dúvidas (rodapé)", "", scope="text")
_t(G, "text", "lbl_contact",   "Rótulo: contato", "", scope="text")
_t(G, "text", "center_name",   "Nome do centro", "", scope="text")
_t(G, "text", "lbl_editorial", "Rótulo: editorial", "", scope="text")
_t(G, "text", "method_label",  "Texto do link da nota metodológica", "", scope="text")
_t(G, "text", "unb_name",      "Nome da universidade (alt do logo)", "", scope="text")
_t(G, "area", "address",       "Endereço", "", scope="text")
_t(G, "area", "legal",         "Direitos autorais", "", scope="text", help="{year} vira o ano atual.")
_t(G, "text", "eml_subject",   "Assunto do .eml", "", scope="text")

# ══ Conteúdo comum ════════════════════════════════════════════════════════════
G = "Conteúdo comum"
_t(G, "text", "title",        "Título (banner)", "GPS Brasil", scope="common")
_t(G, "text", "site_url",     "Site do centro (URL)", "https://estudosglobais.unb.br/", scope="common")
_t(G, "text", "site_label",   "Site do centro (texto)", "estudosglobais.unb.br", scope="common")
_t(G, "text", "email",        "E-mail de contato", "estudosglobais@unb.br", scope="common")
_t(G, "area", "editorial",    "Editorial (um nome por linha)", "", scope="common",
   help="Cada linha é um hiperlink em Markdown: [Nome Sobrenome](https://lattes.cnpq.br/…). "
        "Vazio omite o bloco inteiro.")
_t(G, "text", "method_url",   "URL da nota metodológica", "https://estudosglobais.unb.br/nota-metodologica-gps-brasil/",
   scope="common", help="Vazio omite o link.")
_t(G, "text", "ceg_logo_url", "Logo CEG (URL da imagem)", "https://estudosglobais.unb.br/wp-content/uploads/2026/11/ceg_logotipo.png", scope="common")
_t(G, "text", "ceg_link",     "Logo CEG (link)", "https://estudosglobais.unb.br/", scope="common")
_t(G, "text", "unb_logo_url", "Logo UnB (URL da imagem)", "https://estudosglobais.unb.br/wp-content/uploads/2026/11/unb_wt.png", scope="common")
_t(G, "text", "unb_link",     "Logo UnB (link)", "https://unb.br/", scope="common")

G = "E-mail (.eml)"
_t(G, "text", "eml_from", "De (opcional)", "", scope="common", help="Ex.: CEG <estudosglobais@unb.br>. Vazio deixa o Outlook preencher.")
_t(G, "text", "eml_to",   "Para (opcional)", "", scope="common")

# ══ Visual ════════════════════════════════════════════════════════════════════
G = "Layout"
_color(G, "page_bg",           "Fundo ao redor do e-mail", "#e9ebee")
_int(G,   "page_pad_y",        "Margem vertical (px)", 32, 0, 120)
_int(G,   "email_width",       "Largura do e-mail (px)", 720, 480, 900)
_color(G, "email_bg",          "Fundo do corpo", "#ffffff")
_int(G,   "body_pad_x",        "Margem lateral do corpo (px)", 40, 0, 120)
_int(G,   "body_pad_top",      "Margem superior do corpo (px)", 32, 0, 120)
_int(G,   "body_pad_bottom",   "Margem inferior do corpo (px)", 36, 0, 120)
_int(G,   "mobile_pad_x",      "Margem lateral no celular (px)", 22, 0, 60)

G = "Fontes"
_sel(G, "font_body",  "Corpo e títulos ##/###", "Arial", FONTS)
_sel(G, "font_title", "Título do banner e frase do rodapé", "Georgia", FONTS)
_sel(G, "font_ui",    "Rótulos, tabela e rodapé", "Arial", FONTS)
_sel(G, "font_code",  "Código inline", "Courier New", FONTS)

G = "Banner"
_color(G, "banner_bg",               "Fundo", "#ffffff")
_int(G,   "banner_pad_top",          "Margem superior (px)", 48, 0, 160)
_int(G,   "banner_pad_bottom",       "Margem inferior (px)", 44, 0, 160)
_color(G, "banner_border_color",     "Filete inferior: cor", "#dfe3e8")
_int(G,   "banner_border_w",         "Filete inferior: espessura (px)", 1, 0, 8, help="0 omite o filete.")
_color(G, "banner_eyebrow_color",    "Linha superior: cor", "#6b7178")
_int(G,   "banner_eyebrow_size",     "Linha superior: tamanho (px)", 11, 8, 20)
_float(G, "banner_eyebrow_spacing",  "Linha superior: espaçamento (em)", 0.22, 0.0, 0.6, 0.01)
_sel(G,   "banner_eyebrow_weight",   "Linha superior: peso", "700", WEIGHTS)
_int(G,   "banner_eyebrow_gap",      "Espaço abaixo da linha superior (px)", 18, 0, 60)
_sel(G,   "banner_title_font",       "Título: fonte", "Georgia", FONTS)
_color(G, "banner_title_color",      "Título: cor", "#1a1a1a")
_int(G,   "banner_title_size",       "Título: tamanho (px)", 54, 20, 100)
_int(G,   "banner_title_size_mobile","Título: tamanho no celular (px)", 42, 16, 80)
_sel(G,   "banner_title_weight",     "Título: peso", "700", WEIGHTS)
_sel(G,   "banner_title_style",      "Título: estilo", "normal", STYLES)
_float(G, "banner_title_spacing",    "Título: espaçamento (em)", 0.02, -0.1, 0.5, 0.01)
_sel(G,   "banner_title_transform",  "Título: caixa", "none", TRANSFORMS)
_float(G, "banner_title_lh",         "Título: entrelinha", 1.1, 0.8, 2.0)
_color(G, "banner_rule_color",       "Traço: cor", "#c3c7cc")
_int(G,   "banner_rule_width",       "Traço: largura (px)", 48, 0, 200)
_int(G,   "banner_rule_height",      "Traço: espessura (px)", 2, 0, 8, help="0 omite o traço.")
_int(G,   "banner_rule_gap_top",     "Espaço acima do traço (px)", 20, 0, 60)
_int(G,   "banner_rule_gap_bottom",  "Espaço abaixo do traço (px)", 18, 0, 60)
_sel(G,   "banner_tagline_font",     "Tagline: fonte", "Georgia", FONTS)
_color(G, "banner_tagline_color",    "Tagline: cor", "#6b7178")
_int(G,   "banner_tagline_size",     "Tagline: tamanho (px)", 15, 10, 30)
_sel(G,   "banner_tagline_style",    "Tagline: estilo", "italic", STYLES)
_color(G, "banner_edition_color",    "Selo: cor do texto", "#555b62")
_color(G, "banner_edition_bg",       "Selo: fundo", "#eceef0")
_int(G,   "banner_edition_size",     "Selo: tamanho (px)", 11, 8, 20)
_float(G, "banner_edition_spacing",  "Selo: espaçamento (em)", 0.14, 0.0, 0.5, 0.01)
_int(G,   "banner_edition_gap",      "Espaço acima do selo (px)", 24, 0, 60)

G = "Texto do corpo"
_color(G, "text_color",     "Cor do texto", "#2b2f33")
_int(G,   "text_size",      "Tamanho (px)", 15, 11, 22)
_float(G, "text_lh",        "Entrelinha", 1.65, 1.1, 2.4)
_int(G,   "p_after",        "Espaço após parágrafo (px)", 16, 0, 60)
_color(G, "strong_color",   "Cor do negrito", "#1b1f23")
_color(G, "link_color",     "Cor dos links", "#0168b3")
_t(G, "bool", "link_underline", "Links sublinhados", True)

# Títulos do Markdown: # / ## / ###
_HEADINGS = {
    1: dict(font="Arial", size=12, weight="700", style="normal", transform="uppercase", spacing=0.18,
            lh=1.3, color="#003366", before=36, after=16),
    2: dict(font="Arial", size=22, weight="700", style="normal", transform="none", spacing=0.0,
            lh=1.25, color="#14283c", before=26, after=10),
    3: dict(font="Arial", size=15, weight="400", style="italic", transform="none", spacing=0.0,
            lh=1.4, color="#6b7480", before=18, after=6),
}
for _n, _d in _HEADINGS.items():
    G, p = f"Título {'#' * _n} (nível {_n})", f"h{_n}_"
    _color(G, p + "color",     "Cor", _d["color"])
    _int(G,   p + "size",      "Tamanho (px)", _d["size"], 8, 60)
    _sel(G,   p + "font",      "Fonte", _d["font"], FONTS)
    _sel(G,   p + "weight",    "Peso", _d["weight"], WEIGHTS)
    _sel(G,   p + "style",     "Estilo", _d["style"], STYLES)
    _sel(G,   p + "transform", "Caixa", _d["transform"], TRANSFORMS)
    _float(G, p + "spacing",   "Espaçamento entre letras (em)", _d["spacing"], -0.1, 0.6, 0.01)
    _float(G, p + "lh",        "Entrelinha", _d["lh"], 0.9, 2.4)
    _int(G,   p + "before",    "Espaço acima (px)", _d["before"], 0, 100)
    _int(G,   p + "after",     "Espaço abaixo (px)", _d["after"], 0, 100)
    if _n == 1:
        _color(G, "h1_rule_color", "Filete: cor", "#009ca6")
        _int(G,   "h1_rule_width", "Filete: espessura (px)", 2, 0, 8, help="0 omite o filete.")
        _int(G,   "h1_rule_gap",   "Filete: distância do texto (px)", 10, 0, 40)

G = "Citação"
_color(G, "quote_bg",      "Fundo", "#f3f7fa")
_color(G, "quote_bar",     "Barra lateral: cor", "#009ca6")
_int(G,   "quote_bar_w",   "Barra lateral: largura (px)", 3, 0, 12)
_color(G, "quote_color",   "Cor do texto", "#3d4650")
_int(G,   "quote_size",    "Tamanho (px)", 15, 10, 26)
_sel(G,   "quote_style",   "Estilo", "italic", STYLES)
_int(G,   "quote_pad_y",   "Margem interna vertical (px)", 14, 0, 40)
_int(G,   "quote_pad_x",   "Margem interna horizontal (px)", 18, 0, 60)
_int(G,   "quote_before",  "Espaço acima (px)", 4, 0, 60)
_int(G,   "quote_after",   "Espaço abaixo (px)", 16, 0, 60)

G = "Listas"
_color(G, "list_marker",  "Cor do marcador", "#009ca6")
_int(G,   "list_gap",     "Espaço entre itens (px)", 6, 0, 30)
_int(G,   "list_indent",  "Recuo (px)", 22, 0, 60)
_int(G,   "list_before",  "Espaço acima (px)", 0, 0, 60)
_int(G,   "list_after",   "Espaço abaixo (px)", 16, 0, 60)

G = "Tabela"
_color(G, "table_head_bg",      "Cabeçalho: fundo", "#003366")
_color(G, "table_head_color",   "Cabeçalho: texto", "#ffffff")
_int(G,   "table_head_size",    "Cabeçalho: tamanho (px)", 12, 8, 20)
_float(G, "table_head_spacing", "Cabeçalho: espaçamento (em)", 0.06, 0.0, 0.4, 0.01)
_sel(G,   "table_head_transform","Cabeçalho: caixa", "uppercase", TRANSFORMS)
_int(G,   "table_cell_size",    "Células: tamanho (px)", 13, 9, 20)
_int(G,   "table_wide_size",    "Células: tamanho com 4+ colunas (px)", 12, 8, 20)
_color(G, "table_alt_bg",       "Linhas alternadas: fundo", "#f5f7f9")
_color(G, "table_border",       "Bordas: cor", "#dfe3e8")
_int(G,   "table_border_w",     "Bordas: espessura (px)", 1, 0, 4)
_int(G,   "table_pad_y",        "Margem interna vertical (px)", 9, 0, 30)
_int(G,   "table_pad_x",        "Margem interna horizontal (px)", 12, 0, 30)
_int(G,   "table_before",       "Espaço acima (px)", 6, 0, 60)
_int(G,   "table_after",        "Espaço abaixo (px)", 16, 0, 60)

G = "Código inline"
_color(G, "code_bg",    "Fundo", "#f1f3f5")
_color(G, "code_color", "Cor do texto", "#1b1f23")
_int(G,   "code_size",  "Tamanho (px)", 13, 9, 20)

G = "Imagem"
_int(G, "img_radius", "Cantos arredondados (px)", 0, 0, 24, help="Outlook desktop ignora cantos arredondados.")
_int(G, "img_before", "Espaço acima (px)", 6, 0, 60)
_int(G, "img_after",  "Espaço abaixo (px)", 16, 0, 60)

G = "Divisória"
_color(G, "divider_color",  "Cor", "#dfe3e8")
_int(G,   "divider_weight", "Espessura (px)", 1, 1, 8)
_int(G,   "divider_before", "Espaço acima (px)", 24, 0, 80)
_int(G,   "divider_after",  "Espaço abaixo (px)", 24, 0, 80)

G = "Rodapé"
_color(G, "footer_bg",         "Fundo", "#003366")
_int(G,   "footer_pad_y",      "Margem vertical (px)", 36, 0, 120)
_int(G,   "footer_pad_x",      "Margem lateral (px)", 40, 0, 120)
_color(G, "footer_text",       "Cor do texto", "#d5e1ee")
_color(G, "footer_muted",      "Cor do texto discreto", "#9fb4cb")
_color(G, "footer_strong",     "Cor de destaque e links", "#ffffff")
_color(G, "footer_accent",     "Cor dos rótulos", "#d9d6c3")
_color(G, "footer_rule",       "Cor das divisórias", "#335c85")
_sel(G,   "footer_invite_style","Frase de dúvidas: estilo", "italic", STYLES)
_int(G,   "footer_invite_size","Frase de dúvidas: tamanho (px)", 16, 10, 30)
_int(G,   "footer_label_size", "Rótulos: tamanho (px)", 10, 8, 16)
_float(G, "footer_label_spacing","Rótulos: espaçamento (em)", 0.2, 0.0, 0.5, 0.01)
_int(G,   "footer_text_size",  "Texto: tamanho (px)", 13, 9, 20)
_float(G, "footer_names_lh",   "Editorial: entrelinha", 2.0, 1.2, 3.0)
_int(G,   "footer_method_size","Nota metodológica: tamanho (px)", 11, 8, 18)
_int(G,   "footer_addr_size",  "Endereço: tamanho (px)", 11, 8, 18)
_int(G,   "footer_legal_size", "Direitos: tamanho (px)", 10, 8, 16)
_int(G,   "footer_gap",        "Espaço entre blocos (px)", 26, 0, 80)
_t(G, "bool", "show_logos",    "Mostrar logos CEG | UnB", True)
_int(G,   "footer_logo_height","Logos: altura (px)", 40, 16, 100)
_int(G,   "footer_logo_gap",   "Logos: distância ao filete (px)", 24, 0, 80)


# ══ API ═══════════════════════════════════════════════════════════════════════

BY_KEY = {tk.key: tk for tk in TOKENS}
GROUPS: list[str] = list(dict.fromkeys(tk.group for tk in TOKENS))
_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def default_for(tk: Token, lang: str | None = None):
    if tk.scope == "text":
        return TEXTS[lang or "pt"][tk.key]
    return tk.default


def coerce(tk: Token, value, lang: str | None = None):
    """Valida/normaliza um valor vindo de perfil ou de widget; cai no padrão se inválido."""
    default = default_for(tk, lang)
    try:
        if tk.kind == "color":
            return str(value).lower() if _HEX.match(str(value)) else default
        if tk.kind in ("int", "float"):
            v = float(value)
            v = max(tk.lo, min(tk.hi, v))
            return int(round(v)) if tk.kind == "int" else round(v, 3)
        if tk.kind == "select":
            return value if value in tk.options else default
        if tk.kind == "bool":
            return bool(value)
        return str(value)
    except (TypeError, ValueError):
        return default


def defaults() -> dict:
    """Estado inicial: {'tokens': {chave: valor}, 'texts': {idioma: {chave: valor}}}."""
    return {
        "tokens": {tk.key: tk.default for tk in TOKENS if tk.scope != "text"},
        "texts": {lang: {tk.key: TEXTS[lang][tk.key] for tk in TOKENS if tk.scope == "text"}
                  for lang in LANGS},
    }


def sanitize_profile(data: dict) -> dict:
    """Aceita um perfil (possivelmente parcial/antigo) e devolve só chaves e valores válidos."""
    out = defaults()
    for key, value in (data.get("tokens") or {}).items():
        tk = BY_KEY.get(key)
        if tk and tk.scope != "text":
            out["tokens"][key] = coerce(tk, value)
    for lang, texts in (data.get("texts") or {}).items():
        if lang not in LANGS:
            continue
        for key, value in (texts or {}).items():
            tk = BY_KEY.get(key)
            if tk and tk.scope == "text":
                out["texts"][lang][key] = coerce(tk, value, lang)
    return out


def resolve(state: dict, lang: str) -> dict:
    """Junta tokens visuais/comuns com os textos do idioma ativo em um dict plano."""
    base = defaults()
    t = {**base["tokens"], **state.get("tokens", {})}
    t.update(base["texts"][lang])
    t.update((state.get("texts") or {}).get(lang, {}))
    t["lang"] = lang
    return t
