# CLAUDE.md — WildLog

Guia completo do projeto para o Claude Code. Leia este arquivo antes de qualquer edição.

---

## O que é o WildLog

App Android de coleta de dados de fauna silvestre em campo, desenvolvido para biólogos e consultores ambientais brasileiros. Funciona **100% offline** (IndexedDB + SheetJS embutido), sem backend, sem login.

- **Plataforma:** Android (Capacitor 6 + HTML/CSS/JS single-file)
- **Repositório:** `github.com/gabrielsouzaalmeidan-del/fauna-campo`
- **Build:** GitHub Actions (`.github/workflows/build-apk.yml`)
- **Arquivo principal:** `index.html` (~9.500 linhas)
- **Versão atual:** v2.1

---

## Arquitetura

```
fauna-campo/
├── index.html              ← ÚNICO ARQUIVO DO APP (tudo inline)
├── CLAUDE.md               ← Este arquivo
├── .github/
│   └── workflows/
│       └── build-apk.yml   ← Gera APK via GitHub Actions
└── (gerado pelo Capacitor)
    ├── android/
    └── package.json
```

### Por que um único arquivo?

O Capacitor copia `www/index.html` para o APK. O SheetJS (XLSX) está **embutido inline** no HTML para garantir funcionamento offline. Não há bundler, webpack ou build step — o HTML é o app.

---

## Estrutura do index.html

```
<head>
  <style> ← CSS completo (~2.300 linhas) — Field Pro + Nature Dark
  <script> ← SheetJS embutido (~640KB)

<body>
  <div class="header">        ← Header fixo (logo, dark mode) — FUNDO BRANCO (Field Pro)
  <div id="ctx-bar">          ← Barra de contexto ativo + pill GPS ao vivo
  <div id="offline-bar">      ← Indicador offline
  <div id="sync-indicator">   ← Toast de sync

  <!-- 7 PANELS (abas) -->
  <div class="panel" id="panel-escanear">
  <div class="panel" id="panel-manual">
  <div class="panel" id="panel-biometria">
  <div class="panel" id="panel-campanhas">
  <div class="panel" id="panel-dashboard">
  <div class="panel" id="panel-registros">
  <div class="panel" id="panel-enviar">

  <nav class="nav-bar">       ← Nav FORA dos panels (root level) — FUNDO BRANCO (Field Pro)
  <div id="sync-indicator">
  <div id="toast">

  <script> ← JS completo (~5.200 linhas)
```

### Regra crítica de estrutura HTML

A `<nav class="nav-bar">` DEVE estar no **root level** (depth=0), fora de qualquer `<div>`. Se ficar dentro de um panel (que tem `display:none`), a nav some da tela.

---

## Design — Dois temas visuais

### Modo Normal → Field Pro
- Header e nav-bar com **fundo branco**, borda cinza sutil
- Variáveis: `--verde-medio: #16a34a`, `--areia: #f9fafb`, `--borda: #e5e7eb`, `--texto: #111827`
- Inputs brancos com borda cinza, foco verde + glow `rgba(22,163,74,0.12)`
- Cards brancos, sombra mínima
- record-item: accent line `3px` verde à esquerda
- section-header: linha divisória `::after`

### Dark Mode → Nature Dark (ativa ao ligar "Tela Escura")
- `body.dark-mode`: `--areia: #0a1a0a`, `--verde-medio: #4ade80`, `--texto: #d1fae5`
- Header/nav: `#0d2b0d`, logo/ícones ativos `#4ade80`
- Cards: `#1a2e1a`, border `#2d5a2d`
- 99+ seletores dark-mode para a paleta Nature Dark

---

## Módulos do App (7 abas)

| Aba | Panel ID | Função principal |
|-----|----------|-----------------|
| 📷 Scan | `panel-escanear` | OCR de fichas via câmera + IA |
| 📝 Manual | `panel-manual` | Formulário de registro + MacKinnon inline |
| 📏 Bio | `panel-biometria` | Morfometria por grupo (5 sub-abas) |
| 🗂️ Camp. | `panel-campanhas` | Projetos, campanhas e pontos amostrais |
| 📊 Resumo | `panel-dashboard` | Dashboard gráfico (donut + barras) |
| 📋 Dados | `panel-registros` | Lista de registros com filtros rápidos |
| 📤 Enviar | `panel-enviar` | Exportação XLSX + perfil do consultor |

---

## Formulário Manual — Estrutura Crítica

