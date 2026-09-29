#!/usr/bin/env python3
# =============================================================================
#  main.py — PONTO DE ENTRADA DO PROGRAMA
#
#  COMO USAR:
#    1. Configure config.py com sua URL e tokens
#    2. Execute: python main.py
#    3. O programa coleta agora e repete a cada INTERVALO_MINUTOS
#    4. Pressione Ctrl+C para parar
#
#  ARGUMENTOS OPCIONAIS:
#    python main.py --uma-vez       → coleta uma vez e sai
#    python main.py --agora         → força coleta imediata além do ciclo normal
#    python main.py --intervalo 30  → sobrescreve o intervalo (em minutos)
# =============================================================================

import sys
import time
import argparse
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path

import config
import coletor
import excel


# =============================================================================
#  CONFIGURAÇÃO DO SISTEMA DE LOG
#  Escreve simultaneamente no terminal e no arquivo coletor.log
# =============================================================================

def configurar_log():
    fmt = logging.Formatter(
        fmt="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%d/%m/%Y %H:%M:%S"
    )

    # Handler do terminal
    handler_console = logging.StreamHandler(sys.stdout)
    handler_console.setFormatter(fmt)

    # Handler do arquivo de log (mantém histórico)
    handler_arquivo = logging.FileHandler(config.ARQUIVO_LOG, encoding="utf-8")
    handler_arquivo.setFormatter(fmt)

    logging.basicConfig(
        level=logging.INFO,
        handlers=[handler_console, handler_arquivo]
    )

configurar_log()
log = logging.getLogger(__name__)


# =============================================================================
#  CICLO DE COLETA
# =============================================================================

# Contador global para estatísticas
_stats = {
    "total_coletas":    0,
    "coletas_ok":       0,
    "coletas_erro":     0,
    "ultimo_sucesso":   None,
    "token_expirado":   False,
}


def executar_coleta() -> bool:
    """
    Executa um ciclo completo: coleta → salva no Excel.
    Atualiza as estatísticas globais.
    Retorna True se bem-sucedido.
    """
    agora = datetime.now()
    _stats["total_coletas"] += 1

    log.info("─" * 55)
    log.info("Iniciando coleta #%d — %s", _stats["total_coletas"], agora.strftime("%d/%m/%Y %H:%M:%S"))

    # ── Etapa 1: Coleta os dados ──────────────────────────────────────────
    dados = coletor.coletar()

    if dados is None:
        _stats["coletas_erro"] += 1

        # Verifica se foi por token expirado para dar aviso mais claro
        _stats["token_expirado"] = True
        excel.registrar_erro_no_excel(
            "Falha na coleta — token expirado ou erro de conexão. "
            "Atualize config.py com novos tokens."
        )

        log.error(
            "Coleta #%d FALHOU. Total de falhas: %d.",
            _stats["total_coletas"], _stats["coletas_erro"]
        )
        return False

    _stats["token_expirado"] = False

    # ── Etapa 2: Salva no Excel ───────────────────────────────────────────
    sucesso = excel.salvar(dados, timestamp=agora)

    if sucesso:
        _stats["coletas_ok"]     += 1
        _stats["ultimo_sucesso"]  = agora
        log.info(
            "✅ Coleta #%d concluída com sucesso. "
            "%d registros salvos em '%s'.",
            _stats["total_coletas"], len(dados), config.ARQUIVO_EXCEL
        )
    else:
        _stats["coletas_erro"] += 1
        log.error(
            "Coleta #%d: dados obtidos mas ERRO ao salvar no Excel.",
            _stats["total_coletas"]
        )

    return sucesso


def imprimir_status():
    """Imprime um resumo do status atual do programa."""
    proximo = _stats.get("proximo_ciclo")
    proximo_str = proximo.strftime("%H:%M:%S") if proximo else "—"

    log.info("=" * 55)
    log.info("  STATUS DO COLETOR")
    log.info("  Coletas realizadas : %d", _stats["total_coletas"])
    log.info("  Sucessos           : %d", _stats["coletas_ok"])
    log.info("  Falhas             : %d", _stats["coletas_erro"])
    if _stats["ultimo_sucesso"]:
        log.info(
            "  Último sucesso     : %s",
            _stats["ultimo_sucesso"].strftime("%d/%m/%Y %H:%M:%S")
        )
    log.info("  Próxima coleta     : %s", proximo_str)
    if _stats["token_expirado"]:
        log.warning("  ⚠️  TOKEN EXPIRADO — atualize config.py!")
    log.info("=" * 55)


