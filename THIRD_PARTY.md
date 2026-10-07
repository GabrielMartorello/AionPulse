# Referências e licenças

AionPulse é distribuído sob GPL-3.0-only. O texto integral está em LICENSE. Nenhum binário ou código descompilado do Aletheia está incluído.

## Aether — GPL-3.0

Enquadramento, dano, nomes e catálogo de curas foram adaptados/consultados nestes arquivos:

- https://github.com/Helveticxa/Aether-Aion2-DPS-meter-Global/blob/main/src-tauri/src/dps_meter/capture/parser/damage.rs
- https://github.com/Helveticxa/Aether-Aion2-DPS-meter-Global/blob/main/src-tauri/src/dps_meter/capture/parser/nickname.rs
- https://github.com/Helveticxa/Aether-Aion2-DPS-meter-Global/blob/main/src-tauri/src/dps_meter/region.rs
- https://github.com/Helveticxa/Aether-Aion2-DPS-meter-Global/blob/main/src-tauri/src/dps_meter/capture/processor.rs
- https://github.com/Helveticxa/Aether-Aion2-DPS-meter-Global/blob/main/src-tauri/data/healing_skill_code.json

## Aion2Flow — GPL-3.0

Party, recursos de vida, layouts defensivos e pools de escudo foram adaptados/consultados nestes arquivos:

- https://github.com/cloris-chan/Aion2Flow/blob/main/src/Aion2Flow.Protocol/Packets/PacketPlayerGroupParser.cs
- https://github.com/cloris-chan/Aion2Flow/blob/main/src/Aion2Flow.Protocol/Packets/Packet0438DamageParser.cs
- https://github.com/cloris-chan/Aion2Flow/blob/main/src/Aion2Flow.Protocol/Packets/Packet0538PeriodicValueParser.cs
- https://github.com/cloris-chan/Aion2Flow/blob/main/src/Aion2Flow.SceneRuntime/Combat/CombatEvidence.cs
- https://github.com/cloris-chan/Aion2Flow/blob/main/src/Aion2Flow.SceneRuntime/Canonicalization/PeriodicPoolCanonicalizer.cs

## Dependências

- python-lz4 4.4.5: BSD. Instalado a partir de requirements.txt, não vendorizado neste repositório.
- Python/Tkinter: licenças dos respectivos projetos, não redistribuídos.
- Npcap: dependência externa, não redistribuída.
- Ruff: ferramenta de desenvolvimento, licença MIT, não redistribuída.

Consultado em 06/10/2026. A seleção de variantes de autocura também foi corroborada com registros locais durante o desenvolvimento; os registros privados não fazem parte deste repositório.

## Runtime do instalador

O pacote Windows inclui Python (PSF), Tcl/Tk, lz4 e o bootloader PyInstaller (GPL com exceção do bootloader). As licenças são incluídas em _internal/licenses. A licença Tcl 8.6.12 vem de https://github.com/tcltk/tcl/blob/core-8-6-12/license.terms. O Npcap não é redistribuído no pacote; o assistente oferece seu download direto de https://npcap.com/.
