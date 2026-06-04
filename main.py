import os
import httpx
import asyncio
from datetime import date, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from anthropic import Anthropic
import json
import pytz

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FOOTBALL_API_KEY = os.environ.get("FOOTBALL_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
FOOTBALL_API_URL = "https://v3.football.api-sports.io"
TIMEZONE = "America/Sao_Paulo"

anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)

ANALYSIS_PROMPT = """Você é um tipster profissional de elite. Sua análise deve ser completa, com dados reais e palpites selecionados pelos mercados de maior valor.

REGRA ABSOLUTA: NUNCA escreva "dado insuficiente". Se não tiver o dado exato, estime com base no contexto.

Retorne a análise em formato JSON com esta estrutura EXATA:
{
  "header": "✅ ANÁLISE CONCLUÍDA - SEU TIPSTER ✅",
  "home": {
    "name": "Nome do time",
    "form": ["V","V","D","E","V"],
    "goals_scored": 2.1,
    "goals_conceded": 0.8,
    "cards_per_game": 1.8,
    "shots_on_target": 5.2,
    "corners_per_game": 6.1,
    "corners_first_half": 2.8,
    "goals_first_half": "marcou em 6/8 jogos",
    "clean_sheets": 3,
    "summary": "Texto descritivo do desempenho do time"
  },
  "away": {
    "name": "Nome do time",
    "form": ["V","D","E","V","V"],
    "goals_scored": 1.4,
    "goals_conceded": 1.2,
    "cards_per_game": 2.1,
    "shots_on_target": 4.1,
    "corners_per_game": 4.8,
    "corners_first_half": 2.1,
    "goals_first_half": "marcou em 4/8 jogos",
    "clean_sheets": 2,
    "summary": "Texto descritivo do desempenho do time"
  },
  "h2h": {
    "summary": "Descrição do histórico de confrontos",
    "avg_goals": 2.6,
    "btts_pct": 65,
    "over25_pct": 58,
    "avg_corners": 9.2,
    "avg_cards": 3.8,
    "last_result": "Placar e data do último confronto"
  },
  "context": {
    "referee": "Nome do árbitro — X cartões/jogo",
    "injuries": "Desfalques confirmados",
    "importance": "Contexto e importância do jogo"
  },
  "probabilities": {
    "home_win": 52,
    "draw": 25,
    "away_win": 23
  },
  "tips": [
    {
      "category": "seguro",
      "market": "Nome exato do mercado",
      "pick": "Palpite específico",
      "min_odd": "1.65",
      "confidence": 85,
      "reasoning": "Justificativa com número concreto"
    }
  ],
  "risk": "Principais fatores de risco"
}

Para tips, use category: "seguro" (odd 1.30-1.80), "moderado" (1.80-2.50), "agressivo" (2.50+).
Inclua 6-8 tips dos melhores mercados: resultado, over/under gols, BTTS, escanteios, cartões, 1T, handicap, jogadores.
Escolha apenas os mercados com maior base estatística."""


async def football_request(endpoint: str, params: dict) -> dict:
    headers = {"x-apisports-key": FOOTBALL_API_KEY}
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(f"{FOOTBALL_API_URL}/{endpoint}", headers=headers, params=params)
        r.raise_for_status()
        return r.json()


def translate_team(name: str) -> str:
    teams = {
        "Brazil": "Brasil", "Argentina": "Argentina", "Germany": "Alemanha",
        "France": "França", "Spain": "Espanha", "Portugal": "Portugal",
        "Italy": "Itália", "Netherlands": "Holanda", "England": "Inglaterra",
        "Uruguay": "Uruguai", "Colombia": "Colômbia", "Chile": "Chile",
        "Belgium": "Bélgica", "Croatia": "Croácia", "Morocco": "Marrocos",
        "Senegal": "Senegal", "Japan": "Japão", "South Korea": "Coreia do Sul",
        "USA": "Estados Unidos", "Mexico": "México", "Egypt": "Egito",
        "Vasco DA Gama": "Vasco", "Sao Paulo": "São Paulo",
        "Atletico Mineiro": "Atlético-MG", "Gremio": "Grêmio",
        "Paris Saint-Germain": "PSG", "Paris Saint Germain": "PSG",
        "Bayern Munich": "Bayern de Munique", "AC Milan": "Milan",
        "Inter Milan": "Internazionale", "AS Roma": "Roma",
        "Atletico Madrid": "Atlético de Madrid", "FC Barcelona": "Barcelona",
        "Northern Ireland": "Irlanda do Norte", "Turkey": "Turquia",
        "Switzerland": "Suíça", "Denmark": "Dinamarca", "Sweden": "Suécia",
        "Poland": "Polônia", "Serbia": "Sérvia", "Romania": "Romênia",
        "Ivory Coast": "Costa do Marfim", "Nigeria": "Nigéria",
        "Cameroon": "Camarões", "Ghana": "Gana", "Tunisia": "Tunísia",
        "Australia": "Austrália", "Saudi Arabia": "Arábia Saudita", "Iran": "Irã",
        "Bolivia": "Bolívia", "Ecuador": "Equador", "Paraguay": "Paraguai",
        "Venezuela": "Venezuela", "Peru": "Peru", "Panama": "Panamá",
        "Costa Rica": "Costa Rica", "Honduras": "Honduras",
    }
    return teams.get(name, name)


