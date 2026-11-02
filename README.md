# GPS Brasil — newsletter do CEG-UnB

Editor em Markdown com preview ao vivo que gera a newsletter em **HTML** e em **.eml**
(rascunho para Outlook, Thunderbird e Apple Mail), em português, inglês, espanhol e francês.

## Rodar

```
pip install -r requirements.txt
streamlit run app.py
```

## Como funciona

- **Conteúdo:** um Markdown por idioma (`content/exemplo_<idioma>.md` traz o exemplo inicial).
  `#`, `##` e `###` são três níveis de título, cada um com estilo próprio.
- **Visual:** tudo o que aparece no e-mail é um *token* em [`newsletter/tokens.py`](newsletter/tokens.py)
  (cores, fontes, tamanhos, espaçamentos, margens, logos…). A barra lateral gera um controle para cada token.
  Para criar ou remover um controle, basta editar essa lista.
- **Idiomas:** cada idioma tem seus textos fixos (linha acima do título, tagline, rodapé…) em
  [`newsletter/i18n.py`](newsletter/i18n.py), editáveis na barra lateral. O nome do centro só muda no inglês.
- **Perfis:** salvam todos os tokens e textos em `profiles/*.json` (ficam no Git, se quiser compartilhar).
- **Fontes:** só fontes padrão de e-mail (Arial, Helvetica, Verdana, Tahoma, Trebuchet MS, Georgia, Times New Roman, Courier New).

## Exportação

| Arquivo | Uso |
|---|---|
| `.html` | Produto principal: documento completo, estilos inline, layout em tabelas. |
| `.eml` | Rascunho com `X-Unsent: 1`: o Outlook abre como mensagem nova, editável. Traz também versão em texto simples. |

O formato `.msg` não é gerado (binário proprietário da Microsoft); o `.eml` cobre o mesmo uso.

Limites conhecidos de clientes de e-mail: o Outlook desktop ignora cantos arredondados
(selo da edição, imagens) e imagens do corpo precisam de URL pública `http(s)`.

## Editorial no rodapé

Em **Conteúdo comum → Editorial**, um nome por linha, já como hiperlink:

```
[Nome Sobrenome](https://lattes.cnpq.br/0000000000000000)
[Nome Sobrenome](https://www.linkedin.com/in/usuario)
```

## Testes

```
python -m unittest discover -s tests -v
```

## Estrutura

```
app.py                  editor Streamlit
newsletter/tokens.py    schema de tokens (fonte única do visual)
newsletter/i18n.py      idiomas e textos fixos
newsletter/parser.py    Markdown → blocos
newsletter/renderer.py  blocos + tokens → HTML de e-mail
newsletter/eml.py       HTML → .eml
newsletter/profiles.py  perfis em JSON
content/                Markdown de exemplo por idioma
profiles/               perfis salvos
tests/                  testes
```
