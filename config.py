# =============================================================================
#  config.py — ARQUIVO DE CONFIGURAÇÃO PRINCIPAL
#  Edite apenas este arquivo. Não mexa nos outros a menos que necessário.
# =============================================================================
#
#  COMO PEGAR OS TOKENS NO NAVEGADOR:
#  1. Abra o site no Chrome/Edge e faça login
#  2. Pressione F12 → aba "Network"
#  3. Recarregue a página ou clique em qualquer botão
#  4. Clique em qualquer requisição da lista
#  5. Na aba "Headers" → seção "Request Headers"
#  6. Copie os valores dos tokens para os campos abaixo
#
# =============================================================================


# -----------------------------------------------------------------------------
#  1. URL DA API
# -----------------------------------------------------------------------------

# URL completa do endpoint GET que retorna a tabela
# Exemplo: "https://sistema.empresa.com.br/api/relatorio/tabela"
URL_API = "https://COLE_A_URL_AQUI"

# Se a URL tiver parâmetros de query string, coloque-os aqui como dicionário
# Exemplo: {"data_inicio": "2024-01-01", "pagina": "1"}
# Deixe {} se não houver parâmetros
PARAMS = {}


# -----------------------------------------------------------------------------
#  2. TOKENS DE AUTENTICAÇÃO
#  Cole aqui os valores que você encontrar no DevTools (F12 → Network → Headers)
# -----------------------------------------------------------------------------

# Token de sessão GTA
# Nome do header como aparece no DevTools (ex: "X-GTA-Session", "gta-session-token")
HEADER_NOME_SESSION_TOKEN = "X-GTA-Session"     # ← ajuste o nome se necessário
SESSION_TOKEN             = "COLE_O_TOKEN_AQUI"  # ← cole o valor do token

# Token XSRF (proteção contra CSRF)
# Nome do header como aparece no DevTools (ex: "X-XSRF-TOKEN", "X-CSRF-Token")
HEADER_NOME_XSRF_TOKEN = "X-XSRF-TOKEN"         # ← ajuste o nome se necessário
XSRF_TOKEN             = "COLE_O_TOKEN_AQUI"     # ← cole o valor do token

# Token extra da rede privada (VPN/sistema interno)
# Se não houver, deixe USAR_TOKEN_EXTRA = False
USAR_TOKEN_EXTRA       = True
HEADER_NOME_TOKEN_EXTRA = "Authorization"        # ← ajuste o nome se necessário
TOKEN_EXTRA            = "Bearer COLE_O_TOKEN_AQUI"  # ← cole o valor

# Cookies adicionais (se além dos headers o site também usar cookies)
# Formato: {"nome_cookie": "valor", "outro_cookie": "valor"}
# Deixe {} se não precisar
COOKIES = {}


# -----------------------------------------------------------------------------
#  3. HEADERS FIXOS (não mudam)
#  Copie do DevTools os headers que aparecem em TODAS as requisições
# -----------------------------------------------------------------------------

HEADERS_FIXOS = {
    "User-Agent"  : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36",
    "Accept"          : "text/html,application/json,*/*",
    "Accept-Language" : "pt-BR,pt;q=0.9",
    "Connection"      : "keep-alive",
    # Adicione outros headers fixos que aparecerem no DevTools:
    # "Referer": "https://sistema.empresa.com.br/",
    # "Origin" : "https://sistema.empresa.com.br",
}


# -----------------------------------------------------------------------------
#  4. DETECÇÃO DE TOKEN EXPIRADO
#  O programa usa esses critérios para saber quando o token venceu
# -----------------------------------------------------------------------------

# Códigos HTTP que indicam token expirado/sem autenticação
HTTP_CODES_EXPIRADO = [401, 403]

# Textos que podem aparecer no corpo da resposta indicando expiração
# (insensível a maiúsculas — adicione termos que o seu sistema retorna)
TEXTOS_TOKEN_EXPIRADO = [
    "unauthorized",
    "token expired",
    "session expired",
    "invalid token",
    "not authenticated",
    "401",
    "403",
    "acesso negado",
    "sessão expirada",
    "token inválido",
]


# -----------------------------------------------------------------------------
#  5. PARSING DA TABELA
# -----------------------------------------------------------------------------

# Índice da tabela HTML na página (0 = primeira tabela encontrada)
INDICE_TABELA = 0

# Se a API retornar JSON em vez de HTML, mude para True
# Nesse caso, configure CAMINHO_JSON abaixo
RESPOSTA_E_JSON = False

# Se RESPOSTA_E_JSON = True, caminho para a lista de dados dentro do JSON
# Exemplo: se o JSON for {"data": {"rows": [...]}} → ["data", "rows"]
# Deixe [] se a resposta já for uma lista direta
CAMINHO_JSON = []


# -----------------------------------------------------------------------------
#  6. EXCEL
# -----------------------------------------------------------------------------

# Caminho e nome do arquivo Excel de saída
# Use caminho absoluto para garantir que sempre salve no lugar certo
# Exemplo Windows: r"C:\Users\SeuNome\Desktop\relatorio.xlsx"
ARQUIVO_EXCEL = "relatorio.xlsx"

# Nome da aba na planilha
NOME_ABA = "Dados"

# Se True  → cada atualização SOBRESCREVE os dados anteriores (snapshot atual)
# Se False → cada atualização ACUMULA linhas com timestamp (histórico completo)
MODO_SOBRESCREVER = True

# Se True, adiciona uma coluna "Atualizado em" com o horário de cada coleta
ADICIONAR_COLUNA_TIMESTAMP = True


# -----------------------------------------------------------------------------
#  7. AGENDAMENTO
# -----------------------------------------------------------------------------

# Intervalo de atualização em minutos (padrão: 60 = de hora em hora)
INTERVALO_MINUTOS = 60

# Se True, executa uma coleta imediatamente ao iniciar (sem esperar o intervalo)
COLETAR_AO_INICIAR = True


# -----------------------------------------------------------------------------
#  8. PROXY CORPORATIVO
#  Se sua rede exige proxy para acessar sistemas internos, configure aqui
# -----------------------------------------------------------------------------

USAR_PROXY = False

# Formato: "http://usuario:senha@proxy.empresa.com:8080"
# Se não precisar de autenticação: "http://proxy.empresa.com:8080"
PROXY_HTTP  = "http://proxy.empresa.com:8080"
PROXY_HTTPS = "http://proxy.empresa.com:8080"


# -----------------------------------------------------------------------------
#  9. CONFIGURAÇÕES TÉCNICAS (raramente precisam ser alteradas)
# -----------------------------------------------------------------------------

# Timeout da requisição em segundos
TIMEOUT = 30

# Verificar certificado SSL (False apenas em redes internas com cert autoassinado)
VERIFICAR_SSL = True

# Arquivo de log
ARQUIVO_LOG = "coletor.log"
