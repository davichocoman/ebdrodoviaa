from flask import Flask, render_template, request
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os
import json

cred_raw = os.getenv("GOOGLE_CREDENTIALS")
if not cred_raw:
    raise ValueError("Variável de ambiente GOOGLE_CREDENTIALS não está definida!")

try:
    JSON_CRED_FILE = json.loads(cred_raw)
except Exception as e:
    raise ValueError(f"Erro ao carregar JSON de credenciais: {str(e)}")

def conectar_sheets(sheet_name, aba):
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    credentials = Credentials.from_service_account_info(JSON_CRED_FILE, scopes=scopes)
    client = gspread.authorize(credentials)
    return client.open(sheet_name).worksheet(aba)

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    try:
        classe = request.form.get("classe", "Coordenação")
        planilha = conectar_sheets("EBD - Rodovia A", classe)

         if not planilha:
            return render_template("index.html",
                erro="Erro ao conectar com a planilha. Verifique as credenciais ou o nome da aba.",
                classe=classe,
                year=datetime.now().year
            ), 500

        valores = planilha.get_all_records(expected_headers=["DATA", "PROFESSOR", "LIÇÃO","TRIMESTRE", "TEMA"])

        valores = planilha.get_all_records(expected_headers=["DATA", "PROFESSOR", "LIÇÃO", "TRIMESTRE", "TEMA"])

        trimestre_1, trimestre_2, trimestre_3, trimestre_4 = [], [], [], []

        for aula in valores:
            match aula["TRIMESTRE"]:
                case "1 Trimestre": trimestre_1.append(aula)
                case "2 Trimestre": trimestre_2.append(aula)
                case "3 Trimestre": trimestre_3.append(aula)
                case "4 Trimestre": trimestre_4.append(aula)

        return render_template(
            "index.html",
            trimestre_1=trimestre_1,
            trimestre_2=trimestre_2,
            trimestre_3=trimestre_3,
            trimestre_4=trimestre_4,
            classe=classe,
            year=datetime.now().year,
        )

    except Exception as e:
        print(f"Erro interno na rota /: {e}")
        return f"Erro interno: {str(e)}", 500

# Exporta o app para ser usado como handler no Vercel
handler = app


