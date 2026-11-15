# VoltGuard — Pacote de projeto Rev. B

## 1. Conteúdo

| Pasta | Arquivo | Finalidade |
|---|---|---|
| `desenho/` | `VoltGuard_Desenho_Tecnico_RevB.pdf` | Desenho técnico A3, 4 folhas (VG-DE-01 esquema e lista de materiais; VG-DM-02 base; VG-DM-03 tampa; VG-MO-04 montagem) |
| `cad/` | `voltguard_caixa.scad` | Modelo paramétrico da caixa (OpenSCAD) |
| `cad/` | `voltguard_base.stl`, `voltguard_tampa.stl` | Arquivos prontos para o fatiador (já orientados) |
| `wokwi/` | `diagram.json`, `sketch.ino`, `voltguard_core.h`, `libraries.txt` | Simulação online completa no Wokwi |
| `wokwi/` | `falstad_link.txt` | Link do circuito de condicionamento do SCT no Falstad (abre direto no navegador) |
| `firmware/VoltGuard/` | `VoltGuard.ino` + `voltguard_core.h` (mesma pasta) | Firmware para o protótipo físico (Arduino IDE) |
| `firmware/test/` | `test_core.cpp` | Testes do núcleo de diagnóstico (25 verificações) |
| `firmware/VoltGuard/` | `voltguard_bancada.h` | Bancada virtual: modelos físicos de sensor, ADC, cabo e sondas |
| `firmware/VoltGuard_Ensaio/` | `VoltGuard_Ensaio.ino` | Roteiro de ensaio automático que roda no ESP32 ou no Wokwi |
| `wokwi_ensaio/` | projeto Wokwi + `ensaio.test.yaml` | Bancada virtual no Wokwi, com cenário para Wokwi CI |
| `wokwi_sct_chip/` | projeto Wokwi + chip `sct013-sim` | Simulação com sinal alternado de verdade no ADC (chip personalizado) |
| `ensaio/` | `VoltGuard_Procedimento_de_Ensaio_RevB.pdf` | Procedimento de ensaio físico (VG-PE-05) |
| `ensaio/` | `VoltGuard_Relatorio_Ensaio_Simulado_RevB.pdf` | Resultados da bancada virtual (VG-RE-06) |
| `ensaio/sim/` | `bancada_pc.cpp`, `graficos.py`, `dados/`, `fig/` | Bancada virtual no PC, dados em CSV e gráficos |
| `protoboard/` | `VoltGuard_Montagem_Protoboard_RevB.pdf`, `protoboard_voltguard.png`, `protoboard.py` | Montagem em protoboard, lista de fios e conferência automática |

## 2. Melhorias em relação à versão 4 do documento

1. **Faixa do ADC:** a referência passou de 1,65 V para ≈1,32 V (R1 = 15 kΩ, R2 = 10 kΩ). Com isso, a faixa linear do ESP32 vai até ≈24 A, contra ≈17 A antes.
2. **Proteção da entrada:** R4 = 1 kΩ em série e C3 = 10 nF no GPIO34.
3. **Leitura do ADC:** passa a usar `analogReadMilliVolts()`, que aplica a calibração de fábrica. A janela de amostragem cobre 10 ciclos de 60 Hz (833 amostras), as primeiras leituras são descartadas e há um piso de ruído. O firmware avisa quando o sinal sai da faixa linear.
4. **Correntes baixas:** o parâmetro `cfg.nEspiras` permite passar o condutor várias vezes pelo núcleo, para trabalhar com limiares de 1 a 3 A.
5. **Temperatura:** foi incluído um segundo DS18B20 para medir o ambiente. O diagnóstico agora usa a elevação ΔT (ponto − ambiente) e um limite absoluto (60 °C), no lugar do valor fixo de 40 °C.
6. **Taxa de elevação:** calculada por regressão linear numa janela de 160 s, em °C/min. Não compara mais apenas duas leituras seguidas.
7. **Mau contato:** só é apontado se houver corrente, e quando ΔT fica acima do esperado (k·I²) por 60 s. Calor sem corrente passa a ser classificado como "AQUECIMENTO EXTERNO".
8. **Alarmes estáveis:** histerese de 10 % e tempos de confirmação. Sobrecarga exige 30 s com resposta térmica, ou 5 min de corrente alta.
9. **Falhas do sensor:** leituras de −127 °C (sensor desconectado) e 85 °C (valor de reset) são tratadas e geram o estado "FALHA DE SENSOR".
10. **Sinalização local:** LEDs verde, amarelo e vermelho, mais um buzzer acionado por transistor.
11. **Camada IoT:** publicação MQTT opcional (`USAR_MQTT 1`) nos tópicos `voltguard/<id>/telemetria` e `voltguard/<id>/alerta`.

## 3. Simulação no Wokwi

1. Acesse wokwi.com e crie um projeto ESP32 (Arduino).
2. Substitua o conteúdo de `diagram.json` e `sketch.ino` pelos arquivos da pasta `wokwi/`.
3. Adicione o arquivo `voltguard_core.h` (seta ▾ ao lado das abas → "New file").
4. Crie `libraries.txt` com o conteúdo do arquivo fornecido, ou adicione pelo Library Manager as bibliotecas OneWire, DallasTemperature e PubSubClient.
5. Inicie a simulação e use os controles:
   - **Potenciômetro:** define a corrente simulada, de 0 a 15 A. O firmware gera a senoide de 60 Hz e aplica o mesmo cálculo RMS usado no protótipo real.
   - **DS18B20 "tponto" e "tamb":** clique em cada sensor para alterar a temperatura.