def translate_league(name: str) -> str:
    leagues = {
        "World Cup": "Copa do Mundo", "FIFA World Cup": "Copa do Mundo",
        "International Friendlies": "Amistosos Internacionais",
        "Friendlies": "Amistosos", "Club Friendlies": "Amistosos de Clubes",
        "UEFA Champions League": "Champions League",
        "UEFA Europa League": "Europa League",
        "UEFA Conference League": "Conference League",
        "Copa America": "Copa América", "CONMEBOL Libertadores": "Libertadores",
        "CONMEBOL Sudamericana": "Sul-Americana",
        "UEFA Nations League": "Nations League",
        "Copa Do Brasil": "Copa do Brasil", "Copa do Brasil": "Copa do Brasil",
        "Premier League": "Premier League", "La Liga": "La Liga",
        "Bundesliga": "Bundesliga", "Serie A": "Serie A", "Ligue 1": "Ligue 1",
        "Primeira Liga": "Primeira Liga", "Eredivisie": "Eredivisie",
        "Copa del Rey": "Copa del Rey", "FA Cup": "FA Cup",
    }
    return leagues.get(name, name)


# ── ROUTES ────────────────────────────────────────────────────────────────────

@app.get("/api/fixtures/today")
async def get_today():
    tz = pytz.timezone(TIMEZONE)
    today = date.today().isoformat()
    data = await football_request("fixtures", {"date": today, "timezone": TIMEZONE})
    fixtures = data.get("response", [])
    result = []
    for f in fixtures:
        result.append({
            "id": f["fixture"]["id"],
            "date": f["fixture"]["date"],
            "status": f["fixture"]["status"]["short"],
            "elapsed": f["fixture"]["status"].get("elapsed"),
            "venue": f["fixture"]["venue"]["name"] if f["fixture"].get("venue") else None,
            "league": {
                "id": f["league"]["id"],
                "name": translate_league(f["league"]["name"]),
                "logo": f["league"]["logo"],
                "country": f["league"]["country"],
            },
            "home": {
                "id": f["teams"]["home"]["id"],
                "name": translate_team(f["teams"]["home"]["name"]),
                "logo": f["teams"]["home"]["logo"],
                "score": f["goals"]["home"],
            },
            "away": {
                "id": f["teams"]["away"]["id"],
                "name": translate_team(f["teams"]["away"]["name"]),
                "logo": f["teams"]["away"]["logo"],
                "score": f["goals"]["away"],
            },
        })
    return {"fixtures": result, "total": len(result)}


@app.get("/api/fixtures/week")
async def get_week():
    dates = [(date.today() + timedelta(days=i)).isoformat() for i in range(7)]
    results = await asyncio.gather(
        *[football_request("fixtures", {"date": d, "timezone": TIMEZONE}) for d in dates],
        return_exceptions=True
    )
    week = {}
    for i, day_iso in enumerate(dates):
        if isinstance(results[i], Exception):
            continue
        fixtures = results[i].get("response", [])
        if not fixtures:
            continue
        week[day_iso] = []
        for f in fixtures:
            week[day_iso].append({
                "id": f["fixture"]["id"],
                "date": f["fixture"]["date"],
                "status": f["fixture"]["status"]["short"],
                "league": {
                    "id": f["league"]["id"],
                    "name": translate_league(f["league"]["name"]),
                    "logo": f["league"]["logo"],
                },
                "home": {
                    "name": translate_team(f["teams"]["home"]["name"]),
                    "logo": f["teams"]["home"]["logo"],
                    "score": f["goals"]["home"],
                },
                "away": {
                    "name": translate_team(f["teams"]["away"]["name"]),
                    "logo": f["teams"]["away"]["logo"],
                    "score": f["goals"]["away"],
                },
            })
    return {"week": week}


