# Como identificar seu personagem e sua party

Abra o AionPulse antes de entrar no jogo ou de trocar de área. A identificação é automática: não é necessário informar nomes, vincular contas ou entrar em combate.

## Quando a lista está vazia ou mostra IDs

O medidor recebe apenas os dados que o jogo transmite enquanto a captura está ativa. Se você abrir o aplicativo com os personagens já carregados, o jogo pode não repetir imediatamente os nomes ou a lista completa da party.

1. Mantenha a captura ativa.
2. Teleporte, troque de canal ou entre em uma área com carregamento para o jogo reenviar sua identificação.
3. Para integrantes ainda sem nome, aproxime-se deles na mesma área/canal. Afastar-se e voltar também pode provocar o reenvio da identidade.
4. Aguarde a indicação de nomes identificados no aplicativo.

Essas ações permitem uma nova observação; não garantimos que todo carregamento reenvie a lista completa. Integrantes em outras áreas podem continuar pendentes. A indicação de nomes identificados se refere aos integrantes observados, e não garante que ninguém esteja faltando.

## Reiniciar e fechar

**Reiniciar** limpa os valores de combate e preserva nomes, integrantes e captura. Não limpa o cache.

Fechar a janela principal oculta a interface e mantém a captura em segundo plano. Para interromper a captura, escolha **Encerrar medidor** no menu do overlay. Ao reabrir depois de encerrar, o cache pode restaurar a identidade e a última party observada na mesma conexão, por até 15 minutos. Mudanças ocorridas enquanto o app estava desligado dependem de novos pacotes para serem confirmadas.

## Limpar o cache

Limpar o cache é uma ação de diagnóstico, não uma etapa normal de uso. Com o aplicativo encerrado, o arquivo de identidade é `%LOCALAPPDATA%\AionPulse\identity-cache.json`. Apagá-lo força uma identificação nova e pode deixar a lista vazia até o jogo reenviar os dados. Não apague `preferences.json` para testar a party: esse arquivo guarda idioma, posição do overlay e outras preferências.

## Como interpretar a indicação no app

| Indicação | Significado |
| --- | --- |
| Aguardando identificação | Ainda não observamos integrantes suficientes para montar a lista. |
| Identificação parcial | Há integrantes observados, mas faltam nomes ou sua identificação. |
| Nomes dos integrantes observados identificados | Os integrantes atualmente observados têm nomes; a captura continua acompanhando mudanças. |

O app identifica jogadores a partir de pacotes de identidade, listas e status específicos da party. Dano, proximidade ou ausência de atividade, isoladamente, não comprovam participação ou saída. O medidor não solicita ao servidor uma lista nova.

## Referências e limites

O [guia do Aletheia](https://github.com/p62003/aletheia_AION2_DPS_Meter/blob/main/Guide_Troubleshoot_EN.md) também descreve identificação após uma mudança de cenário. O [Aion2Flow](https://github.com/cloris-chan/Aion2Flow/blob/main/tests/Aion2Flow.ReplayTests/Capture/PacketLogReplayServiceTests.cs) testa recuperação de membros pelos status antes da lista completa. Essas referências não garantem comportamento idêntico em todas as versões e regiões do jogo.
