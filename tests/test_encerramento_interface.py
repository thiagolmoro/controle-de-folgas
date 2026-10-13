"""Regressões de callbacks após o fechamento, sem inicializar janela gráfica."""
import ast
from pathlib import Path
from types import SimpleNamespace
import tkinter as tk


class _FakeFont:
    def __init__(self, **kwargs):
        pass


class _FakeTree:
    def __init__(self, exists=True, fail_on_column=False):
        self.exists = exists
        self.fail_on_column = fail_on_column
        self.column_calls = 0

    def winfo_exists(self):
        return self.exists

    def column(self, *args, **kwargs):
        self.column_calls += 1
        if self.fail_on_column:
            raise tk.TclError('invalid command name ".!treeview"')


def _load_method(method_name):
    # Importar o arquivo completo exigiria GUI e dependências do Windows.
    source = (Path(__file__).resolve().parents[1] / 'controle_folgas_v4_1_0.py').read_text(encoding='utf-8')
    module = ast.parse(source)
    app = next(n for n in module.body if isinstance(n, ast.ClassDef) and n.name == 'App')
    func = next(n for n in app.body if isinstance(n, ast.FunctionDef) and n.name == method_name)
    code = compile(ast.fix_missing_locations(ast.Module(body=[func], type_ignores=[])), '<method>', 'exec')
    scope = {'tk': tk, 'tkfont': SimpleNamespace(Font=_FakeFont)}
    exec(code, scope)
    return scope[method_name]


def test_ajuste_nao_acessa_widget_destruido():
    ajustar = _load_method('adjust_entries_columns')
    tree = _FakeTree(exists=False)
    app = SimpleNamespace(tree_entries=tree, body_font=10, _ui_closing=False)
    ajustar(app)
    assert tree.column_calls == 0


def test_ajuste_nao_roda_durante_fechamento():
    ajustar = _load_method('adjust_entries_columns')
    tree = _FakeTree(exists=True)
    app = SimpleNamespace(tree_entries=tree, body_font=10, _ui_closing=True)
    ajustar(app)
    assert tree.column_calls == 0


def test_ajuste_ignora_erro_de_treeview_destruido():
    ajustar = _load_method('adjust_entries_columns')
    tree = _FakeTree(exists=True, fail_on_column=True)
    app = SimpleNamespace(tree_entries=tree, body_font=10, _ui_closing=False)
    ajustar(app)
    assert tree.column_calls == 1


def test_resize_ignora_fechamento():
    ajustar = _load_method('on_window_resize')
    app = SimpleNamespace(_ui_closing=True)
    ajustar(app)
