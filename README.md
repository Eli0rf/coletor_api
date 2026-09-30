# 📊 Coletor API → Excel Automation

Uma solução em Python robusta, modular e resiliente desenvolvida para automação de extração de dados (*web scraping* / requisições HTTP) a partir de endpoints protegidos por autenticação e exportação automatizada para planilhas do Microsoft Excel.

![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)

---

## 📌 Visão Geral

O **coletor_api** automatiza a captura contínua de relatórios e tabelas provenientes de sistemas corporativos e APIs restritas. O script lida com múltiplos métodos de autenticação (Tokens de Sessão GTA, XSRF Tokens, Headers de VPN/Rede Privada), trata a perda de sessão/token expirado com alertas visuais e formata automaticamente a planilha final com padrões visuais profissionais (padrão zebra, cabeçalho estilizado e colunas auto-ajustáveis).

---

## ✨ Funcionalidades Principais
- 🔄 **Parsing Inteligente (HTML & JSON):** Converte tabelas HTML (`<table>`) capturadas de páginas web ou arrays/objetos JSON em estruturas tabulares.
- 🎨 **Exportação Excel Estilizada (via OpenPyXL):**
  - Formatação visual com cabeçalhos personalizados e padrão *zebra*.
  - Ajuste automático de largura de colunas.
  - Fixação do painel de cabeçalho (`freeze_panes = "A2"`).
  - Suporte aos modos **Sobrescrever** (snapshot atual) ou **Acumulativo** (histórico temporal com timestamp).
- 🛡️ **Tratamento de Exceções & Detecção de Sessão Expirada:** Identifica respostas HTTP 401/403 ou textos de erro no corpo do retorno, registrando avisos no arquivo de log e dentro da própria planilha Excel sem quebrar a execução contínua.
- ⏱️ **Agendador Integrado:** Loop de execução com intervalos customizáveis (ex.: coletas de hora em hora) e tratamento limpo de interrupções (`Ctrl+C`).

---

## 🛠️ Arquitetura do Projeto

```plaintext
coletor_api/
├── config.py     # Central de configurações (URLs, tokens, proxy e opções do Excel)
├── coletor.py    # Módulo de requisições HTTP, gestão de headers e parsing (HTML/JSON)
├── excel.py      # Módulo de manipulação e estilização do Excel via OpenPyXL
└── main.py       # Ponto de entrada (CLI, agendador, gerenciamento de logs e exceções)
