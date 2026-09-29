# =============================================================================
#  coletor.py — MÓDULO DE COLETA DE DADOS
#  Responsável por:
#    - Montar os headers com os tokens configurados
#    - Fazer a requisição GET na API
#    - Detectar quando o token expirou
#    - Fazer o parsing da resposta (HTML ou JSON)
#    - Retornar os dados como lista de dicionários
# =============================================================================

import logging
import json
import requests
from bs4 import BeautifulSoup

import config

log = logging.getLogger(__name__)


# =============================================================================
#  MONTAGEM DOS HEADERS
# =============================================================================

def montar_headers() -> dict:
    """
    Combina os headers fixos com os tokens de autenticação configurados.
    Retorna um dicionário pronto para passar ao requests.
    """
    headers = dict(config.HEADERS_FIXOS)  # copia os headers fixos

    # Adiciona o token de sessão GTA
    if config.SESSION_TOKEN and config.SESSION_TOKEN != "COLE_O_TOKEN_AQUI":
        headers[config.HEADER_NOME_SESSION_TOKEN] = config.SESSION_TOKEN

    # Adiciona o token XSRF
    if config.XSRF_TOKEN and config.XSRF_TOKEN != "COLE_O_TOKEN_AQUI":
        headers[config.HEADER_NOME_XSRF_TOKEN] = config.XSRF_TOKEN

    # Adiciona o token extra da rede privada (se configurado)
    if config.USAR_TOKEN_EXTRA and config.TOKEN_EXTRA and "COLE_O_TOKEN_AQUI" not in config.TOKEN_EXTRA:
        headers[config.HEADER_NOME_TOKEN_EXTRA] = config.TOKEN_EXTRA

    return headers


def montar_proxies() -> dict | None:
    """
    Retorna o dicionário de proxies se USAR_PROXY estiver ativo,
    ou None para conexão direta.
    """
    if not config.USAR_PROXY:
        return None
    return {
        "http" : config.PROXY_HTTP,
        "https": config.PROXY_HTTPS,
    }


# =============================================================================
#  DETECÇÃO DE TOKEN EXPIRADO
# =============================================================================

def token_expirado(response: requests.Response) -> bool:
    """
    Verifica se a resposta indica que o token expirou ou é inválido.
    Checa:
      1. Código HTTP (401, 403, ou outros configurados)
      2. Texto no corpo da resposta (lista TEXTOS_TOKEN_EXPIRADO)
    """
    # Checa o código HTTP
    if response.status_code in config.HTTP_CODES_EXPIRADO:
        log.warning(
            "Token expirado detectado via HTTP %d.", response.status_code
        )
        return True

    # Checa o corpo da resposta por textos indicativos
    corpo = response.text.lower()
    for texto in config.TEXTOS_TOKEN_EXPIRADO:
        if texto.lower() in corpo:
            log.warning(
                "Token expirado detectado via texto na resposta: '%s'.", texto
            )
            return True

    return False


# =============================================================================
#  PARSING DA RESPOSTA
# =============================================================================

def _extrair_de_html(html: str) -> list[dict]:
    """
    Faz o parsing de uma resposta HTML e extrai a tabela configurada.
    Retorna lista de dicionários {coluna: valor}.
    """
    soup = BeautifulSoup(html, "lxml")
    tabelas = soup.find_all("table")

    if not tabelas:
        raise ValueError(
            "Nenhuma tabela <table> encontrada na resposta HTML. "
            "Verifique se a URL está correta e se o login funcionou."
        )

    idx = config.INDICE_TABELA
    if idx >= len(tabelas):
        raise IndexError(
            f"INDICE_TABELA={idx} inválido. "
            f"A página tem {len(tabelas)} tabela(s) (índices 0–{len(tabelas)-1})."
        )

    tabela = tabelas[idx]
    cabecalho = []
    linhas = []

    # Extrai cabeçalho do <thead> ou da primeira linha com <th>
    thead = tabela.find("thead")
    if thead:
        cabecalho = [th.get_text(strip=True) for th in thead.find_all("th")]

    # Itera pelas linhas do corpo da tabela
    corpo = tabela.find("tbody") or tabela
    for tr in corpo.find_all("tr"):
        celulas = tr.find_all(["td", "th"])
        if not celulas:
            continue

        valores = [c.get_text(strip=True) for c in celulas]

        # Se cabeçalho ainda não foi definido, usa a primeira linha
        if not cabecalho:
            cabecalho = valores
            continue

        # Garante que a linha tem o mesmo número de colunas que o cabeçalho
        if len(valores) < len(cabecalho):
            valores += [""] * (len(cabecalho) - len(valores))
        elif len(valores) > len(cabecalho):
            valores = valores[: len(cabecalho)]

        linhas.append(dict(zip(cabecalho, valores)))

    if not linhas:
        raise ValueError(
            "A tabela foi encontrada mas não contém linhas de dados."
        )

    log.info("HTML parseado: %d linhas × %d colunas.", len(linhas), len(cabecalho))
    return linhas


