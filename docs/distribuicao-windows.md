# Distribuição e falsos positivos no Windows

O AionPulse é empacotado em uma pasta, com Python e bibliotecas separados, sem UPX ou ofuscação. O executável contém nome do produto, versão e autor. O app usa Npcap para observar a rede; não injeta pacotes ou lê a memória do jogo. O instalador não cria exclusões, altera configurações de antivírus ou adiciona inicialização automática.

Essas escolhas facilitam a inspeção e a distribuição, mas não garantem ausência de alertas. Microsoft Defender Antivirus, SmartScreen e Smart App Control são mecanismos diferentes. Um alerta de editor desconhecido não equivale, por si só, a uma detecção de malware.

## Assinatura de lançamento

A versão beta inicial ainda não é assinada digitalmente. Para assinar um lançamento público, obtenha um certificado de assinatura de código emitido por uma autoridade confiável ou use um serviço de assinatura com identidade validada. Um certificado autoassinado não estabelece confiança pública.

O build aceita um certificado disponível no repositório do Windows, sem armazenar senhas ou chaves no projeto:

```powershell
.\build-installer.ps1 -Compiler 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe' -SignTool 'signtool.exe' -CertificateThumbprint 'IMPRESSAO_DIGITAL_DO_CERTIFICADO'
```

O executável do aplicativo é assinado antes de entrar no instalador; o instalador é assinado depois. As assinaturas usam SHA-256, carimbo de tempo e verificação Authenticode. Mantenha a identidade do editor consistente entre versões. Assinar reduz a incerteza sobre o editor, mas não garante aprovação do antivírus ou ausência de avisos de reputação.

## Se houver detecção

Registre a versão, o SHA-256 do arquivo e o nome exato da detecção. Investigue o pacote antes de classificá-la como falso positivo. Se confirmar um erro de classificação, o responsável pelo projeto pode enviar o arquivo ao [portal Microsoft Security Intelligence](https://www.microsoft.com/en-us/wdsi/filesubmission), como desenvolvedor. Esse envio compartilha o arquivo com a Microsoft e deve ser autorizado pelo responsável.

Não oriente usuários a desativar o Defender, restaurar um arquivo bloqueado sem análise ou criar exclusões amplas. Publique código-fonte, hashes e resultados das verificações de cada versão. Uma análise local limpa não garante resultado idêntico em outro computador ou em outra data.

Referências: [Microsoft — FAQ para desenvolvedores](https://learn.microsoft.com/en-us/defender-xdr/developer-faq), [assinatura para Smart App Control](https://learn.microsoft.com/en-us/windows/apps/develop/smart-app-control/code-signing-for-smart-app-control).
