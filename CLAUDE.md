# CLAUDE.md — WildLog v2.1

Guia completo do projeto para o Claude Code. **Leia este arquivo antes de qualquer edição.**

---

## O que é o WildLog

App Android de coleta de dados de fauna silvestre em campo, desenvolvido para biólogos e consultores ambientais brasileiros. Funciona **100% offline** (IndexedDB + SheetJS embutido), sem backend, sem login.

- **Plataforma:** Android (Capacitor 6) + PWA (GitHub Pages)
- **Repositório:** `github.com/gabrielsouzaalmeidan-del/fauna-campo`
- **Token GitHub:** configure com `git remote set-url origin https://SEU_TOKEN@github.com/gabrielsouzaalmeidan-del/fauna-campo`
- **Build:** GitHub Actions → `WildLog.apk` automático a cada push no `main`
- **PWA:** `https://gabrielsouzaalmeidan-del.github.io/fauna-campo/`
- **Arquivo principal:** `index.html` (~11.789 linhas, ~1.33MB)
- **Versão:** v2.1

---

## Arquitetura

```
fauna-campo/
├── index.html              ← ÚNICO ARQUIVO DO APP (tudo inline)
├── www/index.html          ← Cópia sincronizada (usada pelo Capacitor)
├── CLAUDE.md               ← Este arquivo
├── android-src/
│   └── MainActivity.java   ← DownloadListener para XLSX no Android
├── capacitor.config.json   ← appId: br.com.wildlog.app
├── package.json            ← Capacitor 6 + @capacitor/filesystem + share
└── .github/workflows/
    └── build-apk.yml       ← 16 steps, gera WildLog.apk
```

### ⚠️ Regra crítica: sempre sincronizar www/

Após editar `index.html`, sempre copiar para `www/index.html`:
```bash
cp index.html www/index.html
```
O Capacitor usa `www/` para gerar o APK. Se não sincronizar, o APK fica desatualizado.

### Por que um único arquivo?

O SheetJS (XLSX) está **embutido inline** no HTML (~640KB). Não há bundler — o HTML é o app.

---

## Estrutura do index.html

```
<head>
  <style>   ← CSS completo (~149KB) — Field Pro + Nature Dark
  <script>  ← Capacitor loader (164 chars)
  <script>  ← SheetJS embutido (~639KB)
  <script>  ← SW_CODE + registrarPWA (41KB)

<body>
  <div class="header">         ← 🌿 WildLog + online pill + dark toggle
  <div id="ctx-bar">           ← Chips: 🗂️Campanha · 📍Ponto · 🔬Método
  <div id="offline-bar">       ← Barra offline amarela
  
  <!-- 8 PANELS -->
  panel-escanear     ← OCR câmera
  panel-manual       ← Formulário registro + autocomplete espécies
  panel-biometria    ← Morfometria (5 grupos)
  panel-campanhas    ← Projetos, campanhas e pontos
  panel-dashboard    ← Sub-abas: 📊 Resumo | 📋 Registros N
  panel-mapa         ← Leaflet + OpenStreetMap
  panel-enviar       ← Export XLSX + perfil
  
  <nav class="nav-bar">        ← 6 abas: Scan/Manual/Bio/Dash/Mapa/Enviar
  
  <script>  ← JS principal (~457KB) — SPECIES_DB + todas as funções
```

### ⚠️ Regra crítica de estrutura HTML

O arquivo **DEVE** terminar com:
```html
</script>
</body>
</html>
```
Se faltar, o browser descarta todo o JS e as abas param de funcionar (`irPara is not defined`).

### ⚠️ Regra crítica da <nav>

A `<nav class="nav-bar">` DEVE estar no **root level** (depth=0), fora de qualquer `<div>`. Se ficar dentro de um panel, some da tela.

---

## Design Visual

### Modo Normal → Field Pro
- Header/nav branco, `border-bottom: 1px solid var(--borda)`
- `--verde-medio: #16a34a` · `--areia: #f9fafb` · `--borda: #e5e7eb` · `--texto: #111827`
- Inputs brancos, foco verde + glow `rgba(22,163,74,0.12)`
- Cards brancos, sombra mínima, record-item com accent line `3px` verde

### Dark Mode → Nature Dark
- `body.dark-mode`: `--areia: #0a1a0a` · `--verde-medio: #4ade80` · `--texto: #d1fae5`
- Header/nav: `#0d2b0d` · Cards: `#1a2e1a` · border: `#2d5a2d`

