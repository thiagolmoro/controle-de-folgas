# Histórico de versões

## v4.1.0 — 13/10/2026

**Versão oficial publicada no GitHub Releases.**

- Substituição do mecanismo de senha mestra fixa por desafios assinados Ed25519 para suporte autorizado.
- Autorizações vinculadas à instalação e operação, com prazo de 30 minutos e uso único.
- Melhorias em backups SQLite com a API de backup nativa (inclusive para WAL).
- Correção de erro de callback de redimensionamento após encerramento de janela Tkinter.
- Remoção de rotina legada de interpretação de frações que não era utilizada no cadastro atual.
- Separação das rotinas de suporte e backup em módulos próprios.
- Testes automatizados adicionados e ampliados para 14 casos.
- Compatibilidade e atualização automática **v4.0.2 → v4.1.0** verificadas no Windows com banco demonstrativo.

## v4.0.2

- Interface com splash e mecanismo de atualização automática GitHub Releases.
- Base de gestão de folgas, funcionários, lançamentos, relatórios, auditoria e Lixeira.

[Releases oficiais](https://github.com/thiagolmoro/controle-de-folgas-releases/releases)
