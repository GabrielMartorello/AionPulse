# AionPulse

**Português (Brasil)** · [English](README.en.md)

Acompanhe o desempenho do seu grupo no AION2 com um overlay compacto e interface em português e inglês. Compare dano causado, cura realizada e dano recebido com barras por jogador, totais do combate e taxas dos últimos cinco segundos.

![Ícone do AionPulse](assets/aionpulse-64.png)

## Recursos

Consulte o [guia de identificação e party](docs/guia-do-usuario.md) se a lista estiver vazia ou mostrar IDs. Não é necessário combater: mantenha a captura ativa durante um carregamento e uma nova observação dos integrantes.

- Modos DPS, Cura, Recebido e Tudo, independentes no app e no overlay.
- Totais, taxas dos últimos 5 segundos e barras por jogador.
- Recebido inclui dano à vida e absorção de escudo identificada, na mesma medida.
- Identificação automática de personagem e atualização por pacotes da party.
- Botão Reiniciar no overlay, posição persistente e tamanhos configuráveis.
- Detalhes por habilidade, CSV e contadores locais de diagnóstico.
- Instância única, sem login, Discord, uploads ou injeção de pacotes.

## Instalação pelo instalador

[Baixe o instalador para Windows](https://github.com/GabrielMartorello/AionPulse/releases/tag/v0.1.0-beta.1) e execute `AionPulse-Setup-0.1.0-beta.1-x64.exe`. Python, Tcl/Tk e lz4 já estão incluídos; não é necessário configurar Python ou pip. O assistente oferece o download do Npcap pelo site oficial se ele estiver faltando, cria atalhos e inclui um desinstalador. Veja o [guia de instalação](docs/instalacao.md).

### Requisitos para executar pelo código-fonte

Windows 10/11 de 64 bits, Python 3.12 ou superior com Tkinter e Npcap instalado. Se o Npcap estiver configurado para acesso apenas por administradores, execute o medidor com essa permissão. A porta padrão é 13328; a captura acompanha o tráfego do servidor para o cliente.

## Instalação pelo código-fonte

Na pasta do projeto, pelo PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py --capture --overlay
```

Para abrir também a janela principal, acrescente `--show-main`. É possível executar `app.py` sem argumentos e iniciar a captura pela interface.

Para compilar o iniciador com a logo:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
.\AionPulse.exe
```

O iniciador usa `.venv\Scripts\pythonw.exe`, a variável opcional `AIONPULSE_PYTHON` ou `pythonw.exe` disponível no PATH. O executável é um iniciador; Python, dependências e arquivos do projeto continuam necessários. O build usa o compilador C# do .NET Framework 4.x e não baixa um compilador.

## Dados locais

AionPulse v0.1.0 Beta 1 · créditos: [@GabrielMartorello](https://github.com/GabrielMartorello).

O seletor de idioma alterna entre Português (Brasil) e English e aplica a escolha à janela principal e ao overlay. O switch **Valores completos** alterna os números das barras entre abreviados e completos. Ambas as preferências são salvas. **Reiniciar** limpa os contadores de combate e mantém a identidade e a party detectadas.

A região é consultada a partir do endereço do servidor da conexão de jogo capturada, sem consultar serviços de geolocalização. Nesta beta, os endereços `193.202.112.174` e `193.202.112.191` foram observados durante sessões declaradas como América do Sul; não estendemos essa associação ao restante da faixa. A identificação da Coreia usa a referência pública descrita em THIRD_PARTY.md. Outros endereços aparecem como **não identificada**; IDs de servidor compartilhados entre serviços não são usados para adivinhar a região.

Preferências, identidades temporárias e log de erros ficam em `%LOCALAPPDATA%\AionPulse`. Para mudar a pasta, defina `AIONPULSE_DATA_DIR`. A identidade e a party em cache têm validade de 15 minutos e são vinculadas à conexão TCP observada; não são uma configuração de pessoas fixas.

`--diagnostic-state` grava um estado local com nomes e contadores para depuração. Ele fica desativado por padrão. Não inclua esses dados, capturas ou relatórios privados no repositório; as regras de `.gitignore` também excluem cópias colocadas na pasta do projeto.

## Desenvolvimento

### Gerar o instalador

Instale [Inno Setup 6.7.3](https://jrsoftware.org/isdl.php) e as dependências de build. Em uma cópia do código:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\build-installer.ps1 -Compiler 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe'
```

O resultado fica em `dist\installer`. O build inclui o runtime e um arquivo com o código-fonte público, sem preferências, identidades, logs ou pacotes pessoais. O instalador não inclui o binário do Npcap: oferece seu download oficial com hash fixado. Consulte e atualize a versão/hash do driver no arquivo `.iss` quando necessário. O compilador Inno Setup 6.7.3 usado neste build permite uso não comercial; consulte sua licença antes de distribuir comercialmente.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
```

Os testes usam dados sintéticos e fixtures de protocolo. Não exigem uma conta do jogo nem captura de rede. A integração contínua executa testes, lint e verificação de formatação. Consulte [CONTRIBUTING.md](CONTRIBUTING.md) e [docs/architecture.md](docs/architecture.md).

## Limites conhecidos

O código atual inclui novos formatos de identidade e lista de party adaptados do A2Tools. Veja [as melhorias e o estado da validação](docs/identity-improvements.md). O instalador Beta 1 permanece como publicado e não inclui esses ajustes novos.

A recuperação sem combate também correlaciona a identidade remota de party (`1C92`) com o bloco de identidade permanente em `4536`, usando personagem e servidor, sem exigir que seu personagem tenha sido identificado primeiro. Essa associação foi validada nos formatos observados nesta beta; se o medidor iniciar depois do pacote de identidade de um integrante e esse pacote não for reenviado, o nome ainda depende de uma nova observação desse jogador. O botão Reiniciar processa as identidades e mudanças de party que estiverem na fila antes de limpar os contadores.

Os formatos reconhecidos são experimentais e podem mudar entre versões/regiões do jogo. O medidor não cobre todas as habilidades ou formatos. Cura é a quantidade informada pelos pacotes; não distingue cura efetiva de overheal. Não inferimos cura por alterações genéricas de HP.

Recebido soma dano à vida e absorção comprovada, mas não representa o dano bruto antes de todas as reduções. Indicadores de bloqueio/aparo não informam por si só a quantidade mitigada. A absorção exige observar o início do pool; abrir o app no meio de um escudo pode perder essa associação.

Entradas e listas completas de party atualizam o grupo sem combate. Ao iniciar sem uma lista completa, os pacotes de status específicos da party (`1B92`) recuperam IDs de integrantes observados; o nome depende de um pacote de identidade. Depois que uma lista completa confirma o grupo, status de jogadores ausentes não os adicionam novamente. Atualizações genéricas de vida não determinam participação. Se o jogo só enviar atualizações remotas sem identidade ou lista, não é possível reconstruir os nomes a partir desses pacotes. Ausência de dano não comprova saída. Perdas ou erros de captura tornam os totais incompletos.

## Licença

GPL-3.0-only. O código adaptado e as referências estão em [THIRD_PARTY.md](THIRD_PARTY.md). O projeto não é afiliado à NCSOFT nem aos projetos de referência. A logo original do AionPulse faz parte dos recursos deste projeto; não é uma marca oficial do jogo.