---

## Nav Bar (6 abas)

```
Scan | Manual | Bio | Dash | Mapa | Enviar
  0      1      2     3      4      5
```

- **Camp.** não tem botão — acessado via ctx-bar ou Dash > Acesso Rápido
- **Dados** não tem botão — é sub-aba interna do Dash
- `irPara('campanhas')` → marca Dash (idx 3) como active
- `irPara('registros')` → abre Dash na sub-aba Registros

---

## Dash: Sub-abas (📊 Resumo | 📋 Registros)

O `panel-dashboard` contém duas sub-abas gerenciadas por `mudarDashTab(tab)`:

```html
<div class="dash-tabs">
  <button class="dash-tab active" id="dtab-resumo">📊 Resumo</button>
  <button class="dash-tab" id="dtab-registros">📋 Registros <span id="dtab-badge">0</span></button>
</div>

<div id="dsub-resumo" class="dsub active">   ← Gráficos + stats + acesso rápido
<div id="dsub-registros" class="dsub">       ← Lista + filtros + biometria
```

### CSS crítico das sub-abas:
```css
#panel-dashboard { height: calc(100vh - 160px); display: flex; flex-direction: column; }
#panel-dashboard.active { display: flex !important; }
.dash-tabs { flex-shrink: 0; }
.dsub.active { display: block; flex: 1; overflow-y: auto; }
```

### ⚠️ Armadilha histórica do dsub-resumo:
O `dsub-resumo` precisa ter **todas as divs fechadas** antes do `<!-- /dsub-resumo -->`. Se faltar 1 `</div>`, o `dsub-registros` fica filho do resumo e fica invisível (rect 0,0,0,0).

---

## SPECIES_DB — Estado Atual (1.254 espécies)

```javascript
// Estrutura de cada entrada:
{ cl, or, fa, sp, np, ha, se, ca, gu,  // taxonomia + habitat/sensib
  mm, iu, ci,                           // MMA, IUCN, CITES
  bi, en, ce }                          // biomas, endemismo, ocorrência CE
```

| Campo | Desc | Total com dados |
|-------|------|----------------|
| `mm`  | MMA/SALVE | 84 espécies |
| `iu`  | IUCN | 175 espécies |
| `ci`  | CITES | 108 espécies |
| `ce`  | Ocorrência CE | 820 espécies |
| `en`  | Endemismo | 29 espécies |
| `bi`  | Biomas | 108 espécies |

**Fontes:** SBMz 2024, Inventário Aves CE 2021, Lista Répteis CE, Anfíbios CE, Portaria MMA 444/2014 (583 sp), Portaria MMA 1.667/2026 (305 peixes)

---

## APIs de Conservação (todas sem token)

Disparadas automaticamente ao selecionar espécie no autocomplete (se online):

```javascript
buscarDadosWeb()   // orquestra as 3 buscas em paralelo
buscarGBIF(sp)     // api.gbif.org — registros BR e CE
buscarInat(sp)     // api.inaturalist.org — obs CE (place_id=7155)
buscarCTFB(sp)     // fauna.jbrj.gov.br — status BR, biomas, estados
```

Cache em memória `_apiCache` para evitar repetição na sessão.

---

## Mapa Cartográfico (aba Mapa)

- Leaflet.js + OpenStreetMap carregado lazy (só quando aba abre)
- `utmParaLatLon(e, n, zone, letter)` — converte UTM → WGS84 (zonas 23-25 S, Brasil)
- `extrairCoords(r)` — extrai do campo `r.coord` ou `r.utm`
- Filtros por grupo taxonômico
- Popup com espécie, data, ponto, método, IUCN/MMA
- Requer internet para carregar tiles

---

## Exportação XLSX

```javascript
baixarXLSX()       // detecta Capacitor → usa Filesystem plugin; browser → blob URL
compartilharXLSX() // Web Share API com arquivo; fallback → baixarXLSX()
gerarXLSX()        // monta workbook: aba 'BANCO DE DADOS' + abas bio por grupo
nomeArquivo()      // ex: "FAUNA_2026-05-25.xlsx"
```

**Download no Android (Capacitor):**
1. `window.Capacitor.Plugins.Filesystem.writeFile()` → `/Documents/FAUNA_*.xlsx`
2. Se falhar → Web Share API (`navigator.share({files})`)
3. Se falhar → blob URL + `<a download>`

