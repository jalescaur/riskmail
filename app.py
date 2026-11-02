"""
app.py — GPS Brasil · editor da newsletter do CEG-UnB.

Rodar:  streamlit run app.py

Barra lateral: idioma, perfis e TODOS os tokens (gerados a partir de newsletter/tokens.py).
Área principal: Markdown à esquerda, preview à direita e exportação em .html e .eml.
"""

from __future__ import annotations
import re
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from newsletter import tokens as tk
from newsletter.eml import build_eml
from newsletter.i18n import LANGS
from newsletter.profiles import PROFILES_DIR, delete_profile, list_profiles, load_profile, save_profile
from newsletter.renderer import render, to_plain

ROOT = Path(__file__).parent
CONTENT_DIR = ROOT / "content"

st.set_page_config(page_title="GPS Brasil · Editor", page_icon="📰", layout="wide")


# ── Estado ────────────────────────────────────────────────────────────────────
# Chaves: tok_<token> (visual/comum) · txt_<idioma>_<token> (textos) · md_<idioma> (corpo)

def _sample(lang: str) -> str:
    path = CONTENT_DIR / f"exemplo_{lang}.md"
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _apply_state(state: dict) -> None:
    for key, value in state["tokens"].items():
        st.session_state[f"tok_{key}"] = value
    for lang, texts in state["texts"].items():
        for key, value in texts.items():
            st.session_state[f"txt_{lang}_{key}"] = value


def _collect() -> dict:
    return {
        "tokens": {k: st.session_state[f"tok_{k}"] for k in tk.defaults()["tokens"]},
        "texts": {lang: {k: st.session_state[f"txt_{lang}_{k}"] for k in tk.defaults()["texts"][lang]}
                  for lang in LANGS},
    }


if "initialised" not in st.session_state:
    _apply_state(tk.defaults())
    for _lang in LANGS:
        st.session_state[f"md_{_lang}"] = _sample(_lang)
    st.session_state["initialised"] = True

# O Streamlit descarta o estado de widgets que não foram desenhados nesta execução
# (ex.: textos de outro idioma). Reatribuir mantém tudo vivo ao trocar de idioma.
for _k in [k for k in st.session_state if k.startswith(("tok_", "txt_", "md_"))]:
    st.session_state[_k] = st.session_state[_k]


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "newsletter"


# ── Controles gerados a partir dos tokens ─────────────────────────────────────

def _widget(tok: tk.Token, key: str, box) -> None:
    kw = dict(key=key, help=tok.help or None)
    if tok.kind == "color":
        box.color_picker(tok.label, **kw)
    elif tok.kind == "int":
        box.number_input(tok.label, min_value=int(tok.lo), max_value=int(tok.hi), step=1, **kw)
    elif tok.kind == "float":
        box.number_input(tok.label, min_value=float(tok.lo), max_value=float(tok.hi),
                         step=float(tok.step), format="%.2f", **kw)
    elif tok.kind == "select":
        box.selectbox(tok.label, tok.options, **kw)
    elif tok.kind == "bool":
        box.toggle(tok.label, **kw)
    elif tok.kind == "area":
        box.text_area(tok.label, height=96, **kw)
    else:
        box.text_input(tok.label, **kw)


def _group_controls(group: str, lang: str) -> None:
    cols = st.columns(2)
    n = 0
    for tok in (t for t in tk.TOKENS if t.group == group):
        key = f"txt_{lang}_{tok.key}" if tok.scope == "text" else f"tok_{tok.key}"
        if tok.kind in ("text", "area"):
            _widget(tok, key, st)
            n = 0
        else:
            _widget(tok, key, cols[n % 2])
            n += 1


# ── Barra lateral ─────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 📰 GPS Brasil · CEG-UnB")
    lang = st.radio("Idioma da edição", list(LANGS), format_func=LANGS.get, horizontal=True, key="lang")

    with st.expander("💾 Perfis (aparência e textos)"):
        names = list_profiles()
        if names:
            chosen = st.selectbox("Perfil salvo", names, key="profile_sel")
            c1, c2 = st.columns(2)
            c1.button("Carregar", use_container_width=True,
                      on_click=lambda: _apply_state(load_profile(st.session_state.profile_sel)))
            c2.button("Excluir", use_container_width=True,
                      on_click=lambda: delete_profile(st.session_state.profile_sel))
        else:
            st.caption("Nenhum perfil salvo ainda.")
        new_name = st.text_input("Nome do perfil", placeholder="ex.: padrão-ceg", key="profile_new")
        if st.button("Salvar perfil atual", use_container_width=True):
            try:
                save_profile(new_name, _collect())
                st.success(f"Perfil salvo em {PROFILES_DIR.name}/")
            except ValueError as e:
                st.warning(str(e))
        st.button("Restaurar padrões", use_container_width=True,
                  on_click=lambda: _apply_state(tk.defaults()),
                  help="Volta todos os tokens e textos aos valores originais (não mexe no Markdown).")

    for group in tk.GROUPS:
        label = f"{group} ({LANGS[lang]})" if group == "Textos do idioma" else group
        with st.expander(label, expanded=group == "Textos do idioma"):
            _group_controls(group, lang)


