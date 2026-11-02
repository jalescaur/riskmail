"""
eml.py — Empacota o HTML como rascunho .eml (message/rfc822).

O cabeçalho X-Unsent: 1 faz o Outlook abrir o arquivo como mensagem nova, editável
e pronta para enviar (em vez de abrir como e-mail recebido, só para leitura).
Formato .msg não é gerado: é binário proprietário da Microsoft; o .eml abre no
Outlook, Thunderbird e Apple Mail.
"""

from __future__ import annotations
from email.message import EmailMessage
from email.utils import formatdate


def build_eml(html: str, plain: str, subject: str, sender: str = "", to: str = "") -> bytes:
    msg = EmailMessage()
    msg["Subject"] = subject
    if sender.strip():
        msg["From"] = sender.strip()
    if to.strip():
        msg["To"] = to.strip()
    msg["Date"] = formatdate(localtime=True)
    msg["X-Unsent"] = "1"
    msg.set_content(plain)
    msg.add_alternative(html, subtype="html")
    return msg.as_bytes()
