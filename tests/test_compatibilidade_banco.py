"""Testa migração da estrutura 4.0.2 usando apenas registros sintéticos.

A fixture reproduz as tabelas relevantes da versão 4.0.2 sem depender de um
banco de funcionários ou de qualquer arquivo .db versionado no repositório.
O teste completo com uma cópia da instalação antiga permanece manual.
"""
from __future__ import annotations

import importlib.util
import sqlite3
import sys
import types
from pathlib import Path


def _load_desktop_module():
    # Teste do banco sem criar janelas de Tk no ambiente de integração contínua.
    if "customtkinter" not in sys.modules:
        stub = types.ModuleType("customtkinter")
        stub.CTkFrame = type("CTkFrame", (object,), {})
        stub.CTk = type("CTk", (object,), {})
        sys.modules["customtkinter"] = stub
    entry = Path(__file__).resolve().parents[1] / "controle_folgas_v4_1_0.py"
    spec = importlib.util.spec_from_file_location("controle_folgas_v4_1_0_test_mod", entry)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SCHEMA_402 = """
CREATE TABLE config (chave TEXT PRIMARY KEY, valor TEXT NOT NULL);
CREATE TABLE funcionarios (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nome TEXT NOT NULL UNIQUE,
  ativo INTEGER NOT NULL DEFAULT 1,
  criado_em TEXT NOT NULL,
  jornada_horas INTEGER NOT NULL DEFAULT 12,
  regime TEXT NOT NULL DEFAULT '12x36'
);
CREATE TABLE lancamentos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  funcionario_id INTEGER NOT NULL,
  data TEXT NOT NULL,
  movimento TEXT NOT NULL,
  categoria TEXT NOT NULL,
  quantidade_texto TEXT,
  minutos INTEGER NOT NULL,
  observacao TEXT,
  origem TEXT DEFAULT 'Manual',
  criado_em TEXT NOT NULL,
  excluido INTEGER NOT NULL DEFAULT 0,
  excluido_em TEXT,
  motivo_exclusao TEXT,
  FOREIGN KEY(funcionario_id) REFERENCES funcionarios(id)
);
CREATE TABLE auditoria (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  acao TEXT NOT NULL,
  lancamento_id INTEGER,
  detalhes TEXT,
  criado_em TEXT NOT NULL
);
"""


def _create_synthetic_v402_db(path: Path):
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA_402)
        conn.executemany("INSERT INTO config (chave,valor) VALUES (?,?)", [
            ("nome_servico", "Demonstração - Dados Fictícios"),
            ("horas_por_dia", "8"),
            ("admin_password_hash", "HASH_TESTE_NAO_E_CREDENCIAL"),
            ("admin_recovery_hash", "HASH_RECUPERACAO_FICTICIO"),
        ])
        conn.execute(
            "INSERT INTO funcionarios (id,nome,ativo,criado_em,jornada_horas,regime) "
            "VALUES (1, 'Funcionario Ficticio', 1, '2026-01-01 10:00:00', 8, 'Outro')"
        )
        conn.executemany(
            """INSERT INTO lancamentos
            (id,funcionario_id,data,movimento,categoria,quantidade_texto,
             minutos,observacao,origem,criado_em,excluido,excluido_em,motivo_exclusao)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            [
                (1, 1, "2026-01-02", "Crédito", "Banco de horas", "2 horas", 120,
                 "Apenas teste", "Manual", "2026-01-02 10:00:00", 0, None, None),
                (2, 1, "2026-01-03", "Débito", "Folga", "1 hora", -60,
                 "Somente demonstração", "Manual", "2026-01-03 10:00:00", 1,
                 "2026-01-04 10:00:00", "Registro descartado no teste"),
            ],
        )
        conn.execute(
            "INSERT INTO auditoria (id, acao, lancamento_id, detalhes, criado_em) "
            "VALUES (1, 'LANCAMENTO ALTERADO', 1, 'Registro de teste', '2026-01-02 11:00:00')"
        )


def _snapshot(path: Path):
    with sqlite3.connect(path) as conn:
        return {
            table: conn.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
            for table in ("funcionarios", "lancamentos", "auditoria", "config")
        }


def test_preserva_estrutura_v402_com_dados_sinteticos(tmp_path, monkeypatch):
    db_file = tmp_path / "controle_folgas.db"
    _create_synthetic_v402_db(db_file)
    before = _snapshot(db_file)
    module = _load_desktop_module()
    monkeypatch.setattr(module, "app_dir", lambda: tmp_path)

    instance = module.Database()
    try:
        assert instance.conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert instance.get_config("nome_servico") == "Demonstração - Dados Fictícios"
    finally:
        instance.conn.close()

    after = _snapshot(db_file)
    for table in before:
        assert after[table] == before[table], f"Dados existentes alterados em {table}"
