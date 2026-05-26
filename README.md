# 🌿 Fauna Campo — App de Coleta Faunística

App mobile para coleta de dados de fauna em campo.  
Funciona **online e offline** no Android.

---

## 📱 Como baixar o APK

### Opção 1 — Releases (mais fácil)
1. Clique na aba **Releases** (lado direito desta página)
2. Baixe o arquivo `.apk` da versão mais recente
3. Instale no celular Android

### Opção 2 — Actions (build mais recente)
1. Clique na aba **Actions** acima
2. Clique no build mais recente (com ✅ verde)
3. Role até **Artifacts**
4. Baixe **FaunaCampo-APK**
5. Extraia o ZIP e instale o `.apk`

---

## 🔧 Como instalar no celular Android

1. Transfira o `.apk` para o celular (WhatsApp, Drive, cabo USB)
2. No celular: **Configurações → Segurança → Instalar apps desconhecidos** → Permitir
3. Abra o arquivo `.apk` e toque em **Instalar**
4. Pronto — o app aparece na tela inicial com o ícone 🌿

---

## 🔄 Como atualizar o app

Quando uma nova versão do `index.html` for enviada para este repositório,
o APK é gerado **automaticamente em ~5 minutos**.

Para atualizar:
1. Substitua `www/index.html` pela nova versão
2. Faça commit e push
3. Aguarde o build terminar na aba **Actions**
4. Baixe e instale o novo APK

---

## 🌐 Versão web (navegador)

Acesse pelo navegador em qualquer dispositivo:
```
https://gabrielsouzaalmeidan-del.github.io/fauna-campo/
```

---

## 📋 Funcionalidades

- **Coleta manual** — observações com GPS, foto, método, destinação
- **Biometria** — 5 grupos (Avifauna, Mastofauna, Herpe, Ictio, Quirópteros)
- **Listas de Mackinnon** — metodologia com cálculo de IFL
- **GPS automático** — coordenadas UTM com conversão WGS84
- **1.254 espécies** do Ceará no autocomplete
- **Campanhas e pontos amostrais** — com importação KML/KMZ/GPX
- **Funciona offline** — IndexedDB para armazenamento local
- **Dashboard** — índices ecológicos e curva de acumulação
- **Perfil do consultor** — identificação em todos os registros

---

*Fauna Campo v17 — gabrielsouzaalmeidan-del*