@app.get("/api/fixture/{fixture_id}")
async def get_fixture(fixture_id: int):
    data = await football_request("fixtures", {"id": fixture_id})
    fixtures = data.get("response", [])
    if not fixtures:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")
    f = fixtures[0]
    return {
        "id": f["fixture"]["id"],
        "date": f["fixture"]["date"],
        "status": f["fixture"]["status"]["short"],
        "elapsed": f["fixture"]["status"].get("elapsed"),
        "venue": f["fixture"]["venue"]["name"] if f["fixture"].get("venue") else None,
        "league": {
            "id": f["league"]["id"],
            "name": translate_league(f["league"]["name"]),
            "logo": f["league"]["logo"],
            "country": f["league"]["country"],
        },
        "home": {
            "id": f["teams"]["home"]["id"],
            "name": translate_team(f["teams"]["home"]["name"]),
            "logo": f["teams"]["home"]["logo"],
            "score": f["goals"]["home"],
        },
        "away": {
            "id": f["teams"]["away"]["id"],
            "name": translate_team(f["teams"]["away"]["name"]),
            "logo": f["teams"]["away"]["logo"],
            "score": f["goals"]["away"],
        },
    }


@app.post("/api/analysis/{fixture_id}")
async def get_analysis(fixture_id: int):
    # Coleta dados
    fixture_data, stats_data = await asyncio.gather(
        football_request("fixtures", {"id": fixture_id}),
        football_request("fixtures/statistics", {"fixture": fixture_id}),
        return_exceptions=True
    )

    fixtures = fixture_data.get("response", []) if not isinstance(fixture_data, Exception) else []
    if not fixtures:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")

    f = fixtures[0]
    home_id = f["teams"]["home"]["id"]
    away_id = f["teams"]["away"]["id"]
    home_name = translate_team(f["teams"]["home"]["name"])
    away_name = translate_team(f["teams"]["away"]["name"])
    league_name = translate_league(f["league"]["name"])

    # Busca forma dos times e H2H
    home_form_data, away_form_data, h2h_real = await asyncio.gather(
        football_request("fixtures", {"team": home_id, "last": 8, "timezone": TIMEZONE}),
        football_request("fixtures", {"team": away_id, "last": 8, "timezone": TIMEZONE}),
        football_request("fixtures/headtohead", {"h2h": f"{home_id}-{away_id}", "last": 10}),
        return_exceptions=True
    )

    # Monta contexto para o Claude
    context = {
        "fixture": {
            "home": home_name,
            "away": away_name,
            "league": league_name,
            "date": f["fixture"]["date"],
            "venue": f["fixture"]["venue"]["name"] if f["fixture"].get("venue") else "N/A",
        },
        "home_recent": [],
        "away_recent": [],
        "h2h": [],
        "statistics": [],
    }

    if not isinstance(home_form_data, Exception):
        for match in home_form_data.get("response", []):
            ht = match["teams"]["home"]["id"]
            hg = match["goals"]["home"] or 0
            ag = match["goals"]["away"] or 0
            is_home = ht == home_id
            if is_home:
                result = "V" if hg > ag else ("E" if hg == ag else "D")
            else:
                result = "V" if ag > hg else ("E" if hg == ag else "D")
            context["home_recent"].append({
                "result": result,
                "scored": hg if is_home else ag,
                "conceded": ag if is_home else hg,
                "opponent": translate_team(match["teams"]["away"]["name"] if is_home else match["teams"]["home"]["name"]),
            })

    if not isinstance(away_form_data, Exception):
        for match in away_form_data.get("response", []):
            ht = match["teams"]["home"]["id"]
            hg = match["goals"]["home"] or 0
            ag = match["goals"]["away"] or 0
            is_home = ht == away_id
            if is_home:
                result = "V" if hg > ag else ("E" if hg == ag else "D")
            else:
                result = "V" if ag > hg else ("E" if hg == ag else "D")
            context["away_recent"].append({
                "result": result,
                "scored": hg if is_home else ag,
                "conceded": ag if is_home else hg,
                "opponent": translate_team(match["teams"]["away"]["name"] if is_home else match["teams"]["home"]["name"]),
            })

    if not isinstance(h2h_real, Exception):
        for match in h2h_real.get("response", []):
            hg = match["goals"]["home"] or 0
            ag = match["goals"]["away"] or 0
            context["h2h"].append({
                "home": translate_team(match["teams"]["home"]["name"]),
                "away": translate_team(match["teams"]["away"]["name"]),
                "score": f"{hg}-{ag}",
                "date": match["fixture"]["date"][:10],
            })

    if not isinstance(stats_data, Exception):
        context["statistics"] = stats_data.get("response", [])

    # Chama Claude
    try:
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=4000,
            system=ANALYSIS_PROMPT,
            messages=[{
                "role": "user",
                "content": f"Analise este jogo e retorne APENAS JSON válido, sem markdown:\n\n{json.dumps(context, ensure_ascii=False, indent=2)}"
            }]
        )
        text = response.content[0].text.strip()
        # Remove markdown se vier
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        analysis = json.loads(text)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise: {str(e)}")


# Serve frontend
@app.get("/")
async def root():
    # Tenta vários caminhos possíveis
    for path in ["index.html", "/app/index.html", "frontend/dist/index.html"]:
        if os.path.exists(path):
            return FileResponse(path)
    return {"status": "SeuTipster API running", "docs": "/docs"}
