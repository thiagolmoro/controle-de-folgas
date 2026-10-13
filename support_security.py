"""Autorização de suporte offline por desafio/resposta Ed25519.

Somente a chave pública é distribuída junto ao aplicativo. A chave privada
é criada e mantida fora do projeto com a ferramenta ferramentas/suporte_cli.py.
Não confundir este mecanismo com autenticação de usuários do sistema operacional:
quem pode substituir o executável ou editar livremente o banco controla os dados.
"""
from __future__ import annotations

import base64
import json
import secrets
import time
from typing import Any

try:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
except ImportError:  # erro explícito ao tentar autorizar, sem liberar acesso
    Ed25519PublicKey = None
    InvalidSignature = Exception

from support_public_key import SUPPORT_PUBLIC_KEY_B64

PREFIX = "CF41-"
DOMAIN = b"controle-folgas/support-auth/v1:"
TTL_SECONDS = 30 * 60
PENDING_KEY = "support_pending_request_v1"
INSTANCE_KEY = "support_installation_id_v1"
ALLOWED_ACTIONS = {"ADMIN_RESET", "TRASH_EMPTY"}


class SupportAuthorizationError(ValueError):
    pass


def b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def b64decode(value: str) -> bytes:
    text = value.strip()
    if not text or len(text) > 4096:
        raise SupportAuthorizationError("Código inválido ou muito longo.")
    try:
        return base64.b64decode(text + "=" * (-len(text) % 4), altchars=b"-_", validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise SupportAuthorizationError("Código com formato inválido.") from exc


def public_key():
    if Ed25519PublicKey is None:
        raise SupportAuthorizationError("Biblioteca cryptography ausente. Instale as dependências.")
    if not SUPPORT_PUBLIC_KEY_B64:
        raise SupportAuthorizationError(
            "Chave pública de suporte não configurada. Gere as chaves antes de compilar a versão 4.1.0."
        )
    try:
        return Ed25519PublicKey.from_public_bytes(b64decode(SUPPORT_PUBLIC_KEY_B64))
    except (ValueError, TypeError) as exc:
        raise SupportAuthorizationError("Chave pública de suporte inválida.") from exc


def validate_action(action: str) -> None:
    if action in ALLOWED_ACTIONS:
        return
    if action.startswith("TRASH_DELETE:") and action.split(":", 1)[1].isdigit():
        return
    raise SupportAuthorizationError("Operação de suporte desconhecida.")


def parse_request(request: str, *, now: int | None = None) -> dict[str, Any]:
    try:
        value = json.loads(b64decode(request))
        if not isinstance(value, dict) or value.get("v") != 1:
            raise ValueError("versão")
        action = value["action"]
        validate_action(action)
        if (not isinstance(value.get("installation"), str) or
                len(value["installation"]) != 32 or
                not isinstance(value.get("nonce"), str) or len(value["nonce"]) != 32):
            raise ValueError("identificação")
        if not isinstance(value.get("issued"), int):
            raise ValueError("timestamp")
        current = int(time.time() if now is None else now)
        if value["issued"] > current + 60 or current - value["issued"] > TTL_SECONDS:
            raise SupportAuthorizationError("Solicitação de suporte expirada. Gere outra solicitação.")
        return value
    except SupportAuthorizationError:
        raise
    except (KeyError, TypeError, ValueError, UnicodeDecodeError) as exc:
        raise SupportAuthorizationError("Solicitação de suporte inválida.") from exc


def issue_request(db, action: str, *, now: int | None = None) -> str:
    public_key()  # Falha fechada se não houver chave válida no executável.
    validate_action(action)
    installation = db.get_config(INSTANCE_KEY, "")
    if not installation or len(str(installation)) != 32:
        installation = secrets.token_hex(16)
        db.set_config(INSTANCE_KEY, installation)
    payload = {
        "v": 1,
        "installation": installation,
        "action": action,
        "nonce": secrets.token_hex(16),
        "issued": int(time.time() if now is None else now),
    }
    encoded = b64encode(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    db.set_config(PENDING_KEY, encoded)  # Nova solicitação invalida a anterior.
    return encoded


def verify_and_consume(db, action: str, response: str, *, now: int | None = None) -> None:
    """Valida assinatura vinculada a instalação/ação/desafio e consome uso único."""
    validate_action(action)
    pending = db.get_config(PENDING_KEY, "")
    if not pending:
        raise SupportAuthorizationError("Não existe solicitação de suporte pendente.")
    request = parse_request(pending, now=now)
    if request["action"] != action or request["installation"] != db.get_config(INSTANCE_KEY, ""):
        raise SupportAuthorizationError("Autorização não corresponde à operação ou instalação.")
    clean = "".join(str(response or "").split())
    if not clean.startswith(PREFIX):
        raise SupportAuthorizationError("A resposta deve começar com CF41-.")
    signature = b64decode(clean[len(PREFIX):])
    try:
        public_key().verify(signature, DOMAIN + pending.encode("ascii"))
    except InvalidSignature as exc:
        raise SupportAuthorizationError("Resposta de suporte inválida ou destinada a outra solicitação.") from exc
    db.delete_config(PENDING_KEY)


def sign_request(private_key, request: str, *, now: int | None = None) -> str:
    """Apenas a ferramenta offline usa esta função; nunca embutir chave privada no app."""
    parse_request(request, now=now)
    return PREFIX + b64encode(private_key.sign(DOMAIN + request.encode("ascii")))
