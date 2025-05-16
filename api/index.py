from flask import Flask, render_template, request
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os
import json

JSON_CRED_FILE = os.getenv("GOOGLE_CREDENTIALS")

def conectar_sheets(nome_do_sheet: str, nome_da_aba: str):
    """Conecta-se ao Google Sheets e retorna a worksheet especificada."""
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        worksheet = client.open(nome_do_sheet).worksheet(nome_da_aba)
        return worksheet
    except Exception as e:
        print(f"Erro ao conectar com Sheets: {e}")
        return None

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():

    classe = request.form.get("classe", "Coordenação")

    planilha = conectar_sheets("EBD - Rodovia A", classe)
    if planilha is None:
        return render_template(
        "index.html",
        erro="Erro ao conectar com a planilha. Verifique as credenciais ou o nome da aba.",
        classe=classe,
        year=datetime.now().year
    ), 500

    else:
        valores = planilha.get_all_records()


        trimestre_1 = []
        trimestre_2 = []
        trimestre_3 = []
        trimestre_4 = []

        for aula in valores:
            if aula["TRIMESTRE"] == "1 Trimestre":
                trimestre_1.append(aula)
            elif aula["TRIMESTRE"] == "2 Trimestre":
                trimestre_2.append(aula)
            elif aula["TRIMESTRE"] == "3 Trimestre":
                trimestre_3.append(aula)
            elif aula["TRIMESTRE"] == "4 Trimestre":
                trimestre_4.append(aula)

        return render_template(
            "index.html",
            trimestre_1=trimestre_1,
            trimestre_2=trimestre_2,
            trimestre_3=trimestre_3,
            trimestre_4=trimestre_4,
            classe=classe,
            year=datetime.now().year,
        )


if __name__ == "__main__":
    app.run(debug=True)


