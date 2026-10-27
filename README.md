# EJCIC Currículos

Gerador de currículos em PDF para as equipes do EJCIC. O programa lê as respostas do formulário de inscrição (Google Forms), organiza a experiência de cada pessoa por equipe e edição, e gera um PDF por pessoa no modelo visual do evento.

## O que ele faz

1. Lê o CSV exportado do Google Forms.
2. Calcula a idade a partir da data de nascimento.
3. Transforma a grade "edição × equipe" em uma linha por equipe, marcando as edições em que a pessoa atuou: `I EJCIC (  ); VIII EJCIC ( X ); ...`
4. Liga a foto de cada pessoa pelo nome (converte fotos HEIC de iPhone para JPG automaticamente).
5. Marca a coordenação a partir de uma planilha separada.
6. Gera um HTML e um PDF por pessoa, usando o Chrome ou o Edge instalado.

## Requisitos

- Windows com Google Chrome ou Microsoft Edge instalado
- Python 3.10 ou superior
- Bibliotecas:

```
pip install pandas jinja2 pillow pillow-heif
```

## Estrutura do projeto

```
curriculos/
├── gerar.py            # o programa
├── template.html       # layout do currículo
├── respostas.csv       # respostas do formulário (não vai para o GitHub)
├── coordenacao.csv     # quem coordenou qual equipe (não vai para o GitHub)
├── fotos/              # fotos baixadas do Drive (não vai para o GitHub)
├── fotos_convertidas/  # criada automaticamente (HEIC -> JPG)
├── saida/              # HTMLs gerados
└── pdfs/               # PDFs gerados
```

## Como usar

1. No Google Forms, abra **Respostas**, abra no Sheets e baixe como CSV (**Arquivo → Baixar → .csv**). Salve como `respostas.csv` na pasta do projeto.
2. Baixe a pasta de fotos do Google Drive (criada pelo Forms) e extraia dentro de `fotos/`.
3. Crie ou atualize o `coordenacao.csv` (veja abaixo).
4. Rode:

```
python gerar.py
```

5. Os PDFs aparecem na pasta `pdfs/`.

## Colunas esperadas no CSV

O programa procura estas colunas pelo nome:

| Coluna | Uso |
|---|---|
| `Nome Completo:` | nome no currículo e ligação com foto e coordenação |
| `Data de nascimento` | cálculo da idade (formato dd/mm/aaaa) |
| `Numero de whatsApp ou Contato:` | telefone |
| `Instagram:` | Instagram |
| `Quando você participou como encontrista do EJCIC?` | campo EJCIC |
| `Selecione as habilidades que tem a ver com seu perfil:` | características |
| `Se foi equipista, em qual/quais equipes você atuou? [I EJCIC (2014)]` ... | grade de edições (uma coluna por edição) |
| `Contato de emergência: nome` | bloco de emergência |
| `Contato de emergência: telefone` | bloco de emergência |

As colunas da grade são encontradas pelo padrão `[I EJCIC`, então novas edições entram sem mudar nada além da lista `EDICOES` no `gerar.py`.

## Coordenação

Crie o `coordenacao.csv` com uma linha por equipe coordenada:

```
Nome,Equipe
Maria Silva,Bandinha
Maria Silva,Casa
```

O nome deve ser igual ao digitado no formulário (acentos e maiúsculas são ignorados). A equipe deve ser uma das listadas em `EQUIPES` no `gerar.py`.

## Fotos

Cada foto é ligada à pessoa pelo nome que vem depois do " - " no nome do arquivo (o Forms nomeia assim os envios). Se alguma foto não for encontrada, ligue à mão no dicionário `FOTOS_MANUAIS` do `gerar.py`:

```python
FOTOS_MANUAIS = {"Maria Silva": "IMG_5678 - Maria S.jpg"}
```

## Observações

- As fontes do Google (Marcellus e Roboto Condensed) são carregadas online. Sem internet, o PDF usa fontes parecidas do Windows.
- Se o Chrome/Edge estiver instalado em outro local, ajuste a lista `NAVEGADORES` no `gerar.py`.
- Duas pessoas com o começo do nome igual podem ser ligadas à mesma foto. Confira a saída do terminal e use o `FOTOS_MANUAIS` se necessário.

## Privacidade

Este projeto lida com dados pessoais, inclusive de menores de idade. Por isso `respostas.csv`, `coordenacao.csv`, as fotos e os PDFs gerados **não são versionados** (veja o `.gitignore`). Nunca publique esses arquivos.

## Autor

Feito por [Seu Nome](https://github.com/seu-usuario) para a organização do EJCIC.