import re
import unicodedata
import difflib
import subprocess
import pandas as pd
from datetime import date
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from PIL import Image, ImageOps
from pillow_heif import register_heif_opener

register_heif_opener()

EDICOES = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI"]

EQUIPES = ["Bandinha", "Sala", "Lanche", "Teatro", "Produção",
           "Liturgia", "Secretaria", "Casa", "Ministério", "Dirigencia"]

def formatar_edicoes(lista):
    partes = []
    for ed in EDICOES:
        marca = "X" if ed in lista else "\u00a0"   # espaço que não quebra
        partes.append(f"{ed}\u00a0EJCIC\u00a0(\u00a0{marca}\u00a0);")
    return " ".join(partes)

pessoas = pd.read_csv("respostas.csv", dtype=str, encoding="utf-8").fillna("")
pessoas.columns = [c.strip() for c in pessoas.columns]

colunas_grade = {}
for coluna in pessoas.columns:
    achou = re.search(r"\[([IVX]+) EJCIC", coluna)
    if achou:
        colunas_grade[achou.group(1)] = coluna

def equipes_da_pessoa(pessoa):
    por_equipe = {}
    for edicao, coluna in colunas_grade.items():
        equipe = pessoa[coluna].strip()
        if equipe and equipe != "Nenhuma":
            por_equipe.setdefault(equipe, []).append(edicao)
    return por_equipe

def calcular_idade(texto):
    try:
        ano, mes, dia = texto.strip().split("-")
        nasc = date(int(ano), int(mes), int(dia))
    except ValueError:
        return ""
    hoje = date.today()
    idade = hoje.year - nasc.year
    if (hoje.month, hoje.day) < (nasc.month, nasc.day):
        idade -= 1
    return str(idade)

def tamanho_fonte_nome(nome):
    # nomes longos ganham fonte menor para caber na faixa
    n = len(nome)
    if n <= 17:
        return 30
    if n <= 40:
        return 24
    return 20

#FOTOS
# se algum caso não for achado sozinho, ligue à mão aqui:
# "Nome Completo da pessoa": "nome_do_arquivo.jpg"
FOTOS_MANUAIS = {}

EXTENSOES = {".jpg", ".jpeg", ".png", ".webp"}
Path("fotos_convertidas").mkdir(exist_ok=True)

# converte HEIC/HEIF em JPG, mantendo o nome original
for heic in Path("fotos").rglob("*"):
    if heic.suffix.lower() in {".heic", ".heif"}:
        destino = Path("fotos_convertidas") / (heic.stem + ".jpg")
        if not destino.exists():
            img = ImageOps.exif_transpose(Image.open(heic)).convert("RGB")
            img.save(destino, "JPEG", quality=92)

arquivos_fotos = [a for a in Path("fotos").rglob("*") if a.suffix.lower() in EXTENSOES]
arquivos_fotos += list(Path("fotos_convertidas").glob("*.jpg"))

def normalizar(texto):
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z ]+", " ", texto).strip()

def achar_foto(nome):
    # primeiro, a ligação manual
    if nome in FOTOS_MANUAIS:
        for arq in arquivos_fotos:
            if arq.name == FOTOS_MANUAIS[nome]:
                return arq, 1.0
    alvo = normalizar(nome)
    palavras_alvo = alvo.split()
    melhor, melhor_nota = None, 0
    for arq in arquivos_fotos:
        candidato = normalizar(arq.stem.split(" - ")[-1])
        palavras_cand = candidato.split()
        if not palavras_cand:
            continue
        # quantas palavras do arquivo aparecem no nome da pessoa
        # (ou das palavras da pessoa que aparecem no arquivo, o que for menor)
        menor = min(len(palavras_cand), len(palavras_alvo))
        em_comum = len(set(palavras_cand) & set(palavras_alvo))
        nota = em_comum / menor
        # empate: prefere o arquivo com mais palavras em comum
        if nota > melhor_nota or (nota == melhor_nota and melhor and em_comum > len(set(normalizar(melhor.stem.split(" - ")[-1]).split()) & set(palavras_alvo))):
            melhor, melhor_nota = arq, nota
    if melhor_nota >= 0.99:
        return melhor, melhor_nota
    return None, melhor_nota