# ── Principal ─────────────────────────────────────────────────────────────────

state = _collect()
t = tk.resolve(state, lang)
md = st.session_state.get(f"md_{lang}", "")

st.markdown(f"## Newsletter · {LANGS[lang]}")
tab_editor, tab_guide = st.tabs(["✏️ Editor", "📖 Guia de Markdown"])

with tab_editor:
    col_md, col_preview = st.columns([2, 3], gap="large")

    with col_md:
        st.markdown("##### Conteúdo (Markdown)")
        st.text_area("Markdown", key=f"md_{lang}", height=640, label_visibility="collapsed")
        b1, b2 = st.columns(2)
        b1.button("Resetar para o exemplo", use_container_width=True,
                  on_click=lambda: st.session_state.update({f"md_{lang}": _sample(lang)}))
        b2.button("Limpar", use_container_width=True,
                  on_click=lambda: st.session_state.update({f"md_{lang}": ""}))

    html = render(md, t)

    with col_preview:
        head, mode = st.columns([3, 2])
        head.markdown("##### Preview")
        view = mode.radio("Tela", ["Computador", "Celular"], horizontal=True, label_visibility="collapsed")
        width = t["email_width"] + 24 if view == "Computador" else 390
        if hasattr(st, "iframe"):
            st.iframe(html, width=width, height=700)
        else:
            components.html(html, width=width, height=700, scrolling=True)

    st.divider()
    base = f"{_slug(t['title'])}-{lang}"
    d1, d2, d3 = st.columns([1, 1, 2])
    d1.download_button("⬇️ Baixar .html", data=html, file_name=f"{base}.html", mime="text/html",
                       use_container_width=True)
    d2.download_button("⬇️ Baixar .eml", mime="message/rfc822", file_name=f"{base}.eml",
                       data=build_eml(html, to_plain(md, t), t["eml_subject"] or t["title"],
                                      t["eml_from"], t["eml_to"]),
                       use_container_width=True)
    d3.caption("O .eml abre no Outlook como rascunho novo (editável e pronto para enviar). "
               "Se algo falhar no .eml, o .html continua sendo o produto principal.")

with tab_guide:
    st.markdown("""
### Estrutura

| Markdown | Estilo (controlado nos tokens) |
|---|---|
| `# Texto` | Título nível 1 — rótulo em caixa alta com filete |
| `## Texto` | Título nível 2 — destaque do artigo |
| `### Texto` | Título nível 3 — subtítulo discreto |

Cada nível tem cor, tamanho, fonte, peso, caixa, espaçamento e margens próprios nos grupos **Título #**, **##** e **###**.

### Formatação

| Sintaxe | Resultado |
|---|---|
| `**negrito**` `*itálico*` `***ambos***` | **negrito** *itálico* ***ambos*** |
| `~~tachado~~` `` `código` `` | ~~tachado~~ `código` |
| `[texto](url)` | link |
| `- item` / `1. item` | lista com marcador / numerada |
| `> texto` | citação |
| `\\| a \\| b \\|` + linha `\\|---\\|---\\|` | tabela (`:---:` centraliza, `---:` alinha à direita) |
| `{center}texto{/center}` | parágrafo centralizado |
| `---` | divisória |
| `![descrição](https://…)` | imagem (precisa de URL pública http/https) |
| `$E=mc^2$` · `$$…$$` | LaTeX (a maioria dos clientes de e-mail não exibe MathML) |

### Editorial (rodapé)
Em **Conteúdo comum → Editorial**, escreva um nome por linha, já como hiperlink:

```
[Nome Sobrenome](https://lattes.cnpq.br/0000000000000000)
[Nome Sobrenome](https://www.linkedin.com/in/usuario)
```
Vazio omite o bloco do editorial.

### Idiomas
Cada idioma tem seu próprio Markdown e seus próprios textos fixos (grupo **Textos do idioma**).
O nome do centro só muda no inglês; em espanhol e francês fica em inglês. Cores, tamanhos e
logos valem para todos os idiomas.

### Próxima edição
Escreva no corpo do Markdown (ex.: `{center}Próxima edição: **julho de 2026**{/center}`); o rodapé não repete a informação.
""")
