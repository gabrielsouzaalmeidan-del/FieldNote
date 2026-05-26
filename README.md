# FieldNote — App de Coleta de Fauna Silvestre

App Android para coleta de dados de fauna em campo, desenvolvido para biólogos e consultores ambientais brasileiros.
Funciona **100% offline** — sem backend, sem login, sem internet.

---

## Baixar o APK

### Releases (recomendado)
1. Clique na aba **[Releases](../../releases)** (lado direito desta página)
2. Baixe o `FieldNote.apk` da versão mais recente
3. Instale no celular Android

### Actions (build mais recente)
1. Clique na aba **[Actions](../../actions)**
2. Abra o build mais recente com ✅ verde
3. Role até **Artifacts** → baixe **FieldNote-APK**
4. Extraia o ZIP e instale o `.apk`

### Versão web (navegador)

Acesse sem instalar em qualquer dispositivo:
```
https://gabrielsouzaalmeidan-del.github.io/FieldNote/
```

---

## Instalar no Android

1. Transfira o `.apk` para o celular (WhatsApp, Drive, cabo USB)
2. **Configurações → Segurança → Instalar apps desconhecidos** → Permitir
3. Abra o `.apk` e toque em **Instalar**

---

## Funcionalidades — v2.1

### Registro de campo
- **Formulário manual** — espécie, GPS, método, destinação, microhabitat
- **1.254+ espécies do Ceará** com autocomplete (nome científico + popular)
- **Status de conservação automático** — MMA, IUCN e CE (Decreto 32.548/2018)
- **GPS nativo Android** com fallback web — coordenadas UTM ao vivo
- **Entrada por voz** — ditado de espécie via Web Speech API
- **Histórico de espécies recentes** — chips clicáveis para reutilização rápida
- **Marcador notável** ⭐ — destaque persistido para espécies de interesse

### Métodos amostrais
- Ponto de escuta · Censo por transecto · Busca ativa · Encontro ocasional
- Camera trap · Rede de neblina · Armadilha · Pitfall · Procura limitada por tempo
- **Listas de Mackinnon** integradas inline — registros e controle de lista sem sair do formulário

### Biometria
- 5 grupos: **Avifauna · Mastofauna · Herpetofauna · Ictiofauna · Quiropterofauna**
- Campos morfométricos específicos por grupo

### Campanhas e pontos
- Cadastro de projetos, campanhas e pontos amostrais
- Cards colapsáveis para navegação rápida
- Contexto ativo sempre visível na barra superior

### Dados e exportação
- **Aba Dados** com sub-abas Resumo (dashboard) e Registros
- Filtros rápidos: grupos taxonômicos · Notáveis · Hoje · Semana · Campanha
- **Dashboard** com gráfico donut e barras por ponto amostral
- **Exportação XLSX** — aba principal + abas de biometria por grupo (SheetJS embutido)
- Compartilhamento de registros individuais via Web Share API

### Design e usabilidade
- **Field Pro** (modo normal) — interface limpa, profissional, branca
- **Nature Dark** (modo escuro) — alta legibilidade em campo noturno
- Funciona offline completo via IndexedDB
- Método amostral persistido entre sessões

---

## Atualizar o app

Qualquer push no branch `main` dispara o build automaticamente (~20 min).
O APK novo é publicado como GitHub Release.

Para acompanhar o build:
```powershell
.\check-build.ps1
```

---

## Desenvolvimento

### Estrutura
```
FieldNote/
├── index.html              ← app completo (HTML + CSS + JS, ~11.700 linhas)
├── android-src/
│   └── MainActivity.java   ← suporte a download de arquivos no WebView
├── capacitor.config.json
├── package.json
├── check-build.ps1         ← monitora o build no GitHub Actions
├── setup.ps1               ← configura o ambiente Claude Code em nova máquina
└── .github/workflows/
    └── build-apk.yml       ← gera APK via Capacitor 6 + Gradle
```

### Setup em novo computador
```powershell
git clone https://github.com/gabrielsouzaalmeidan-del/FieldNote.git
cd FieldNote
.\setup.ps1
```

### Gerar APK manualmente
Acesse **Actions → Build APK - FieldNote → Run workflow**.

---

*Desenvolvido por Gabriel Almeida — biólogo e consultor ambiental, Ceará/BR*