```html
<div class="panel" id="panel-manual">
  <div class="card">
    <!-- Seção Projeto -->
    <!-- Seção Local e Tempo -->
    <!-- Seção Metodologia -->
    <div class="field-group">
      <label>Método</label>
      <select id="m-metodo" onchange="onMetodoChange(this.value)"
                            oninput="onMetodoChange(this.value)">
    </div>
    <div class="field-group" id="manual-tipo-group">  ← some no MacKinnon
      <label>Tipo de registro</label>
      <select id="m-tipo">
    </div>

    <!-- MacKinnon INLINE (antes do bio-wrap) -->
    <div id="mck-inline-block" style="display:none">
      ... módulo MacKinnon completo ...
    </div>

    <!-- Dados Biológicos (some no MacKinnon) -->
    <div id="manual-bio-wrap">
      <div class="card">
        <div class="card-title">
          <span id="bio-section-icon">🐦</span>   ← ícone dinâmico por classe (Aves = 🐦)
          <span id="bio-section-label"> Dados biológicos</span>
        </div>
      </div>
    </div>
  </div>
</div>
```

### Ícones por Classe (CLASSE_ICONE)
- Aves: `🐦`  Mammalia: `🐾`  Reptilia: `🦎`  Amphibia: `🐸`  Pisces: `🐟`

### onMetodoChange — lógica central

```javascript
function onMetodoChange(val) {
  // Persiste no IDB como metodo_padrao
  if (val) idbPut('config', { _id: 'metodo_padrao', valor: val }).catch(()=>{});
  const isMck = val === 'Listas de Mackinnon';
  mckBlock.style.display  = isMck ? 'block' : 'none';
  biowrap.style.display   = isMck ? 'none'  : '';
  tipoGroup.style.display = isMck ? 'none'  : '';
}
```

**Métodos disponíveis no select:**
Listas de Mackinnon · Ponto de escuta · Censo por transecto · Busca ativa · Encontro ocasional · Camera trap · Rede de neblina · Armadilha · Pitfall · Procura limitada por tempo · Observação embarcada

---

## Funções JavaScript Críticas

### Inicialização
```javascript
async function init()              // carrega IDB, config, perfil, restaura método salvo
function irPara(panel, btn)        // navegação — sincroniza ctx-metodo → m-metodo
function loadDarkMode()            // restaura preferência de dark mode
```

### Dados / IDB
```javascript
async function idbPut(store, obj)       // salvar no IndexedDB
async function idbGet(store, id)        // ler um item pelo id
async function idbGetAll(store)         // ler todos do store
async function salvarDados()            // persiste registros[]
async function carregarDados()          // carrega registros[] do IDB
function normalizarRegistro(r)          // padroniza campos (ATENÇÃO: renomeia horario→hora)
```

### ⚠️ Armadilha: normalizarRegistro

```javascript
// normalizarRegistro DELETA r.horario e cria r.hora
// gerarXLSX deve usar: r.hora || r.horario
if (n.horario !== undefined && n.hora === undefined) {
  n.hora = n.horario;
  delete n.horario;
}
```

### Exportação XLSX
```javascript
function baixarXLSX()    // verifica XLSX disponível + null check + try-catch
function gerarXLSX()     // monta workbook: aba 'BANCO DE DADOS' + abas de biometria por grupo
function nomeArquivo()   // ex: "FAUNA_2026-05-10.xlsx"
```

**Estrutura da planilha (26 colunas — FASE foi removida):**
```
PROJETO | CAMPANHA | ÁREA | PONTO | ZONA | UTM(X) | UTM(Y) |
DATA | HORÁRIO | PERÍODO | ESTAÇÃO | MÉTODO | TIPO REG. | DESTINAÇÃO |
MICROHABITAT | CLASSE | ORDEM | FAMÍLIA | ESPÉCIE | Nº INDIV. | SEXO |
IUCN | MMA | NOTÁVEL | CONSULTOR | OBSERVAÇÕES
```

**Abas de biometria:** AVIF (Avifauna) · MAST (Mastofauna) · HERP (Herpetofauna) · ICTI (Ictiofauna) · QUIR (Quiropterofauna)

### GPS
```javascript
function applyGpsResult(fieldId, metaId, detailId, pos, isFallback)
// Após capturar GPS, atualiza pill no ctx-bar com zona UTM e precisão em metros
```

---

## IndexedDB — Stores

| Store | Conteúdo |
|-------|----------|
| `registros` | Registros manuais de fauna |
| `biometria` | Registros de biometria |
| `campanhas` | Campanhas criadas |
| `pontos` | Pontos amostrais |
| `config` | Configurações (inclui `metodo_padrao`) |
| `perfil` | Dados do consultor |

---

