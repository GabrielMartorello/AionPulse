# Instalar AionPulse no Windows

1. Execute `AionPulse-Setup-0.1.0-beta.1-x64.exe`.
2. Escolha Português (Brasil) ou English e aceite a licença do AionPulse.
3. Confirme a pasta e a criação do atalho na área de trabalho.
4. Se faltar Npcap, mantenha selecionada a opção de instalação dele. O assistente baixa a versão 1.89 diretamente de `npcap.com`, verifica o SHA-256 do arquivo e abre o instalador oficial. Aceite a solicitação de administrador do Windows e conclua esse assistente.
5. Finalize a instalação e abra AionPulse pelo atalho. Abra o medidor antes de entrar no jogo ou trocar de área para capturar a identificação da party.

Não é necessário instalar Python, executar pip, configurar um ambiente virtual ou instalar o Visual C++ separadamente. O pacote contém Python, Tcl/Tk, lz4 e os recursos necessários para executar esta versão em Windows 10/11 x64.

O AionPulse é instalado para o usuário atual em `%LOCALAPPDATA%\Programs\AionPulse`, com atalhos no menu Iniciar e, quando selecionado, na área de trabalho. Apenas a instalação do driver Npcap exige a autorização de administrador.

## Se o Npcap já estiver instalado

O assistente detecta a biblioteca do Npcap e não o reinstala. Se a captura falhar, consulte as configurações de acesso do driver: uma instalação restrita a administradores pode pedir elevação quando o medidor abrir.

## Instalação sem internet

Python e bibliotecas já estão no pacote. A conexão com a internet só é necessária para obter o Npcap quando ele estiver faltando. Se preferir, instale-o previamente pelo [site oficial](https://npcap.com/#download). É possível desmarcar essa tarefa e instalar o app sem o driver, mas a captura não funcionará até o Npcap ser instalado.

O Npcap gratuito não pode ser redistribuído dentro deste instalador; seu download e seu contrato de licença são fornecidos pelo fabricante. Consulte a [licença do Npcap](https://npcap.com/#download).

## Atualizar ou remover

Para atualizar, encerre o medidor pelo menu do overlay e execute o novo instalador na mesma pasta. As preferências e o cache ficam em `%LOCALAPPDATA%\AionPulse` e são preservados.

Para remover, use Configurações do Windows → Aplicativos → AionPulse → Desinstalar. O desinstalador remove o aplicativo e os atalhos, preservando seus dados locais e o Npcap, que pode ser usado por outros programas.

## Código-fonte e licenças

O pacote inclui o código desta versão em `source\AionPulse-source.zip`. As licenças do Python, das bibliotecas e do AionPulse ficam em `_internal\licenses` e `LICENSE`. É possível construir o instalador a partir do código seguindo o README.
