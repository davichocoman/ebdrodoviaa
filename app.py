from flask import Flask, render_template, request
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os
import json

credentials_json = os.environ.get('GOOGLE_CREDENTIALS')
credentials_info = json.loads(credentials_json)
credentials = Credentials.from_service_account_info(credentials_info)

gc = gspread.authorize(credentials)
spreadsheet = gc.open("EBD - Rodovia A")

app = Flask(__name__)

meses_pt = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

def listar_imagens_planilha():
    planilha_fotos = spreadsheet.worksheet("Fotos")  # Acessa a aba "Fotos"
    links = planilha_fotos.col_values(1)  # Pega todos os valores da primeira coluna
    return links[1:]  # Ignora o cabeçalho (primeira linha)


class Pesquisas():
    def __init__(self, planilha):      
        try:
            self.planilha = spreadsheet.worksheet(planilha)
        except gspread.exceptions.WorksheetNotFound:
            raise ValueError(f"Planilha '{planilha}' não encontrada. Verifique o nome.")

    def get_ranking_geral(self):
        planilha = self.planilha.get_all_records()
        planilha_ordenada = sorted(planilha, key=lambda x: x.get("PONTUAÇÃO", 0), reverse=True)

        # Adicionar a numeração do ranking e medalhas
        for idx, row in enumerate(planilha_ordenada, start=1):
            row["POSIÇÃO"] = idx
            if idx == 1:
                row["MEDALHA"] = {"nome": "Ouro", "cor": "#ffd700"}
            elif idx == 2:
                row["MEDALHA"] = {"nome": "Prata", "cor": "#c0c0c0"}
            elif idx == 3:
                row["MEDALHA"] = {"nome": "Bronze", "cor": "#cd7f32"}
            elif idx <= 10:
                row["MEDALHA"] = {"nome": "Top 10", "cor": "#87ceeb"}
            else:
                row["MEDALHA"] = {"nome": "Sem medalha", "cor": "#c8c8c8"}
        return planilha_ordenada

    def get_posicao_por_nome(self, nome):
        planilha = self.get_ranking_geral()
        filtro = [row for row in planilha if nome.lower() in row.get("NOME", "").lower()]
        return filtro if filtro else [{"NOME": nome, "PONTUAÇÃO": "Não encontrado", "POSIÇÃO": "-", "CLASSE": "-", "MEDALHA": {"nome": "-", "cor": "#ffffff"}}]


def carregar_noticias():
    planilha_noticias = spreadsheet.worksheet("Notícias")
    linhas = planilha_noticias.get_all_values()
    mensagem_aniversario = linhas[1][1]  # Mensagem de aniversário da segunda linha
    noticias = []

    for linha in linhas[2:]:  # Ignorar as duas primeiras linhas
        if len(linha) >= 4:  # Garantir que há pelo menos 4 colunas (tema, texto, tipo, link)
            tema, texto, tipo, link = linha[:4]
            if tipo.lower() in ["foto", "vídeo"] and link:
                noticias.append({
                    'tema': tema.strip() if tema else None,
                    'texto': texto.strip() if texto else None,
                    'tipo': tipo.strip().lower(),
                    'link': link.strip()
                })
            elif tema and texto:  # Caso tenha somente tema e texto
                noticias.append({
                    'tema': tema.strip(),
                    'texto': texto.strip(),
                    'tipo': None,
                    'link': None
                })
    return noticias, mensagem_aniversario


def carregar_aniversariantes():
    planilha_aniversariantes = spreadsheet.worksheet("Aniversariantes")
    linhas = planilha_aniversariantes.get_all_values()
    aniversariantes = [
        {'nome': linha[0], 'classe': linha[1], 'data': linha[2]}
        for linha in linhas[1:]  # Ignora o cabeçalho
        if len(linha) >= 3 and linha[2]  # Verifica se a data é válida
    ]
    return aniversariantes

class Pesquisas_escala():
    def __init__(self, planilha):      
        try:
            self.planilha = spreadsheet.worksheet(planilha)
        except gspread.exceptions.WorksheetNotFound:
            raise ValueError(f"Planilha '{planilha}' não encontrada. Verifique o nome.")

    def get_escala(self):
        # Obtém todos os dados da planilha
        return self.planilha.get_all_records()

    def get_escala_por_classe(self, classe):
        # Filtra a escala pela classe
        planilha = self.get_escala()
        if classe == "Todas":
            return planilha
        filtro = [row for row in planilha if row.get("CLASSE", "").lower() == classe.lower()]
        return filtro if filtro else [{"DATA": "-", "PROFESSOR": "-", "LIÇÃO": "-", "TEMA": "-", "CLASSE": classe}]

    def separar_por_trimestre(self, escala):
        # Separar os dados da escala por trimestre
        trimestre_1 = []
        trimestre_2 = []
        trimestre_3 = []
        trimestre_4 = []

        for row in escala:
            try:
                # Extrair o mês da data (formato DD/MM)
                mes = datetime.strptime(row['DATA'], '%d/%m').month
                if mes in [1, 2, 3]:
                    trimestre_1.append(row)
                elif mes in [4, 5, 6]:
                    trimestre_2.append(row)
                elif mes in [7, 8, 9]:
                    trimestre_3.append(row)
                elif mes in [10, 11, 12]:
                    trimestre_4.append(row)
            except ValueError:
                # Se houver erro de data, não adiciona à nenhuma lista
                continue

        return trimestre_1, trimestre_2, trimestre_3, trimestre_4