def _extrair_de_json(texto: str) -> list[dict]:
    """
    Faz o parsing de uma resposta JSON.
    Navega pelo caminho CAMINHO_JSON para encontrar a lista de dados.
    Retorna lista de dicionários.
    """
    try:
        dados = json.loads(texto)
    except json.JSONDecodeError as e:
        raise ValueError(f"Resposta não é um JSON válido: {e}") from e

    # Navega pelo caminho configurado (ex: ["data", "rows"])
    for chave in config.CAMINHO_JSON:
        if isinstance(dados, dict) and chave in dados:
            dados = dados[chave]
        else:
            raise KeyError(
                f"Chave '{chave}' não encontrada no JSON. "
                f"Verifique CAMINHO_JSON em config.py. "
                f"Chaves disponíveis: {list(dados.keys()) if isinstance(dados, dict) else 'N/A'}"
            )

    if not isinstance(dados, list):
        raise TypeError(
            f"Esperava uma lista de registros, mas recebeu: {type(dados).__name__}. "
            "Ajuste CAMINHO_JSON em config.py."
        )

    if not dados:
        raise ValueError("O JSON foi encontrado mas a lista de dados está vazia.")

    # Garante que cada item é um dicionário
    if dados and not isinstance(dados[0], dict):
        # Se for lista de listas, tenta converter (primeira linha como cabeçalho)
        if isinstance(dados[0], list):
            cabecalho = [str(i) for i in dados[0]]
            dados = [dict(zip(cabecalho, linha)) for linha in dados[1:]]
        else:
            raise TypeError(
                "Os itens da lista não são objetos. "
                "Estrutura inesperada no JSON."
            )

    log.info("JSON parseado: %d registros.", len(dados))
    return dados


def parsear_resposta(response: requests.Response) -> list[dict]:
    """
    Escolhe automaticamente entre parsing HTML ou JSON
    com base na configuração RESPOSTA_E_JSON.
    """
    if config.RESPOSTA_E_JSON:
        return _extrair_de_json(response.text)
    else:
        return _extrair_de_html(response.text)


# =============================================================================
#  FUNÇÃO PRINCIPAL DE COLETA
# =============================================================================

def coletar() -> list[dict] | None:
    """
    Executa a coleta completa:
      1. Monta headers com tokens
      2. Faz GET na API
      3. Verifica se token expirou
      4. Faz parsing da resposta
      5. Retorna lista de dicionários com os dados

    Retorna None se:
      - O token estiver expirado (usuário precisa atualizar config.py)
      - Houver erro de conexão ou HTTP
      - Não encontrar dados na resposta
    """
    headers = montar_headers()
    proxies = montar_proxies()

    # Avisa se os tokens ainda são os placeholders padrão
    if "COLE_O_TOKEN_AQUI" in config.SESSION_TOKEN:
        log.error(
            "SESSION_TOKEN não foi configurado! "
            "Abra config.py e cole o valor do token."
        )
        return None

    if config.URL_API == "https://COLE_A_URL_AQUI":
        log.error(
            "URL_API não foi configurada! "
            "Abra config.py e cole a URL da API."
        )
        return None

    log.info("Iniciando coleta em: %s", config.URL_API)
    log.debug("Headers enviados: %s", {k: v[:10] + "..." for k, v in headers.items()})

    try:
        response = requests.get(
            config.URL_API,
            headers=headers,
            params=config.PARAMS,
            cookies=config.COOKIES if config.COOKIES else None,
            proxies=proxies,
            timeout=config.TIMEOUT,
            verify=config.VERIFICAR_SSL,
        )

        log.info("Resposta recebida: HTTP %d", response.status_code)

        # ── Verifica expiração ANTES de checar o status ───────────────────
        if token_expirado(response):
            log.error(
                "=" * 60 + "\n"
                "  AÇÃO NECESSÁRIA: Token expirado!\n"
                "  1. Abra o site no navegador e faça login\n"
                "  2. Pressione F12 → Network → clique em qualquer requisição\n"
                "  3. Copie os novos valores dos tokens\n"
                "  4. Cole em config.py e salve\n"
                "  O programa tentará novamente na próxima hora.\n"
                + "=" * 60
            )
            return None

        # ── Verifica outros erros HTTP ────────────────────────────────────
        response.raise_for_status()

        # ── Faz o parsing ─────────────────────────────────────────────────
        dados = parsear_resposta(response)
        log.info("Coleta concluída: %d registros obtidos.", len(dados))
        return dados

    except requests.exceptions.SSLError:
        log.error(
            "Erro de certificado SSL. Se for uma rede interna com "
            "certificado próprio, mude VERIFICAR_SSL = False em config.py."
        )
    except requests.exceptions.ProxyError:
        log.error(
            "Erro de proxy. Verifique as configurações de proxy em config.py "
            "ou mude USAR_PROXY = False."
        )
    except requests.exceptions.ConnectionError:
        log.error(
            "Sem conexão com %s. "
            "Verifique VPN, proxy ou se o sistema está disponível.",
            config.URL_API,
        )
    except requests.exceptions.Timeout:
        log.error(
            "Timeout após %ds. O servidor demorou demais para responder. "
            "Aumente TIMEOUT em config.py se necessário.",
            config.TIMEOUT,
        )
    except requests.exceptions.HTTPError as e:
        log.error("Erro HTTP inesperado: %s", e)
    except (ValueError, IndexError, KeyError, TypeError) as e:
        log.error("Erro ao processar os dados da resposta: %s", e)
    except Exception as e:
        log.exception("Erro inesperado durante a coleta: %s", e)

    return None
