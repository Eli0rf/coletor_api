# =============================================================================
#  excel.py — MÓDULO DE EXPORTAÇÃO PARA EXCEL
#  Responsável por:
#    - Criar ou abrir a planilha configurada
#    - Escrever os dados coletados
#    - Aplicar formatação visual (cabeçalho, zebra, larguras)
#    - Suportar dois modos: sobrescrever ou acumular com timestamp
# =============================================================================

import logging
from datetime import datetime
from pathlib import Path

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

import config

log = logging.getLogger(__name__)


# =============================================================================
#  ESTILOS VISUAIS
# =============================================================================

# Cores principais
COR_CABECALHO     = "1F4E79"   # azul escuro
COR_LINHA_PAR     = "D6E4F0"   # azul claro (linhas pares)
COR_LINHA_IMPAR   = "FFFFFF"   # branco (linhas ímpares)
COR_TOTAL         = "1F4E79"   # azul escuro (linha de totalizador)
COR_AVISO         = "FFF2CC"   # amarelo claro (linha de aviso)
COR_FONTE_CABEC   = "FFFFFF"   # branco
COR_FONTE_TOTAL   = "FFFFFF"   # branco


def _estilo_cabecalho(ws, num_colunas: int):
    """Aplica formatação ao cabeçalho (primeira linha)."""
    fill  = PatternFill("solid", fgColor=COR_CABECALHO)
    fonte = Font(bold=True, color=COR_FONTE_CABEC, size=11, name="Calibri")
    borda = Border(bottom=Side(style="medium", color="AAAAAA"))
    alinhamento = Alignment(horizontal="center", vertical="center", wrap_text=True)

    for col in range(1, num_colunas + 1):
        cell = ws.cell(1, col)
        cell.fill      = fill
        cell.font      = fonte
        cell.border    = borda
        cell.alignment = alinhamento

    ws.row_dimensions[1].height = 28


def _estilo_linha_dados(ws, linha: int, zebra: bool):
    """Aplica formatação zebra nas linhas de dados."""
    cor  = COR_LINHA_PAR if zebra else COR_LINHA_IMPAR
    fill = PatternFill("solid", fgColor=cor)
    alinhamento = Alignment(horizontal="center", vertical="center", wrap_text=False)

    for cell in ws[linha]:
        cell.fill      = fill
        cell.alignment = alinhamento


def _ajustar_largura_colunas(ws):
    """Ajusta automaticamente a largura de cada coluna pelo conteúdo."""
    for col in ws.columns:
        max_len = max(
            (len(str(cell.value or "")) for cell in col),
            default=8
        )
        # Limita entre 12 e 50 caracteres
        largura = min(max(max_len + 4, 12), 50)
        ws.column_dimensions[get_column_letter(col[0].column)].width = largura


# =============================================================================
#  FUNÇÃO PRINCIPAL DE SALVAMENTO
# =============================================================================