def carregar_coordenacao():
    coord = {}
    caminho = Path("coordenacao.csv")
    if not caminho.exists():
        return coord
    tabela = pd.read_csv(caminho, dtype=str, encoding="utf-8").fillna("")
    tabela.columns = [c.strip() for c in tabela.columns]
    for _, linha in tabela.iterrows():
        nome = normalizar(linha["Nome"])
        equipe = normalizar(linha["Equipe"])
        coord.setdefault(nome, set()).add(equipe)
    return coord

COORDENACAO = carregar_coordenacao()

def formatar_caracteristicas(texto):
    # "A;B;C" -> ["A", "B", "C"] (aceita ; ou , como separador)
    itens = [i.strip() for i in re.split(r"[;,]", texto) if i.strip()]
    return itens

def montar_pacote(pessoa):
    por_equipe = equipes_da_pessoa(pessoa)
    coordenou = COORDENACAO.get(normalizar(pessoa["Nome Completo:"].strip()), set())
    arq, nota = achar_foto(pessoa["Nome Completo:"].strip())
    foto_uri = arq.resolve().as_uri() if arq else ""
    foto_info = f"{arq.name} (semelhança {nota:.0%})" if arq else f"NÃO ACHADA (melhor semelhança {nota:.0%})"
    return {
        "nome": pessoa["Nome Completo:"].strip(),
        "fonte_nome": tamanho_fonte_nome(pessoa["Nome Completo:"].strip()),
        "foto": foto_uri,
        "foto_info": foto_info,
        "idade": calcular_idade(pessoa["Data de nascimento"]),
        "telefone": pessoa["Numero de whatsApp ou Contato:"].strip(),
        "instagram": pessoa["Instagram:"].strip(),
        "ejcic": pessoa["Quando você participou como encontrista do EJCIC?"].strip(),
        "caracteristicas": formatar_caracteristicas(pessoa["Selecione as habilidades que tem a ver com seu perfil:"]),
        # ainda não existem no formulário: ficam vazios até criarmos as perguntas
        "emergencia_nome": pessoa.get("Contato de Emergência (nome)", "").strip(),
        "emergencia_tel": pessoa.get("Contato de Emergência (número)", "").strip(),
        "equipes": {eq: formatar_edicoes(por_equipe.get(eq, [])) for eq in EQUIPES},
        "coord": {eq: normalizar(eq) in coordenou for eq in EQUIPES},
    }

# prepara o modelo e a pasta de saída
env = Environment(loader=FileSystemLoader("."), autoescape=True)
modelo = env.get_template("template.html")
Path("saida").mkdir(exist_ok=True)

# caminho do navegador: use o que existir no seu computador
NAVEGADORES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]
navegador = next((n for n in NAVEGADORES if Path(n).exists()), None)
Path("pdfs").mkdir(exist_ok=True)

def gerar_pdf(html_path, pdf_path):
    subprocess.run([
        navegador,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path.resolve()}",
        html_path.resolve().as_uri(),
    ], check=True, capture_output=True)

for _, pessoa in pessoas.iterrows():
    pacote = montar_pacote(pessoa)
    nome_arquivo = re.sub(r"[^\w\-]+", "_", pacote["nome"]) + ".html"
    html = modelo.render(**pacote)
    Path("saida", nome_arquivo).write_text(html, encoding="utf-8")
    if navegador:
        pdf = Path("pdfs", nome_arquivo.replace(".html", ".pdf"))
        gerar_pdf(Path("saida", nome_arquivo), pdf)
        print("PDF:", pdf.name)
    else:
        print("Navegador não encontrado, só o HTML foi gerado.")
    print("Gerado:", nome_arquivo, "| foto:", pacote["foto_info"])