**Abas do XLSX:** BANCO DE DADOS · AVIF · MAST · HERP · ICTI · QUIR

---

## IndexedDB

**Nome:** `FaunaCampoDB` · **Versão:** `3`

| Store | KeyPath | Conteúdo |
|-------|---------|----------|
| `registros` | `_id` | Registros manuais |
| `biometria` | `_id` | Morfometria |
| `campanhas` | `_id` | Campanhas |
| `pontos` | `_id` | Pontos amostrais |
| `config` | `_id` | Config (inclui `metodo_padrao`, `apiKey`) |
| `perfil` | `_id` | Dados do consultor |

```javascript
async function idbGet(store, id)    // usa abrirDB() — NÃO usar db global direto
async function idbPut(store, obj)   // salva/atualiza
async function idbGetAll(store)     // lista todos
async function abrirDB()            // abre/migra o banco
```

---

## Persistência de dados (GH Pages / browser)

- `salvarDados()`: dupla garantia — IDB + localStorage
- `carregarDados()`: tenta IDB, fallback localStorage
- Service Worker: network-first, CACHE_NAME dinâmico (Date.now())
- Banner PWA aparece após 3s para usuários do browser (com instruções para instalar)

---

## Funções JavaScript Críticas

```javascript
// ── Inicialização ──────────────────────────────────────────────
async function init()                // carrega IDB, config, restaura método
function irPara(panel, btn)          // navegação principal
function loadDarkMode()              // restaura preferência dark mode

// ── Navegação especial ─────────────────────────────────────────
// irPara('registros') → abre Dash na sub-aba Registros
// irPara('campanhas') → abre Dash com btn[3] active
// irPara('dashboard') → inicializa sub-aba Resumo
// irPara('mapa')      → chama renderMapa()

// ── Dashboard ─────────────────────────────────────────────────
function mudarDashTab(tab)           // 'resumo' | 'registros'
function atualizarDtabBadge()        // atualiza contador no badge
function renderDashboard()           // gráficos + estat. (esconde quando vazio)
function atualizarDashInicio()       // saudação + stats zeradas

// ── Registros ─────────────────────────────────────────────────
function renderRegistrosFiltrado()   // lista os record-items com filtros
function filtrarDados(filtro, chip)  // todos/Aves/Mammalia/.../hoje/semana/campanha

// ── Autocomplete espécies ─────────────────────────────────────
function acOnInput(val)              // filtra SPECIES_DB em tempo real
function autoFillFromSpecies(s)      // preenche formulário + badges + busca APIs
function aplicarStatusConservacao(s) // exibe badges de IUCN/MMA/CITES/CE/endem/biomas
async function buscarDadosWeb()      // GBIF + iNat em background (auto, sem click)

// ── Formulário Manual ─────────────────────────────────────────
function onMetodoChange(val)         // alterna MacKinnon/normal, persiste no IDB
function adicionarManual()           // salva registro + chama salvarDados()
```

---

## CSS — Variáveis Principais (Field Pro)

```css
--verde-medio: #16a34a   --verde-claro: #22c55e   --verde-suave: #f0fdf4
--verde-borda: #bbf7d0   --borda: #e5e7eb          --areia: #f9fafb
--areia-escura: #f3f4f6  --texto: #111827          --texto-suave: #374151
--texto-muted: #6b7280   --branco: #ffffff          --radius: 10px
--radius-sm: 8px         --sombra: 0 1px 3px rgba(0,0,0,.07)
```

⚠️ **Não adicionar `var(--x)` sem definir no `:root`** — causa campos sem borda.

---

## Bugs Históricos (NÃO repetir)

| Bug | Causa | Fix |
|-----|-------|-----|
| Abas não funcionavam | `</script></body></html>` faltando no final | Sempre fechar o script no final |
| `irPara is not defined` | Script principal sem `</script>` | Idem |
| www/ desatualizado | Versão antiga versionada | `cp index.html www/index.html` |
| CSS legado sobrescrevia Field Pro | Bloco v2.0 após redesign | Removido |
| Offline-bar invisível no claro | `display:none` hardcoded | Removido |
| dsub-registros invisível | 1 `</div>` faltando no dsub-resumo → filho do pai errado | Fechar todas as divs |
| XLSX não baixava no Android | `XLSX.writeFile()` bloqueado no WebView | `Capacitor.Plugins.Filesystem` |
| Bio não exportada no XLSX | Filtro usava `r._grupo` (inexistente) | Corrigido para `r._tipo` |
| Config store keyPath errado | `'chave'` em vez de `'_id'` | Corrigido, IDB_VERSION → 3 |
| idbGet sem abrirDB | Usava variável global `db` | Usa `abrirDB()` agora |
| YAML workflow quebrado | Heredoc Java inline no YAML | Arquivo separado `android-src/` |
| Dados somem no browser | idbGet + SW cache fixo + store config errada | 4 bugs corrigidos |

