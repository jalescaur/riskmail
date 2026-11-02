"""
i18n.py — Idiomas da newsletter e textos fixos (tudo que não é o corpo em Markdown).

O nome do centro só muda em inglês; em espanhol e francês mantém-se a versão em inglês.
Os textos abaixo são só os valores iniciais: todos são editáveis no app e salvos nos perfis.
"""

from __future__ import annotations

LANGS = {
    "pt": "Português",
    "en": "English",
    "es": "Español",
    "fr": "Français",
}

HTML_LANG = {"pt": "pt-BR", "en": "en", "es": "es", "fr": "fr"}

_CENTER_EN = "Center for Global Studies"

TEXTS: dict[str, dict[str, str]] = {
    "pt": {
        "eyebrow":       "Centro de Estudos Globais · Universidade de Brasília",
        "tagline":       "O que importa no mundo. O que muda para o Brasil.",
        "edition":       "Edição · Jun. 2026",
        "invite":        "Dúvidas, comentários ou interesse em\naprofundar algum tema? Teremos prazer em conversar.",
        "lbl_contact":   "Contato",
        "lbl_editorial": "Editorial",
        "center_name":   "Centro de Estudos Globais",
        "unb_name":      "Universidade de Brasília",
        "method_label":  "Nota metodológica",
        "address":       "Instituto de Relações Internacionais — Universidade de Brasília\n"
                         "Campus Universitário Darcy Ribeiro, Asa Norte — Brasília, DF 70910-900",
        "legal":         "© {year} Centro de Estudos Globais da Universidade de Brasília.\n"
                         "Reprodução permitida mediante citação da fonte.",
        "eml_subject":   "GPS Brasil — Jun. 2026",
    },
    "en": {
        "eyebrow":       f"{_CENTER_EN} · University of Brasília",
        "tagline":       "What matters in the world. What changes for Brazil.",
        "edition":       "Edition · Jun. 2026",
        "invite":        "Questions, comments or interest in\ngoing deeper on a topic? We would be glad to talk.",
        "lbl_contact":   "Contact",
        "lbl_editorial": "Editorial",
        "center_name":   _CENTER_EN,
        "unb_name":      "University of Brasília",
        "method_label":  "Methodological note",
        "address":       "Institute of International Relations — University of Brasília\n"
                         "Darcy Ribeiro University Campus, Asa Norte — Brasília, DF 70910-900, Brazil",
        "legal":         f"© {{year}} {_CENTER_EN}, University of Brasília.\n"
                         "Reproduction permitted with citation of the source.",
        "eml_subject":   "GPS Brasil — Jun. 2026",
    },
    "es": {
        "eyebrow":       f"{_CENTER_EN} · Universidad de Brasilia",
        "tagline":       "Lo que importa en el mundo. Lo que cambia para Brasil.",
        "edition":       "Edición · Jun. 2026",
        "invite":        "¿Dudas, comentarios o interés en\nprofundizar algún tema? Será un placer conversar.",
        "lbl_contact":   "Contacto",
        "lbl_editorial": "Editorial",
        "center_name":   _CENTER_EN,
        "unb_name":      "Universidad de Brasilia",
        "method_label":  "Nota metodológica",
        "address":       "Instituto de Relaciones Internacionales — Universidad de Brasilia\n"
                         "Campus Universitario Darcy Ribeiro, Asa Norte — Brasilia, DF 70910-900, Brasil",
        "legal":         f"© {{year}} {_CENTER_EN}, Universidad de Brasilia.\n"
                         "Reproducción permitida citando la fuente.",
        "eml_subject":   "GPS Brasil — Jun. 2026",
    },
    "fr": {
        "eyebrow":       f"{_CENTER_EN} · Université de Brasília",
        "tagline":       "Ce qui compte dans le monde. Ce qui change pour le Brésil.",
        "edition":       "Édition · juin 2026",
        "invite":        "Des questions, des commentaires ou l’envie\nd’approfondir un sujet ? Nous serons heureux d’échanger.",
        "lbl_contact":   "Contact",
        "lbl_editorial": "Éditorial",
        "center_name":   _CENTER_EN,
        "unb_name":      "Université de Brasília",
        "method_label":  "Note méthodologique",
        "address":       "Institut des Relations Internationales — Université de Brasília\n"
                         "Campus universitaire Darcy Ribeiro, Asa Norte — Brasília, DF 70910-900, Brésil",
        "legal":         f"© {{year}} {_CENTER_EN}, Université de Brasília.\n"
                         "Reproduction autorisée avec mention de la source.",
        "eml_subject":   "GPS Brasil — Jun. 2026",
    },
}
