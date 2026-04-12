from __future__ import annotations
# testes de commit 
from io import StringIO
from typing import Dict, List

import httpx
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="B2B Governo API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ANEEL_CSV_URL = (
    "https://dadosabertos.aneel.gov.br/dataset/"
    "d5f0712e-62f6-4736-8dff-9991f10758a7/resource/"
    "4493985c-baea-429c-9df5-3030422c71d7/download/"
    "indicadores-continuidade-coletivos-2020-2029.csv"
)

IBGE_ESTADOS_URL = "https://servicodados.ibge.gov.br/api/v1/localidades/estados"

# Mapeamento por distribuidora/Uf.
# Você pode evoluir isso depois para usar uma tabela própria ou base relacional.
SIG_AGENTE_TO_UF: Dict[str, str] = {
    "EQUATORIAL AL": "AL",
    "NEOENERGIA PE": "PE",
    "NEOENERGIA COELBA": "BA",
    "NEOENERGIA COSERN": "RN",
    "NEOENERGIA ELEKTRO": "SP",
    "ENEL CE": "CE",
    "ENEL RJ": "RJ",
    "ENEL SP": "SP",
    "CPFL PAULISTA": "SP",
    "CPFL PIRATININGA": "SP",
    "RGE": "RS",
    "CEEE-D": "RS",
    "EQUATORIAL MA": "MA",
    "EQUATORIAL PA": "PA",
    "EQUATORIAL PI": "PI",
    "EQUATORIAL GO": "GO",
    "LIGHT": "RJ",
    "CEMIG-D": "MG",
    "COPEL-DIS": "PR",
    "CELESC-DIS": "SC",
    "ENERGISA PB": "PB",
    "ENERGISA SE": "SE",
    "ENERGISA TO": "TO",
    "ENERGISA MT": "MT",
    "ENERGISA MS": "MS",
    "ENERGISA MG": "MG",
    "ENERGISA RO": "RO",
    "ENERGISA BO": "RO",
    "EQUATORIAL AP": "AP",
    "AMAZONAS ENERGIA": "AM",
    "RORAIMA ENERGIA": "RR",
    "SULGIPE": "SE",
}

_ibge_cache: Dict[str, str] | None = None
_aneel_cache_df: pd.DataFrame | None = None


async def carregar_uf_para_regiao() -> Dict[str, str]:
    global _ibge_cache

    if _ibge_cache is not None:
      return _ibge_cache

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(IBGE_ESTADOS_URL)
        response.raise_for_status()
        data = response.json()

    uf_para_regiao: Dict[str, str] = {}
    for item in data:
        sigla = item.get("sigla")
        regiao = item.get("regiao", {}).get("nome")
        if sigla and regiao:
            uf_para_regiao[sigla] = regiao

    _ibge_cache = uf_para_regiao
    return uf_para_regiao


async def carregar_csv_aneel() -> pd.DataFrame:
    global _aneel_cache_df

    if _aneel_cache_df is not None:
        return _aneel_cache_df.copy()

    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.get(ANEEL_CSV_URL)
        response.raise_for_status()
        csv_text = response.text

    df = pd.read_csv(
        StringIO(csv_text),
        sep=";",
        dtype=str,
        low_memory=False,
    )

    # Normalização básica
    expected_cols = {
        "SigAgente",
        "SigIndicador",
        "AnoIndice",
        "NumPeriodoIndice",
        "VlrIndiceEnviado",
    }
    missing = expected_cols - set(df.columns)
    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"CSV da ANEEL sem colunas esperadas: {sorted(missing)}",
        )

    df["SigAgente"] = df["SigAgente"].fillna("").str.strip().str.upper()
    df["SigIndicador"] = df["SigIndicador"].fillna("").str.strip().str.upper()
    df["AnoIndice"] = pd.to_numeric(df["AnoIndice"], errors="coerce")
    df["NumPeriodoIndice"] = pd.to_numeric(df["NumPeriodoIndice"], errors="coerce")

    # Troca decimal brasileira por ponto
    df["VlrIndiceEnviado"] = (
        df["VlrIndiceEnviado"]
        .fillna("0")
        .astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    df["VlrIndiceEnviado"] = pd.to_numeric(df["VlrIndiceEnviado"], errors="coerce").fillna(0.0)

    _aneel_cache_df = df.copy()
    return df


def agente_para_uf(sig_agente: str) -> str | None:
    return SIG_AGENTE_TO_UF.get(sig_agente.strip().upper())


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/consumo/regioes")
async def consumo_regioes(
    ano: int = Query(..., ge=2020, le=2030),
    indicador: str = Query("DEC"),
    periodo: int | None = Query(None, ge=1, le=12),
) -> List[Dict[str, float | str]]:
    indicador = indicador.strip().upper()

    if indicador not in {"DEC", "FEC"}:
        raise HTTPException(
            status_code=400,
            detail="Indicador inválido. Use DEC ou FEC.",
        )

    uf_para_regiao = await carregar_uf_para_regiao()
    df = await carregar_csv_aneel()

    filtrado = df[
        (df["AnoIndice"] == ano) &
        (df["SigIndicador"] == indicador)
    ].copy()

    if periodo is not None:
        filtrado = filtrado[filtrado["NumPeriodoIndice"] == periodo].copy()

    if filtrado.empty:
        return []

    filtrado["UF"] = filtrado["SigAgente"].apply(agente_para_uf)
    filtrado = filtrado[filtrado["UF"].notna()].copy()

    filtrado["Regiao"] = filtrado["UF"].map(uf_para_regiao)
    filtrado = filtrado[filtrado["Regiao"].notna()].copy()

    if filtrado.empty:
        return []

    agregado = (
        filtrado.groupby("Regiao", as_index=False)["VlrIndiceEnviado"]
        .mean()
        .sort_values("Regiao")
    )

    return [
        {
            "regiao": row["Regiao"],
            "valor": round(float(row["VlrIndiceEnviado"]), 2),
        }
        for _, row in agregado.iterrows()
    ]
