"""Testes independentes do Windows / GUI. Execução: python -m pytest -q."""
from __future__ import annotations

import base64
import sqlite3
import time

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

import support_security as sec


class FakeDB:
    def __init__(self):
        self.data = {}

    def get_config(self, key, default=""):
        return self.data.get(key, default)

    def set_config(self, key, value):
        self.data[key] = value

    def delete_config(self, key):
        self.data.pop(key, None)


@pytest.fixture
def signed(monkeypatch):
    private = Ed25519PrivateKey.generate()
    pub = private.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    monkeypatch.setattr(sec, 'SUPPORT_PUBLIC_KEY_B64', sec.b64encode(pub))
    return private


def test_support_token_per_installation_and_one_time(signed):
    db = FakeDB()
    token = sec.issue_request(db, "ADMIN_RESET")
    response = sec.sign_request(signed, token)
    sec.verify_and_consume(db, "ADMIN_RESET", response)
    with pytest.raises(sec.SupportAuthorizationError, match="Não existe"):
        sec.verify_and_consume(db, "ADMIN_RESET", response)


def test_reject_wrong_scope(signed):
    db = FakeDB()
    token = sec.issue_request(db, "TRASH_DELETE:22")
    response = sec.sign_request(signed, token)
    with pytest.raises(sec.SupportAuthorizationError, match="operação"):
        sec.verify_and_consume(db, "TRASH_DELETE:21", response)


def test_reject_response_for_another_challenge(signed):
    db = FakeDB()
    first = sec.issue_request(db, "TRASH_EMPTY")
    response = sec.sign_request(signed, first)
    sec.issue_request(db, "TRASH_EMPTY")
    with pytest.raises(sec.SupportAuthorizationError, match="inválida"):
        sec.verify_and_consume(db, "TRASH_EMPTY", response)


def test_expired_rejected(signed):
    db = FakeDB()
    past = int(time.time()) - sec.TTL_SECONDS - 1
    token = sec.issue_request(db, "ADMIN_RESET", now=past)
    with pytest.raises(sec.SupportAuthorizationError, match="expirada"):
        sec.verify_and_consume(db, "ADMIN_RESET", "CF41-aaaa")
    with pytest.raises(sec.SupportAuthorizationError, match="expirada"):
        sec.sign_request(signed, token)


def test_wrong_key_and_modified_request(signed):
    other = Ed25519PrivateKey.generate()
    db = FakeDB()
    token = sec.issue_request(db, "TRASH_EMPTY")
    with pytest.raises(sec.SupportAuthorizationError, match="inválida"):
        sec.verify_and_consume(db, "TRASH_EMPTY", sec.sign_request(other, token))
    with pytest.raises(sec.SupportAuthorizationError):
        sec.issue_request(db, "UNKNOWN")


def test_support_unconfigured_blocks(monkeypatch):
    monkeypatch.setattr(sec, 'SUPPORT_PUBLIC_KEY_B64', '')
    with pytest.raises(sec.SupportAuthorizationError, match="não configurada"):
        sec.issue_request(FakeDB(), "ADMIN_RESET")


def test_request_installation_binding(signed):
    db1, db2 = FakeDB(), FakeDB()
    request = sec.issue_request(db1, 'ADMIN_RESET')
    db2.set_config(sec.PENDING_KEY, request)
    db2.set_config(sec.INSTANCE_KEY, '0'*32)
    with pytest.raises(sec.SupportAuthorizationError, match='instalação'):
        sec.verify_and_consume(db2, 'ADMIN_RESET', sec.sign_request(signed, request))
