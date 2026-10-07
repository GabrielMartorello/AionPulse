# Arquitetura

| Módulo | Responsabilidade |
|---|---|
| app.py | Interface principal, consumo da fila, grupo, exportação e ciclo de atualização |
| overlay.py | Overlay, barras, modos, tamanho e posição |
| metrics.py | Metadados únicos dos modos, cores e taxas |
| config.py | Preferências em memória e gravação atômica de dados locais |
| native.py | Integração de leitura com Npcap e extração TCP |
| capture.py | Thread de captura, remontagem por conexão e publicação de eventos |
| protocol.py | Framing, LZ4, TCP, dano e nomes |
| party.py | Entradas, listas completas e resolução conservadora da party |
| support.py / tank.py | Cura, dano recebido e absorção de escudo |
| stats.py | Totais do combate e janela móvel de cinco segundos |
| identity_cache.py | Identidade temporária vinculada à conexão TCP |
| instance.py / branding.py | Instância única e integração visual com Windows |
| AionPulseLauncher.cs | Iniciador opcional com ícone embutido |

A captura trabalha em thread própria e publica em uma fila limitada. Apenas a thread Tk altera widgets e estatísticas. O ciclo da interface separa consumo de eventos, persistência de identidade, renderização e diagnóstico. App e overlay usam o mesmo instante e as mesmas taxas em cada atualização.

As taxas mantêm somas incrementais por jogador e métrica. Ao expirar um evento da janela, sua quantidade é subtraída; consultas normais percorrem os jogadores ativos, sem reler todos os eventos. Os totais do encontro permanecem após a taxa cair a zero. Os testes preservam também a exclusão de eventos futuros nas consultas sintéticas.

Preferências são lidas uma vez, gravadas atomicamente quando mudam e não ficam no diretório do código. A restauração de identidade/grupo usa uma leitura única e valida conexão e prazo. O caminho do runtime não está embutido no iniciador.
