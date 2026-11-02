"""Testes do gerador. Rodar: python -m unittest discover -s tests -v"""

import email
import json
import re
import sys
import tempfile
import unittest
from email import policy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from newsletter import profiles, tokens as tk
from newsletter.eml import build_eml
from newsletter.i18n import LANGS
from newsletter.parser import Divider, Heading, ListBlock, Paragraph, Quote, Table, parse
from newsletter.renderer import inline, render, to_plain


def sample(lang="pt"):
    return (ROOT / "content" / f"exemplo_{lang}.md").read_text(encoding="utf-8")


def theme(lang="pt", **tokens):
    state = tk.defaults()
    state["tokens"].update(tokens)
    return tk.resolve(state, lang)


class ParserTests(unittest.TestCase):
    def test_block_types_and_heading_levels(self):
        blocks = parse("# A\n\n## B\n\n### C\n\n#### D\n\ntexto\nem duas linhas\n\n- x\n- y\n\n> q\n\n---")
        self.assertEqual([type(b) for b in blocks],
                         [Heading, Heading, Heading, Heading, Paragraph, ListBlock, Quote, Divider])
        self.assertEqual([b.level for b in blocks[:4]], [1, 2, 3, 3])
        self.assertEqual(blocks[4].text, "texto em duas linhas")

    def test_table_header_and_alignment(self):
        (tbl,) = parse("| a | b |\n|:--|--:|\n| 1 | 2 |")
        self.assertIsInstance(tbl, Table)
        self.assertEqual(tbl.headers, ["a", "b"])
        self.assertEqual(tbl.aligns, ["left", "right"])
        self.assertEqual(tbl.rows, [["1", "2"]])


class InlineTests(unittest.TestCase):
    def test_html_is_escaped_and_unsafe_links_neutralised(self):
        t = theme()
        out = inline("<script>x</script> & [a](javascript:alert(1)) [b](https://x.org?a=1&b=2)", t)
        self.assertNotIn("<script>", out)
        self.assertIn("&lt;script&gt;", out)
        self.assertIn('href="#"', out)
        self.assertIn('href="https://x.org?a=1&amp;b=2"', out)

    def test_currency_dollar_is_not_latex(self):
        out = inline("US$110 e R$ 5 e **ok**", theme())
        self.assertIn("US$110", out)
        self.assertIn("R$ 5", out)

    def test_code_span_protects_emphasis(self):
        self.assertIn("*x*", inline("`*x*`", theme()))


class RenderTests(unittest.TestCase):
    def test_email_safe_output(self):
        for lang in LANGS:
            html = render(sample(lang), theme(lang))
            self.assertNotIn("var(", html)
            self.assertNotIn("rgba(", html)
            self.assertNotIn("gradient", html)
            self.assertEqual(html.count("<style>"), 1)       # só o @media de celular
            self.assertIn(f'lang="{ {"pt": "pt-BR"}.get(lang, lang) }"', html)

    def test_tokens_drive_the_output(self):
        html = render("# Oi\n\ntexto", theme(banner_bg="#112233", h1_color="#abcdef", text_size=19))
        self.assertIn("#112233", html)
        self.assertIn("color:#abcdef", html)
        self.assertIn("font-size:19px", html)

    def test_center_name_only_changes_in_english(self):
        names = {lang: theme(lang)["center_name"] for lang in LANGS}
        self.assertEqual(names["pt"], "Centro de Estudos Globais")
        self.assertEqual({names["en"], names["es"], names["fr"]}, {"Center for Global Studies"})

    def test_footer_order_and_editorial_links(self):
        t = theme(editorial="[Ana Souza](https://lattes.cnpq.br/1)\n[Bia Lima](https://www.linkedin.com/in/b)")
        html = render("texto", t)
        pos = [html.index(s) for s in (t["invite"].split("\n")[0], "Contato", "Editorial",
                                       "ceg_logotipo.png", "Instituto de Rela", "©")]
        self.assertEqual(pos, sorted(pos))
        self.assertIn('href="https://lattes.cnpq.br/1"', html)
        self.assertRegex(html, r'<a href="https://lattes.cnpq.br/1"[^>]*>Ana Souza</a><br>')
        self.assertNotIn("Próxima edição", render("texto", theme()))   # rodapé não repete

    def test_empty_editorial_omits_block(self):
        self.assertNotIn(">Editorial<", render("texto", theme(editorial="")))

    def test_images_need_http_url(self):
        html = render("![a](javascript:x)\n\n![b](https://x.org/i.png)", theme())
        self.assertNotIn("javascript", html)
        self.assertIn('src="https://x.org/i.png"', html)

    def test_heading_spacing_collapses_like_margins(self):
        t = theme(p_after=16, h2_before=26)
        html = render("par\n\n## T", t)
        self.assertIn("padding:26px 0 0 0", html)       # max(16, 26), não 16 + 26


