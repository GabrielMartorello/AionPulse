# Verificação de desempenho

Na refatoração de 06/10/2026, uma simulação local adicionou 10.000 eventos de dano, cura e dano recebido distribuídos entre seis jogadores. Foram feitas 900 consultas às taxas dos últimos cinco segundos, mantendo o mesmo instante de consulta.

| Implementação | Tempo das 900 consultas |
|---|---:|
| Releitura das filas a cada consulta | 1,454 s |
| Totais incrementais por métrica/jogador | 0,000685 s |

É um microbenchmark das consultas, não uma medição de FPS, CPU total ou velocidade do aplicativo inteiro. Resultados variam por máquina e volume de eventos. O custo foi transferido para a entrada e expiração de eventos; cada atualização normal consulta somente os totais por jogador. Testes de equivalência verificam os resultados contra uma soma direta dos eventos da janela.

A captura consulta descartes do Npcap a cada segundo, em vez de uma chamada nativa por pacote. Pacotes sem opcode de combate não passam pelos parsers de dano/cura/tank. App e overlay compartilham instante e taxas na atualização, preferências permanecem em memória e identidade/grupo são restaurados com uma leitura de arquivo.
