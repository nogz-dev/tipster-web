# SeuTipster — Web App

## Stack
- Backend: Python + FastAPI
- Frontend: HTML/CSS/JS (single file)
- APIs: Football API v3 + Anthropic Claude

## Deploy no Railway

### 1. Cria novo repositório no GitHub
- Vai em github.com → New repository
- Nome: `tipster-web`
- Sobe os arquivos: `main.py`, `requirements.txt`, `Procfile`, `index.html`

### 2. Cria novo serviço no Railway
- Vai em railway.app → New Project → Deploy from GitHub repo
- Seleciona `tipster-web`

### 3. Adiciona variáveis de ambiente
No Railway, vai em Variables e adiciona:
```
FOOTBALL_API_KEY=sua_chave_aqui
ANTHROPIC_API_KEY=sua_chave_aqui
```

### 4. Deploy automático
O Railway detecta o Procfile e sobe automaticamente.
Você recebe um link tipo: `tipster-web.railway.app`

## Funcionalidades
- ✅ Jogos do dia com atualização automática
- ✅ Navegação por dia (7 dias)
- ✅ Jogos ao vivo em destaque
- ✅ Análise preditiva com IA (Claude)
- ✅ Probabilidades com gráfico de barras
- ✅ Estatísticas por time (forma, gols, cartões, escanteios)
- ✅ H2H — histórico de confrontos
- ✅ Palpites selecionados (6-8 por jogo)
- ✅ Design fiel ao Figma (preto + verde neon)
- ✅ Mobile-first, funciona como PWA
