# Segurança e privacidade

## O que é público e o que deve permanecer privado

- `support_public_key.py` contém **somente a chave pública Ed25519**, usada para verificar autorizações. Não é um segredo.
- A **chave privada de suporte** (`*.pem`) deve ficar cifrada, fora do diretório do projeto e do GitHub, e ter backup protegido.
- O código de recuperação administrativa, bancos SQLite, backups, credenciais locais e configurações de instalações nunca devem ser publicados.
- As capturas do README usam um conjunto de dados **fictícios**.

## Modelo de autorização por suporte

O aplicativo cria uma solicitação vinculada a instalação, operação e nonce; uma ferramenta separada assina a solicitação com a chave privada protegida. O EXE verifica a assinatura usando somente a chave pública. Solicitações expiram após 30 minutos e são destinadas a uso único. Recuperação de senha por código local permanece disponível.

**Limite de segurança:** este mecanismo protege o fluxo de interface previsto, mas não impede que uma pessoa com acesso ao sistema de arquivos modifique diretamente um banco SQLite, substitua o EXE ou controle o computador. Em instalações operacionais, aplique também permissões adequadas do Windows e políticas de backup.

## Para criar uma variante independente

A ferramenta `ferramentas/suporte_cli.py` só gera um par de chaves quando `support_public_key.py` está **sem chave**. Se desejar uma instalação independente, faça isso **em um fork**, com seu próprio par de chaves e repositório de Releases, depois de avaliar a compatibilidade das instalações. Nunca rotacione a chave usada pelo executável oficial simplesmente editando o repositório de portfólio.

## Divulgação responsável

Não inclua segredos em issues, screenshots, commits ou Pull Requests. Caso encontre uma vulnerabilidade de segurança, evite publicá-la com detalhes de exploração antes de comunicar o mantenedor pelo GitHub.