def salvar(dados: list[dict], timestamp: datetime | None = None) -> bool:
    """
    Salva os dados na planilha Excel conforme as configurações.

    Parâmetros:
        dados      — lista de dicionários retornada pelo coletor
        timestamp  — horário da coleta (usa datetime.now() se None)

    Retorna:
        True  se salvou com sucesso
        False se ocorreu algum erro
    """
    if not dados:
        log.warning("Nenhum dado para salvar no Excel.")
        return False

    if timestamp is None:
        timestamp = datetime.now()

    caminho = Path(config.ARQUIVO_EXCEL)
    colunas_dados = list(dados[0].keys())

    # Monta o cabeçalho completo (com ou sem coluna de timestamp)
    if config.ADICIONAR_COLUNA_TIMESTAMP:
        cabecalho = ["Coletado em"] + colunas_dados
    else:
        cabecalho = colunas_dados

    try:
        # ── Abre ou cria o arquivo Excel ──────────────────────────────────
        try:
            wb = openpyxl.load_workbook(caminho)
        except FileNotFoundError:
            log.info("Criando novo arquivo Excel: %s", caminho)
            wb = openpyxl.Workbook()
            # Remove a aba padrão criada pelo openpyxl
            if "Sheet" in wb.sheetnames:
                del wb["Sheet"]

        # ── Gerencia a aba de destino ─────────────────────────────────────
        if config.MODO_SOBRESCREVER:
            # Remove a aba existente e recria do zero
            if config.NOME_ABA in wb.sheetnames:
                del wb[config.NOME_ABA]
            ws = wb.create_sheet(config.NOME_ABA, 0)

            # Escreve cabeçalho
            ws.append(cabecalho)

            # Escreve todas as linhas de dados
            for i, registro in enumerate(dados, start=1):
                linha = []
                if config.ADICIONAR_COLUNA_TIMESTAMP:
                    linha.append(timestamp.strftime("%d/%m/%Y %H:%M:%S"))
                linha += [registro.get(col, "") for col in colunas_dados]
                ws.append(linha)
                _estilo_linha_dados(ws, i + 1, i % 2 == 0)

        else:
            # Modo acumulativo: adiciona ao final da aba existente
            if config.NOME_ABA not in wb.sheetnames:
                ws = wb.create_sheet(config.NOME_ABA, 0)
                ws.append(cabecalho)  # cabeçalho só na primeira vez
            else:
                ws = wb[config.NOME_ABA]

            linha_inicio = ws.max_row  # linha onde os dados novos começarão
            ts_str = timestamp.strftime("%d/%m/%Y %H:%M:%S")

            for i, registro in enumerate(dados, start=1):
                linha = []
                if config.ADICIONAR_COLUNA_TIMESTAMP:
                    linha.append(ts_str)
                linha += [registro.get(col, "") for col in colunas_dados]
                ws.append(linha)
                # Continua o padrão zebra do final atual
                num_linha_ws = linha_inicio + i
                _estilo_linha_dados(ws, num_linha_ws, num_linha_ws % 2 == 0)

        # ── Estiliza cabeçalho e ajusta colunas ───────────────────────────
        _estilo_cabecalho(ws, len(cabecalho))
        _ajustar_largura_colunas(ws)

        # ── Congela o cabeçalho (scroll sem perder o cabeçalho) ───────────
        ws.freeze_panes = "A2"

        # ── Metadados do arquivo ──────────────────────────────────────────
        wb.properties.title      = "Relatório Automático"
        wb.properties.lastModifiedBy = "coletor_api"

        # ── Salva o arquivo ───────────────────────────────────────────────
        wb.save(caminho)
        log.info(
            "Excel salvo: %s | %d registros | Aba: '%s'",
            caminho.resolve(), len(dados), config.NOME_ABA
        )
        return True

    except PermissionError:
        log.error(
            "Sem permissão para salvar '%s'. "
            "O arquivo está aberto no Excel? Feche e tente novamente.",
            caminho
        )
    except Exception as e:
        log.exception("Erro inesperado ao salvar Excel: %s", e)

    return False


def registrar_erro_no_excel(mensagem: str):
    """
    Registra uma linha de aviso/erro diretamente na planilha,
    útil para rastrear quando o token expirou ou houve falha.
    """
    caminho = Path(config.ARQUIVO_EXCEL)

    try:
        try:
            wb = openpyxl.load_workbook(caminho)
        except FileNotFoundError:
            wb = openpyxl.Workbook()
            if "Sheet" in wb.sheetnames:
                del wb["Sheet"]

        if config.NOME_ABA not in wb.sheetnames:
            ws = wb.create_sheet(config.NOME_ABA, 0)
        else:
            ws = wb[config.NOME_ABA]

        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        # Linha de aviso com fundo amarelo
        ws.append([agora, f"⚠️ {mensagem}"])
        linha = ws.max_row
        fill_aviso = PatternFill("solid", fgColor=COR_AVISO)
        fonte_aviso = Font(bold=True, color="7B6000")
        for cell in ws[linha]:
            cell.fill = fill_aviso
            cell.font = fonte_aviso

        wb.save(caminho)
        log.info("Aviso registrado no Excel: %s", mensagem)

    except Exception as e:
        log.warning("Não foi possível registrar aviso no Excel: %s", e)
