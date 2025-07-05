from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os
import json

# Configuração da Vercel
# Certifique-se de que o arquivo HTML está na pasta 'templates'
templates = Jinja2Templates(directory="templates")

# JSON_CRED_FILE = "GOOGLE_CREDENTIALS.json"
JSON_CRED_FILE = os.getenv("GOOGLE_CREDENTIALS")

def conectar_sheets(nome_do_sheets, nome_da_planilha):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_CRED_FILE, scope)
    client = gspread.authorize(creds)
    return client.open(nome_do_sheets).worksheet(nome_da_planilha)

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
@app.post("/", response_class=HTMLResponse)
async def index(request: Request, classe: str = Form("Coordenação")): # Use Form para dados de formulário
    try:
        # A lógica de conexão com o Google Sheets pode permanecer síncrona
        # gspread não é assíncrono por padrão. Para assincronicidade real,
        # você precisaria de gspread_asyncio ou executar em um ThreadPoolExecutor.
        # Por simplicidade, mantemos síncrono aqui, mas o FastAPI ainda funcionará.
        planilha = conectar_sheets("EBD - Rodovia A", classe)

        if not planilha:
            return templates.TemplateResponse(
                "index.html",
                {
                    "request": request,
                    "erro": "Erro ao conectar com a planilha. Verifique as credenciais ou o nome da aba.",
                    "classe": classe,
                    "year": datetime.now().year,
                },
                status_code=500,
            )

        valores = planilha.get_all_records(expected_headers=["DATA", "PROFESSOR", "LIÇÃO", "TRIMESTRE", "TEMA"])

        trimestre_1, trimestre_2, trimestre_3, trimestre_4 = [], [], [], []

        for aula in valores:
            match aula["TRIMESTRE"]:
                case "1 Trimestre": trimestre_1.append(aula)
                case "2 Trimestre": trimestre_2.append(aula)
                case "3 Trimestre": trimestre_3.append(aula)
                case "4 Trimestre": trimestre_4.append(aula)

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "trimestre_1": trimestre_1,
                "trimestre_2": trimestre_2,
                "trimestre_3": trimestre_3,
                "trimestre_4": trimestre_4,
                "classe": classe,
                "year": datetime.now().year,
            },
        )

    except Exception as e:
        print(f"Erro interno na rota /: {e}")
        return HTMLResponse(content=f"Erro interno: {str(e)}", status_code=500)

# # Para Vercel, o FastAPI 'app' já é o handler
handler = app

# if __name__ == "__main__":
#     app.run(debug=True) # debug=True é útil para desenvolvimento local
