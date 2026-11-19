"""Etapa 5: envio do relatório ao cuidador por e-mail.

Tema RPA: automação de e-mail.
Idempotente: cada período (semana ISO) gera no máximo uma notificação. Sem SMTP
configurado, o e-mail vai para saida/caixa_de_saida/*.eml (modo de demonstração),
que abre em qualquer cliente de e-mail.
"""
from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from pathlib import Path

from robo.resiliencia import ErroDeSistema, com_retry

log = logging.getLogger("robo.notificacao")


def montar_email(cfg, assunto: str, texto: str, html_corpo: str, anexo: Path) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = cfg.email_remetente
    msg["To"] = cfg.email_cuidador
    msg["Subject"] = assunto
    msg.set_content(texto)
    msg.add_alternative(html_corpo, subtype="html")
    msg.add_attachment(anexo.read_bytes(), maintype="application",
                       subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=anexo.name)
    return msg


def enviar_smtp(cfg, msg: EmailMessage) -> None:
    @com_retry(tentativas=3, espera_inicial=2.0)
    def _enviar():
        try:
            with smtplib.SMTP(cfg.smtp_host, cfg.smtp_porta, timeout=20) as smtp:
                smtp.starttls()
                if cfg.smtp_usuario:
                    smtp.login(cfg.smtp_usuario, cfg.smtp_senha or "")
                smtp.send_message(msg)
        except (OSError, smtplib.SMTPException) as erro:
            raise ErroDeSistema(f"falha no SMTP: {erro}") from erro

    _enviar()


def executar(cfg, estado, detalhes: dict, chave_periodo: str, assunto: str, texto: str,
             html_corpo: str, anexo: Path, forcar: bool = False) -> None:
    chave = f"relatorio:{chave_periodo}:{cfg.email_cuidador}"
    if estado.ja_notificado(chave) and not forcar:
        log.info("Relatório de %s já foi enviado antes. Nada a fazer (idempotência).", chave_periodo)
        detalhes.update(enviado=False, motivo="já enviado neste período")
        return

    msg = montar_email(cfg, assunto, texto, html_corpo, anexo)
    caixa = cfg.dir_saida / "caixa_de_saida"
    caixa.mkdir(exist_ok=True)
    arquivo_eml = caixa / f"{chave_periodo}.eml"

    if cfg.smtp_host:
        try:
            enviar_smtp(cfg, msg)
            detalhes.update(enviado=True, canal="smtp")
        except ErroDeSistema as erro:
            # Caminho seguro: guarda o e-mail para reenvio manual em vez de perder a notificação
            arquivo_eml.write_bytes(bytes(msg))
            detalhes.update(enviado=False, canal="pendente", arquivo=arquivo_eml.name, avisos=True)
            log.error("%s. E-mail salvo em %s para reenvio.", erro, arquivo_eml.name)
            return
    else:
        arquivo_eml.write_bytes(bytes(msg))
        detalhes.update(enviado=True, canal="arquivo .eml (modo demonstração)", arquivo=arquivo_eml.name)
        log.info("SMTP não configurado: e-mail salvo em %s", arquivo_eml.name)

    estado.registrar_notificacao(chave)