---

## Validação (rodar antes de commitar)

```bash
# 1. JS sem erros de sintaxe
python3 -c "
import re, subprocess
with open('index.html') as f: html = f.read()
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
with open('/tmp/check.js','w') as f: f.write('\n'.join(scripts))
res = subprocess.run(['node','--check','/tmp/check.js'], capture_output=True, text=True)
print('✅ JS OK' if res.returncode==0 else '❌ '+res.stderr[:200])
"

# 2. HTML divs balanceados (no HTML puro, excluindo scripts)
python3 -c "
import re
with open('index.html') as f: html = f.read()
hn = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
hn = re.sub(r'<style[^>]*>.*?</style>', '', hn, flags=re.DOTALL)
d = hn.count('<div') - hn.count('</div>')
print(f'Divs: {d} (✅ 0 = ok)')
"

# 3. Nav no root level
python3 -c "
import re
with open('index.html') as f: html = f.read()
npos = html.find('<nav class=\"nav-bar\">')
nb = re.sub(r'<script[^>]*>.*?</script>', '', html[:npos], flags=re.DOTALL)
nb = re.sub(r'<style[^>]*>.*?</style>', '', nb, flags=re.DOTALL)
print(f'Nav depth: {nb.count(\"<div\") - nb.count(\"</div>\")} (✅ 0 = ok)')
"

# 4. Arquivo termina corretamente
tail -3 index.html

# 5. www/ sincronizado
cp index.html www/index.html && echo "✅ www/ ok"
```

---

## Build APK

O workflow `.github/workflows/build-apk.yml` (16 steps):
1. Checkout + Java 17 + Node 22
2. Copiar `index.html` → `www/index.html`
3. `npm install` (Capacitor + @capacitor/filesystem + @capacitor/share)
4. `npx cap add android` + `npx cap sync android`
5. Copiar `android-src/MainActivity.java` (DownloadListener para XLSX)
6. Substituir AndroidManifest (permissões + requestLegacyExternalStorage)
7. Gradle build → `WildLog.apk`
8. GitHub Release automático

Para gerar: push no `main` ou Actions → Run workflow.

---

## Features Implementadas (v2.1)

- ✅ 1.254 espécies no SPECIES_DB com dados de conservação
- ✅ Badges automáticos: IUCN, MMA, CITES, CE, Endemismo, Biomas
- ✅ Busca automática GBIF + iNaturalist ao selecionar espécie (sem token)
- ✅ Mapa cartográfico Leaflet + OpenStreetMap (aba 🗺️ Mapa)
- ✅ Conversão UTM → lat/lon (zonas 23-25 S)
- ✅ Dash com sub-abas: 📊 Resumo | 📋 Registros N
- ✅ Filtros de data: Hoje / Semana / Campanha
- ✅ Exportação XLSX com abas de biometria por grupo
- ✅ Compartilhamento via Web Share API (arquivo real)
- ✅ Download XLSX via Capacitor.Plugins.Filesystem
- ✅ Método amostral persistido entre sessões
- ✅ Field Pro (claro) + Nature Dark (escuro)
- ✅ GPS nativo + pill ao vivo no ctx-bar
- ✅ MacKinnon integrado como método inline
- ✅ Entrada por voz (Web Speech API)
- ✅ Persistência IDB + localStorage (dupla garantia)
- ✅ PWA instalável + banner de aviso no browser
- ✅ Service Worker network-first com versionamento dinâmico

## Pendências

- [ ] Verificar "WildLog" no INPI (Classe 09 e 42)
- [ ] Completar IUCN para as ~1.000 espécies sem status (API IUCN v4 requer token gratuito em api.iucnredlist.org)
- [ ] Testar Capacitor.Plugins.Filesystem no APK real (Android Downloads)
- [ ] Login por perfil de consultor (cada biólogo vê só seus dados)

---

## Contato

Desenvolvido por **Gabriel Almeida** — biólogo e consultor ambiental, Ceará/BR.