# =============================================================================
#  LOOP PRINCIPAL
# =============================================================================

def loop_principal(intervalo_minutos: int):
    """
    Roda indefinidamente, executando uma coleta a cada intervalo.
    Para com Ctrl+C.
    """
    intervalo_seg = intervalo_minutos * 60

    log.info("=" * 55)
    log.info("  COLETOR API → EXCEL")
    log.info("  URL      : %s", config.URL_API)
    log.info("  Saída    : %s", Path(config.ARQUIVO_EXCEL).resolve())
    log.info("  Intervalo: %d minutos", intervalo_minutos)
    log.info("  Modo     : %s", "Sobrescrever" if config.MODO_SOBRESCREVER else "Acumulativo")
    log.info("  Pressione Ctrl+C para parar")
    log.info("=" * 55)

    # Coleta imediata ao iniciar (se configurado)
    if config.COLETAR_AO_INICIAR:
        executar_coleta()

    try:
        while True:
            # Calcula e registra o horário da próxima coleta
            proximo = datetime.now() + timedelta(seconds=intervalo_seg)
            _stats["proximo_ciclo"] = proximo

            log.info(
                "Aguardando %d minutos. Próxima coleta às %s.",
                intervalo_minutos, proximo.strftime("%H:%M:%S")
            )

            # Dorme em blocos de 1 segundo para responder ao Ctrl+C rapidamente
            for _ in range(intervalo_seg):
                time.sleep(1)

            executar_coleta()
            imprimir_status()

    except KeyboardInterrupt:
        log.info("Programa encerrado pelo usuário (Ctrl+C).")
        imprimir_status()
        sys.exit(0)


# =============================================================================
#  ARGUMENTOS DE LINHA DE COMANDO
# =============================================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="Coleta dados de API e salva em Excel de hora em hora.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python main.py                   → inicia o loop horário
  python main.py --uma-vez         → coleta uma vez e sai
  python main.py --intervalo 30    → coleta a cada 30 minutos
        """
    )
    parser.add_argument(
        "--uma-vez",
        action="store_true",
        help="Executa uma única coleta e encerra o programa."
    )
    parser.add_argument(
        "--intervalo",
        type=int,
        default=None,
        help="Intervalo entre coletas em minutos (padrão: valor em config.py)."
    )
    return parser.parse_args()


# =============================================================================
#  VERIFICAÇÃO DE CONFIGURAÇÃO
# =============================================================================

def verificar_config() -> bool:
    """
    Verifica se as configurações mínimas foram preenchidas.
    Retorna False e loga os problemas encontrados.
    """
    ok = True

    if config.URL_API == "https://COLE_A_URL_AQUI":
        log.error(
            "❌ URL_API não configurada! "
            "Abra config.py e preencha o campo URL_API."
        )
        ok = False

    if config.SESSION_TOKEN == "COLE_O_TOKEN_AQUI":
        log.error(
            "❌ SESSION_TOKEN não configurado! "
            "Abra config.py e cole o valor do token de sessão."
        )
        ok = False

    if config.XSRF_TOKEN == "COLE_O_TOKEN_AQUI":
        log.warning(
            "⚠️  XSRF_TOKEN não configurado. "
            "Se o sistema exigir, cole o valor em config.py."
        )
        # Não bloqueia — pode ser que o sistema não use XSRF

    if config.USAR_TOKEN_EXTRA and "COLE_O_TOKEN_AQUI" in config.TOKEN_EXTRA:
        log.warning(
            "⚠️  TOKEN_EXTRA está marcado como ativo mas não foi configurado. "
            "Cole o valor em config.py ou mude USAR_TOKEN_EXTRA = False."
        )

    return ok


# =============================================================================
#  PONTO DE ENTRADA
# =============================================================================

if __name__ == "__main__":
    args = parse_args()

    # Determina o intervalo a usar
    intervalo = args.intervalo if args.intervalo else config.INTERVALO_MINUTOS

    # Verifica configuração mínima
    if not verificar_config():
        log.error(
            "Configure o arquivo config.py antes de executar. "
            "Encerrando."
        )
        sys.exit(1)

    if args.uma_vez:
        # ── Modo: coleta única ────────────────────────────────────────────
        log.info("Modo: coleta única.")
        sucesso = executar_coleta()
        sys.exit(0 if sucesso else 1)

    else:
        # ── Modo: loop contínuo ───────────────────────────────────────────
        loop_principal(intervalo)