class EmlTests(unittest.TestCase):
    def test_eml_has_both_parts_and_unsent_flag(self):
        t = theme()
        html = render(sample(), t)
        raw = build_eml(html, to_plain(sample(), t), "GPS Brasil — Jun. 2026", "CEG <a@b.br>", "x@y.br")
        msg = email.message_from_bytes(raw, policy=policy.default)
        self.assertEqual(msg["X-Unsent"], "1")
        self.assertEqual(msg["Subject"], "GPS Brasil — Jun. 2026")
        self.assertEqual(msg.get_body(("plain",)).get_content().splitlines()[0], "GPS Brasil")
        self.assertIn("<!DOCTYPE html>", msg.get_body(("html",)).get_content())

    def test_eml_without_addresses(self):
        raw = build_eml("<p>x</p>", "x", "Assunto")
        msg = email.message_from_bytes(raw, policy=policy.default)
        self.assertIsNone(msg["From"])
        self.assertIsNone(msg["To"])


class TokenAndProfileTests(unittest.TestCase):
    def test_every_token_has_a_valid_default(self):
        for tok in tk.TOKENS:
            value = tk.default_for(tok, "pt")
            self.assertEqual(tk.coerce(tok, value, "pt"), value, tok.key)

    def test_sanitize_ignores_unknown_and_invalid(self):
        out = tk.sanitize_profile({"tokens": {"banner_bg": "azul", "nao_existe": 1, "text_size": 999,
                                              "font_body": "Comic Sans"},
                                   "texts": {"pt": {"tagline": "Olá"}, "xx": {"tagline": "?"}}})
        self.assertEqual(out["tokens"]["banner_bg"], "#003366")
        self.assertEqual(out["tokens"]["text_size"], 22)
        self.assertEqual(out["tokens"]["font_body"], "Arial")
        self.assertNotIn("nao_existe", out["tokens"])
        self.assertEqual(out["texts"]["pt"]["tagline"], "Olá")
        self.assertNotIn("xx", out["texts"])

    def test_profile_roundtrip_and_name_safety(self):
        with tempfile.TemporaryDirectory() as d:
            profiles.PROFILES_DIR = Path(d)
            state = tk.defaults()
            state["tokens"]["banner_bg"] = "#123456"
            profiles.save_profile("padrão ceg", state)
            self.assertEqual(profiles.list_profiles(), ["padrão ceg"])
            self.assertEqual(profiles.load_profile("padrão ceg")["tokens"]["banner_bg"], "#123456")
            profiles.save_profile("../fora", state)           # não escapa da pasta
            self.assertTrue((Path(d) / "fora.json").exists())
            with self.assertRaises(ValueError):
                profiles.save_profile("///", state)


class AppSmokeTest(unittest.TestCase):
    def test_app_runs_and_reacts_to_language_and_tokens(self):
        from streamlit.testing.v1 import AppTest
        at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=90).run()
        self.assertFalse(at.exception)
        at.sidebar.radio(key="lang").set_value("fr").run()
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state["txt_fr_center_name"], "Center for Global Studies")
        self.assertIn("Commerce extérieur", at.session_state["md_fr"])
        at.sidebar.color_picker(key="tok_banner_bg").set_value("#102030").run()
        self.assertFalse(at.exception)


if __name__ == "__main__":
    unittest.main()
