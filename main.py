from typing import List, Dict
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="B2B Governo API")

# ==================== CORS ====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://*.riker.replit.dev",  # aceita qualquer subdomínio riker
        "https://*.replit.dev",
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:5000",
    ],
    allow_origin_regex=r"https://.*\.replit\.dev",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Seus dados fixos...
DADOS_FIXOS = [
    {"regiao": "Norte", "valor": 0.91},
    {"regiao": "Nordeste", "valor": 1.18},
    {"regiao": "Centro-Oeste", "valor": 1.17},
    {"regiao": "Sudeste", "valor": 2.05},
    {"regiao": "Sul", "valor": 1.83},
]


# Suas rotas...
@app.get("/")
def root():
    return {"status": "ok", "msg": "API B2B Governo rodando"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/consumo/regioes")
def consumo_regioes(
    ano: int = Query(2026),
    indicador: str = Query("DEC"),
) -> List[Dict]:
    return DADOS_FIXOS


dados_por_regiao = {
    "Norte": [
        {"mes": "Jan", "demanda": 90},
        {"mes": "Fev", "demanda": 95},
        {"mes": "Mar", "demanda": 100},
        {"mes": "Abr", "demanda": 98},
        {"mes": "Mai", "demanda": 102},
        {"mes": "Jun", "demanda": 110},
        {"mes": "Jul", "demanda": 115},
        {"mes": "Ago", "demanda": 118},
        {"mes": "Set", "demanda": 120},
        {"mes": "Out", "demanda": 125},
        {"mes": "Nov", "demanda": 130},
        {"mes": "Dez", "demanda": 135},
    ],
    "Nordeste": [
        {"mes": "Jan", "demanda": 120},
        {"mes": "Fev", "demanda": 126},
        {"mes": "Mar", "demanda": 131},
        {"mes": "Abr", "demanda": 128},
        {"mes": "Mai", "demanda": 134},
        {"mes": "Jun", "demanda": 140},
        {"mes": "Jul", "demanda": 145},
        {"mes": "Ago", "demanda": 149},
        {"mes": "Set", "demanda": 153},
        {"mes": "Out", "demanda": 158},
        {"mes": "Nov", "demanda": 162},
        {"mes": "Dez", "demanda": 168},
    ],
    "Sudeste": [
        {"mes": "Jan", "demanda": 200},
        {"mes": "Fev", "demanda": 210},
        {"mes": "Mar", "demanda": 220},
        {"mes": "Abr", "demanda": 215},
        {"mes": "Mai", "demanda": 225},
        {"mes": "Jun", "demanda": 240},
        {"mes": "Jul", "demanda": 250},
        {"mes": "Ago", "demanda": 260},
        {"mes": "Set", "demanda": 270},
        {"mes": "Out", "demanda": 280},
        {"mes": "Nov", "demanda": 290},
        {"mes": "Dez", "demanda": 300},
    ],
    "Sul": [
        {"mes": "Jan", "demanda": 150},
        {"mes": "Fev", "demanda": 155},
        {"mes": "Mar", "demanda": 160},
        {"mes": "Abr", "demanda": 158},
        {"mes": "Mai", "demanda": 165},
        {"mes": "Jun", "demanda": 170},
        {"mes": "Jul", "demanda": 175},
        {"mes": "Ago", "demanda": 180},
        {"mes": "Set", "demanda": 185},
        {"mes": "Out", "demanda": 190},
        {"mes": "Nov", "demanda": 195},
        {"mes": "Dez", "demanda": 200},
    ],
    "Centro-Oeste": [
        {"mes": "Jan", "demanda": 110},
        {"mes": "Fev", "demanda": 115},
        {"mes": "Mar", "demanda": 120},
        {"mes": "Abr", "demanda": 118},
        {"mes": "Mai", "demanda": 125},
        {"mes": "Jun", "demanda": 130},
        {"mes": "Jul", "demanda": 135},
        {"mes": "Ago", "demanda": 138},
        {"mes": "Set", "demanda": 140},
        {"mes": "Out", "demanda": 145},
        {"mes": "Nov", "demanda": 150},
        {"mes": "Dez", "demanda": 155},
    ],
}


@app.get("/api/previsao/demanda")
def previsao_demanda(
    ano: int = Query(2026),
    regiao: str = Query(...),
) -> List[Dict]:
    regiao = regiao.strip().title()  # Normaliza (ex: "sudeste" → "Sudeste")

    if regiao not in dados_por_regiao:
        raise HTTPException(
            status_code=400,
            detail={
                "erro": "Região inválida",
                "regioes_disponiveis": list(dados_por_regiao.keys()),
            },
        )
    return dados_por_regiao[regiao]
