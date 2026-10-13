# Guia de desenvolvimento e compilação — Windows

Esta documentação é para trabalhar a partir do **código-fonte** do Controle de Folgas 4.1.0. A versão estável já está publicada no [repositório oficial de Releases](https://github.com/thiagolmoro/controle-de-folgas-releases/releases/tag/v4.1.0).

## 1. Ambiente isolado

Abra a pasta do projeto no VS Code e execute no PowerShell:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install pytest
.\.venv\Scripts\python.exe -m pytest -q
```

É possível usar o Python da `.venv` diretamente sem ativar o ambiente virtual.

## 2. Testar a interface

```powershell
.\.venv\Scripts\python.exe .\controle_folgas_v4_1_0.py
```

Se não houver banco de dados ao lado do script, será criado um `controle_folgas.db` vazio. Para testes que modificam registros, use **somente dados de demonstração**. Nunca substitua o banco de uma instalação operacional.

## 3. Gerar o executável

```powershell
.\.venv\Scripts\python.exe .\criar_splash_controle_folgas.py
.\.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm .\Controle_de_Folgas_v4_1_0.spec
```

O resultado esperado é `dist\Controle de Folgas.exe`.

**Atenção à chave de suporte:** `support_public_key.py` já contém a chave **pública** correspondente ao executável oficial 4.1.0. Ela pode ser distribuída. A chave privada correspondente não está no repositório e não pode ser reconstruída a partir da pública. Não gere ou substitua chaves para novas Releases oficiais sem coordenar o processo de rotação. Para fazer uma variante independente, consulte o documento de [segurança](SEGURANCA.md).

## 4. Testes recomendados antes de uma futura Release

- Executar os testes automatizados e abrir/fechar a GUI sem erros no terminal.
- Testar o backup e a restauração **numa cópia** de um banco anterior.
- Revisar cálculo de créditos/débitos, filtros e relatório Excel.
- Testar Lixeira, auditoria e recuperação administrativa com registros sintéticos.
- Confirmar splash, ícone, instância única e encerramento do EXE.
- Simular a atualização em repositório isolado, preservando uma cópia do banco.
- Confirmar que o atualizador consulta o repositório correto e que a nova Release contém o EXE adequado.

## 5. Publicação de código

Antes de enviar arquivos a um repositório público:

```powershell
git status --short
```

Revise cuidadosamente os arquivos que aparecerem. `.gitignore` protege contra inclusão acidental de `.db`, `.pem`, configurações e saídas de compilação, **mas não é uma ferramenta de remoção de segredos já versionados**. Use `git status` e confira o conteúdo do commit. Não inclua bancos, tokens, chaves privadas ou códigos de recuperação.

O repositório de **código-fonte** deve ser separado do repositório de distribuição do executável para não afetar o atualizador automático.