6. **Para ver os dados MQTT:** use um cliente web (por exemplo, o HiveMQ Web Client) conectado a `broker.hivemq.com` e assine `voltguard/#`.

Cenários sugeridos:

| Ação | Estado esperado |
|---|---|
| Potenciômetro > 55 % (≈8 A) | ALERTA PREVENTIVO |
| Manter > 8 A e subir T-ponto 25 °C acima de T-amb | SOBRECARGA após 30 s |
| Potenciômetro em ~25 % (≈4 A) e T-ponto 20 °C acima de T-amb | ALERTA DE TEMPERATURA → POSSÍVEL MAU CONTATO após 60 s |
| Potenciômetro em 0 e T-ponto alto | AQUECIMENTO EXTERNO (e não mau contato) |

## 4. Circuito analógico no Falstad

Abra o link contido em `wokwi/falstad_link.txt`. Para ver a forma de onda no GPIO34, clique com o botão direito sobre o voltímetro e escolha "Ver no osciloscópio". Para outra corrente, edite a amplitude da fonte senoidal: 1,414 V de pico equivale a 30 A.

## 5. Protótipo físico

- **Placa:** "ESP32 Dev Module" (pacote esp32 by Espressif Systems).
- **Ao ligar:** o monitor serial (115200 baud) mostra os endereços dos dois DS18B20. O índice 0 é o ponto monitorado e o índice 1 é o ambiente. Se ficarem trocados, inverta os bornes J2 e J3.
- **Calibração:** com uma carga resistiva conhecida, compare a leitura com um alicate amperímetro true RMS e ajuste `cfg.calibracao`. Depois, meça a leitura sem carga e ajuste `cfg.pisoRuidoA`.
- **Limites:** os valores de `cfg.iLimiteA`, `cfg.kTermico` e dos tempos de confirmação devem ser definidos para o condutor monitorado, a partir do ensaio térmico (etapa 7 do roteiro).

## 6. Impressão 3D

| Parâmetro | Valor |
|---|---|
| Material | PETG |
| Bico / camada | 0,4 mm / 0,2 mm |
| Perímetros | 3 |
| Preenchimento | 25 % |
| Suporte | Não precisa |

Para mudar dimensões (por exemplo, uma placa de outro tamanho), altere os parâmetros no topo do `.scad` e gere novamente:

```
openscad -D 'parte="base"'  -o voltguard_base.stl  voltguard_caixa.scad
openscad -D 'parte="tampa"' -o voltguard_tampa.stl voltguard_caixa.scad
```

Antes de imprimir, confira com paquímetro as medidas dos componentes comprados: furos da placa perfurada, prensa-cabo PG7 e jaque P2.

## 7. Como usar o Wokwi neste projeto

São três projetos, cada um com uma finalidade.

**7.1 `wokwi/`: demonstração interativa.** O potenciômetro define a corrente de 0 a 15 A e o firmware gera internamente a senoide do sensor. Clicando em cada DS18B20 você muda a temperatura. Serve para mostrar os estados mudando, os LEDs e o buzzer.

**7.2 `wokwi_sct_chip/`: sinal alternado de verdade no ADC.** Um chip personalizado (`sct013-sim`) entrega no GPIO34 a mesma tensão que o SCT e o divisor entregariam: VREF mais uma senoide de 60 Hz. Assim o firmware roda com `MODO_SIMULACAO 0`, isto é, o mesmo caminho de aquisição do protótipo real. Para montar no navegador:
1. Crie um projeto ESP32.
2. Use o botão de novo arquivo e escolha "Custom chip", com o nome `sct013-sim` e a linguagem C.
3. Substitua o conteúdo de `sct013-sim.chip.json` e `sct013-sim.chip.c` pelos arquivos do pacote.
4. Substitua `diagram.json` e `sketch.ino`, e adicione `voltguard_core.h` e `libraries.txt`.

Durante a simulação, clique no chip para ajustar a corrente e a referência. Este projeto não foi executado no Wokwi durante a preparação do pacote: rode uma vez para conferir.

**7.3 `wokwi_ensaio/`: bancada virtual automática.** Roda todo o roteiro do VG-PE-05 dentro do ESP32 simulado, usando o núcleo real do firmware e modelos físicos no lugar dos sensores. Basta colar `sketch.ino`, `voltguard_core.h` e `voltguard_bancada.h` num projeto ESP32 e iniciar. O resultado aparece no monitor serial, com uma linha por ensaio e, no final, `RESULTADO GERAL: APROVADO`. O Wokwi gratuito simula devagar (cerca de 5 % a 10 % da velocidade real), então o roteiro completo leva alguns minutos. No PC, o mesmo roteiro roda em menos de um segundo com `ensaio/sim/bancada_pc.cpp`.

**7.4 Testes automáticos (Wokwi CI).** Os arquivos `*.test.yaml` descrevem cenários que o Wokwi executa sozinho: mexe no potenciômetro, espera mensagens no serial e falha se algo não acontecer. Para usar:
1. Instale o PlatformIO e o `wokwi-cli`.
2. Crie um token no painel do Wokwi CI e exporte a variável de ambiente `WOKWI_CLI_TOKEN`.
3. Rode, dentro da pasta do projeto:

```
pio run
wokwi-cli . --scenario ensaio.test.yaml --timeout 900000
```

O mesmo comando pode rodar no GitHub Actions a cada alteração do código, de modo que um erro de lógica seja detectado antes de chegar à placa.

**7.5 Prova de que os testes pegam erros.** Foi feito um teste de mutação: a condição "só há mau contato se houver corrente" foi retirada de propósito do firmware. O roteiro acusou imediatamente a falha no cenário C5 (aquecimento externo confundido com mau contato), que era justamente o erro da versão 4 do documento.
