"""Utilitário OFFLINE. Nunca inclua o arquivo de chave privada em repositórios.

Python 3.10+ com `cryptography` instalado.
"""
from __future__ import annotations

import argparse
import base64
import getpass
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from support_security import parse_request, sign_request


def create_keys(folder: Path):
    """Cria chave privada cifrada fora do projeto e salva somente a pública no app."""
    folder = folder.expanduser().resolve()
    if folder == ROOT or ROOT in folder.parents:
        raise ValueError("A pasta das chaves PRIVADAS deve estar fora do projeto GitHub.")
    target = folder / "controle_folgas_suporte_PRIVADA.pem"
    public_module = ROOT / "support_public_key.py"
    if target.exists():
        raise FileExistsError(f"A chave privada já existe: {target}. Não foi substituída.")
    if 'SUPPORT_PUBLIC_KEY_B64 = ""' not in public_module.read_text(encoding="utf-8"):
        raise RuntimeError("O projeto já tem chave pública configurada; para rotacionar é necessário um plano de migração.")
    password = getpass.getpass("Crie uma senha forte para proteger a chave PRIVADA: ")
    confirmation = getpass.getpass("Confirme a senha: ")
    if password != confirmation or len(password) < 12:
        raise ValueError("Senhas diferentes ou menores que 12 caracteres. Nada foi alterado.")
    key = Ed25519PrivateKey.generate()
    encrypted = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(password.encode("utf-8")),
    )
    folder.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as output:
        output.write(encrypted)
    public_raw = key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    pub = base64.urlsafe_b64encode(public_raw).rstrip(b"=").decode("ascii")
    public_module.write_text(
        '"""Chave PÚBLICA Ed25519 da instalação. Não inclua a chave privada aqui."""\n'
        f'SUPPORT_PUBLIC_KEY_B64 = "{pub}"\n', encoding="utf-8"
    )
    print(f"Chave privada cifrada (NÃO publicar): {target}")
    print(f"Chave pública configurada em: {public_module}")
    print("Guarde também a senha da chave em local seguro. Sem a chave privada, não é possível autorizar o suporte.")


def approve_request(private_file: Path):
    path = private_file.expanduser().resolve()
    request = input("Cole a SOLICITAÇÃO copiada do aplicativo: ").strip()
    data = parse_request(request)
    print("\nATENÇÃO: confira se esta solicitação é do equipamento e da operação esperados.")
    print(f"Instalação: {data['installation']}")
    print(f"Operação: {data['action']}")
    confirmation = input("Autorizar esta operação? Digite AUTORIZAR: ").strip()
    if confirmation != "AUTORIZAR":
        print("Operação cancelada.")
        return
    password = getpass.getpass("Senha da chave privada: ")
    key = serialization.load_pem_private_key(path.read_bytes(), password=password.encode("utf-8"))
    if not isinstance(key, Ed25519PrivateKey):
        raise TypeError("O arquivo de chave não contém uma chave Ed25519.")
    print("\nRESPOSTA PARA DIGITAR NO PROGRAMA:")
    print(sign_request(key, request))
    print("\nA resposta vale apenas para esta solicitação, durante 30 minutos, uma única vez.")


def main():
    parser = argparse.ArgumentParser(description="Ferramenta offline de suporte — Controle de Folgas 4.1")
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("criar-chaves", help="cria chave privada cifrada e configura a pública no projeto")
    create.add_argument("--destino", type=Path, required=True, help="pasta FORA do projeto para guardar a chave")
    sign = sub.add_parser("assinar", help="autoriza uma solicitação de suporte após conferência")
    sign.add_argument("--chave", type=Path, required=True, help="caminho da chave privada cifrada")
    args = parser.parse_args()
    try:
        if args.command == "criar-chaves":
            create_keys(args.destino)
        else:
            approve_request(args.chave)
    except (OSError, ValueError, TypeError, RuntimeError) as exc:
        parser.exit(1, f"ERRO: {exc}\n")


if __name__ == "__main__":
    main()