## CSS — Variáveis (Field Pro — modo normal)

```css
--verde-medio: #16a34a   --verde-claro: #22c55e   --verde-suave: #f0fdf4
--verde-borda: #bbf7d0   --borda: #e5e7eb          --areia: #f9fafb
--texto: #111827         --texto-suave: #374151    --branco: #ffffff
--perigo: #dc2626        --sucesso: #16a34a        --radius: 10px
```

**⚠️ Não adicionar novos `var(--x)` sem definir no `:root` — causa campos sem borda.**

---

## Filtros na Aba Dados

Chips disponíveis: Todos · 🐦 Aves · 🦁 Mamíf. · 🦎 Répteis · 🐸 Anfíb. · 🐟 Peixes · ⭐ Notáveis · 📅 Hoje · 📅 Semana · 🗂️ Campanha

---

## Regras de Validação

```python
# 1. JS Sintaxe
node --check /tmp/wl.js

# 2. HTML depth (divs balanceados)
d = html.count('<div') - html.count('</div>')  # deve ser 0

# 3. Nav no root
nd = nb.count('<div') - nb.count('</div>')  # deve ser 0 antes da <nav>

# 4. CSS vars definidas
undef = used_vars - def_vars  # deve ser vazio
```

---

## Bugs Históricos (não repetir)

| Bug | Causa | Fix |
|-----|-------|-----|
| Nav sumia | `<nav>` dentro de um `<div class="panel">` | Mover nav para root level |
| Exportação vazia | `r.horario` deletado por `normalizarRegistro` | Usar `r.hora \|\| r.horario` |
| Exportação travava | `XLSX.writeFile(null, ...)` sem null-check | Verificar `if (!wb) return` |
| MacKinnon não aparecia | `onMetodoChange` não chamado no carregamento | Chamar no `init()` e no `irPara()` |
| Campos sem borda | `var(--borda)` usada mas não definida no `:root` | Sempre definir vars no `:root` |
| `async async function salvarBio` | Fix de async aplicado 2x | Verificar duplicatas |
| Colunas XLSX desalinhadas | cabeçalho vs return | Sempre contar colunas = campos |
| FASE sempre vazia | Coluna no cabeçalho sem campo no form | Coluna removida (v2.1) |
| Bio não exportada | Filtro usava `r._grupo` (inexistente, campo é `r._tipo`) | Corrigido para `r._tipo` |
| Método não salvo | parseInt fallback `\|\| 0` | Corrigido para `\|\| 1` |

---

## Features Implementadas (v2.1)

- ✅ Dashboard gráfico (donut chart canvas puro + barras por ponto + estado vazio orientativo)
- ✅ Entrada por voz (Web Speech API)
- ✅ Histórico de espécies recentes (chips clicáveis)
- ✅ Filtros rápidos: grupos taxonômicos + notáveis + **Hoje / Semana / Campanha**
- ✅ Marcador de espécie notável (⭐ persistido no IDB)
- ✅ Badge IUCN + MMA automático
- ✅ MacKinnon integrado como método inline
- ✅ Ícone dinâmico por Classe
- ✅ Barra de contexto ativo (ctx-bar) com **pill GPS ao vivo**
- ✅ Barra offline inteligente
- ✅ Cards de registro ricos
- ✅ SheetJS embutido inline
- ✅ GPS nativo Android (Capacitor) com fallback web
- ✅ Dark mode completo — Nature Dark (alta legibilidade em campo)
- ✅ RECORD_AUDIO no AndroidManifest
- ✅ Exportação XLSX com **abas de biometria por grupo**
- ✅ Método amostral **persistido entre sessões** (IDB config)
- ✅ Web Share API para registros individuais
- ✅ Design Field Pro (modo normal) — branco, profissional

## Pendências

- [ ] Verificar "WildLog" no INPI (Classe 09 e 42)
- [ ] Modularizar o index.html (separar em arquivos por feature)

---

## Build APK

O workflow `.github/workflows/build-apk.yml`:
1. Cria `www/index.html` a partir do `index.html` da raiz
2. Instala e copia SheetJS para `www/xlsx.full.min.js` (fallback)
3. Instala Capacitor e adiciona plataforma Android
4. Compila com Gradle e gera `WildLog.apk`
5. Publica como GitHub Release

Para gerar novo APK: fazer push na branch `main` ou disparar manualmente em **Actions → Run workflow**.

---

## Testes

```bash
pip install playwright
playwright install chromium
python3 tests/test_wildlog.py
```

---

## Contato

Desenvolvido por **Gabriel Almeida** — biólogo e consultor ambiental, Ceará/BR.