def pegar_valor_especifico(linha, coluna):
  try:
    planilha_aniversariantes = spreadsheet.worksheet("Textos")
    celula = planilha_aniversariantes.cell(linha, coluna).value
    return celula
  except IndexError:
    return "Linha ou coluna inválida."
  except AttributeError:
    return "Célula vazia."


@app.route("/")
def index():
    pesquisa = Pesquisas("Ranking Geral")
    dados = pesquisa.get_ranking_geral()

    # URLs das imagens do carrossel
    image_urls = listar_imagens_planilha()

    # Carregar notícias e aniversariantes
    noticias, mensagem_aniversario = carregar_noticias()
    aniversariantes = carregar_aniversariantes()

    # Filtrar aniversariantes do mês atual
    mes_atual = meses_pt[datetime.now().month]
    aniversariantes_mes = [
        aniversariante for aniversariante in aniversariantes
        if datetime.strptime(aniversariante['data'], '%d/%m').month == datetime.now().month
    ]

    return render_template(
        "ranking.html",
        title="Ranking Geral",
        tipo="Ranking Geral",
        dados=dados,
        fotos=image_urls,
        noticias=noticias,
        aniversariantes=aniversariantes_mes,
        mensagem_aniversario=mensagem_aniversario,
        mes_atual=mes_atual,
        year=datetime.now().year,
    )

@app.route("/ranking")
def ranking():
    tipo = request.args.get("tipo", "Ranking Geral")
    pesquisa = Pesquisas(tipo)
    dados = pesquisa.get_ranking_geral()

    image_urls = listar_imagens_planilha()

    # Carregar notícias e aniversariantes
    noticias, mensagem_aniversario = carregar_noticias()
    aniversariantes = carregar_aniversariantes()

    # Filtrar aniversariantes do mês atual
    mes_atual = meses_pt[datetime.now().month]
    aniversariantes_mes = [
        aniversariante for aniversariante in aniversariantes
        if datetime.strptime(aniversariante['data'], '%d/%m').month == datetime.now().month
    ]

    return render_template(
        "ranking.html",
        title=f"{tipo}",
        tipo=tipo,
        dados=dados,
        fotos=image_urls,
        noticias=noticias,
        aniversariantes=aniversariantes_mes,
        mensagem_aniversario=mensagem_aniversario,
        mes_atual=mes_atual,
        year=datetime.now().year,
    )


@app.route("/buscar", methods=["POST"])
def buscar():
    nome = request.form.get("nome")
    classe = request.form.get("classe", "Ranking Geral")
    pesquisa = Pesquisas(classe)
    resultado = pesquisa.get_posicao_por_nome(nome)
    return render_template(
        "ranking.html",
        title=f"Resultado para {nome}",
        tipo=classe,
        dados=resultado,
        year=datetime.now().year,
    )

@app.route("/escala", methods=["GET", "POST"])
def escala():
    # Inicializa com a classe "Coordenação" se nada for selecionado
    classe = request.form.get("classe", "Coordenação")
    pesquisa = Pesquisas_escala("Escala")
    
    # Obtém os dados filtrados ou a escala completa
    if classe:
        resultado = pesquisa.get_escala_por_classe(classe)
        titulo = f"{classe}" if classe != "Todas" else "Escala Completa"
    else:
        resultado = pesquisa.get_escala()
        titulo = "Escala Completa"

    texto = pegar_valor_especifico(2,2)

    # Separando os resultados por trimestre
    trimestre_1, trimestre_2, trimestre_3, trimestre_4 = pesquisa.separar_por_trimestre(resultado)

    return render_template(
        "escala.html",
        title=titulo,
        trimestre_1=trimestre_1,
        trimestre_2=trimestre_2,
        trimestre_3=trimestre_3,
        trimestre_4=trimestre_4,
        classe=classe,
        texto=texto,
        year=datetime.now().year,
    )

if __name__ == "__main__":
    app.run(debug=True)


