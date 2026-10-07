# Identificação de nomes e party / Name and party identification

## Português

O código atual reconhece registros de identidade `33 36`, `44 36` e `45 36` pela máscara que informa a presença do nome. Também procura múltiplos registros dentro de um pacote, incluindo registros que não estão no início dele. Os formatos antigos continuam disponíveis para compatibilidade.

Foi acrescentado suporte à lista `02 97`, com nomes, slots e campos de tamanho variável. Essa lista contém uma identidade persistente que não é o ID de combate; o parser não usa esse valor como se fosse o ID do jogador. A lista é associada aos atores já observados somente quando os nomes têm correspondência única e incluem o personagem local. Uma lista incompleta ou ambígua não remove integrantes.

Os novos formatos são adaptações do A2Tools sob GPL-3.0, com referência em THIRD_PARTY.md. Testes sintéticos cobrem múltiplos nomes, Unicode, máscaras diferentes, slots vazios, truncamentos e ambiguidades. Uma comparação com 584 amostras locais preservou os 115 nomes reconhecidos pelo parser anterior. Não havia amostras `02 97` nesse conjunto; esse caminho ainda precisa de validação em uma sessão real.

Isso amplia os pacotes que conseguimos ler, mas não recria um nome que não tenha sido enviado pelo jogo. O problema de precisar se aproximar de um integrante ainda pode ocorrer. Estes ajustes estão no código atual; o instalador da release Beta 1 não foi substituído.

## English

The current source recognizes `33 36`, `44 36` and `45 36` identity records through the mask indicating whether a name is present. It also finds multiple identity records embedded inside a packet, rather than only at its beginning. Earlier formats remain available for compatibility.

The `02 97` roster format is now supported, including names, slots and variable-length fields. Its persistent identifier is not a combat actor ID and is not used as one. The roster is linked to observed actors only when names match uniquely and the local character is included. Incomplete or ambiguous rosters do not remove members.

The new formats are adapted from A2Tools under GPL-3.0; attribution is in THIRD_PARTY.md. Synthetic tests cover multiple names, Unicode, different masks, empty slots, truncation and ambiguity. A comparison against 584 local samples preserved all 115 names recognized by the earlier parser. That sample set contained no `02 97` rosters, so this path still needs validation in a live session.

These changes expand the records we can read, but cannot reconstruct a name the game has not sent. Approaching a party member may still be necessary. These improvements are in the current source; the Beta 1 release installer has not been replaced.

