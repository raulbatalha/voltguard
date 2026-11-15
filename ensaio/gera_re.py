"""Relatorio de Ensaio Simulado VG-RE-06 (bancada virtual)."""
from pathlib import Path as _P
RAIZ = str(_P(__file__).resolve().parents[1])  # raiz do repositorio
import json, sys
sys.path.insert(0, str(_P(__file__).resolve().parent))
import estilo_doc as E
from estilo_doc import P, H1, H2, I, COD, TAB, ESPACO, story, S, Doc
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak, Image, KeepTogether
from reportlab.lib.units import mm
from reportlab.lib import colors

E.TITULO_CAB = "VOLTGUARD   Relatório de Ensaio Simulado (Bancada Virtual)"
E.CODIGO_CAB = "VG-RE-06   Rev. B"
E.TITULO_PDF = "VoltGuard: Relatório de Ensaio Simulado"

D = RAIZ + "/ensaio/sim/dados/"
FIG = RAIZ + "/ensaio/sim/fig/"
R = json.load(open(D + "resumo.json"))
AJ = json.load(open(D + "e4_ajuste.json"))
import csv
e1 = list(csv.DictReader(open(D + "e1_exatidao.csv")))
e3 = list(csv.DictReader(open(D + "e3_baixa_corrente.csv")))
v = lambda x: f"{float(x):.2f}".replace(".", ",")
v1 = lambda x: f"{float(x):.1f}".replace(".", ",")


def FIGURA(arq, larg_mm, legenda, titulo=None):
    from PIL import Image as PI
    w, h = PI.open(FIG + arq).size
    img = Image(FIG + arq, width=larg_mm * mm, height=larg_mm * mm * h / w)
    bloco = ([Paragraph(titulo, S["h2"])] if titulo else []) + [img, Paragraph(legenda, S["leg"])]
    story.append(KeepTogether(bloco))
    story.append(Spacer(1, 4))


from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
S["leg"] = ParagraphStyle("leg", fontName="Serif-I", fontSize=9, leading=11, alignment=TA_CENTER, spaceBefore=2, spaceAfter=6)

# ================================ CAPA ================================
story += [Spacer(1, 45 * mm), Paragraph("VOLTGUARD", S["capa1"]), Spacer(1, 4 * mm),
          Paragraph("Sistema de monitoramento e prevenção de sobrecargas<br/>em infraestruturas elétricas", S["capa3"]),
          Spacer(1, 22 * mm), Paragraph("RELATÓRIO DE ENSAIO SIMULADO<br/>BANCADA VIRTUAL", S["capa2"]),
          Spacer(1, 6 * mm), Paragraph("Documento VG-RE-06, Revisão B", S["capa3"]), Spacer(1, 10 * mm),
          Paragraph("Resultados obtidos por simulação. Não substituem os ensaios físicos do procedimento VG-PE-05.", S["capa3"]),
          Spacer(1, 30 * mm)]
capa = Table([[Paragraph("Firmware ensaiado:", S["tab"]), Paragraph("voltguard_core.h Rev. B (núcleo real, sem alteração)", S["tab"])],
              [Paragraph("Ferramenta:", S["tab"]), Paragraph("voltguard_bancada.h e bancada_pc.cpp", S["tab"])],
              [Paragraph("Data da execução:", S["tab"]), Paragraph("14/11/2026", S["tab"])]],
             colWidths=[45 * mm, 105 * mm], rowHeights=[9 * mm] * 3)
capa.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.black), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
story += [capa, PageBreak()]

# ================================ 1 ================================
H1("1. OBJETIVO")
P("Este relatório apresenta os resultados da execução do roteiro de ensaios do VoltGuard numa bancada virtual, isto é, "
  "num ambiente em que o sensor de corrente, o conversor analógico do ESP32, o cabo monitorado e as sondas de temperatura "
  "são substituídos por modelos matemáticos. O objetivo é verificar, antes da montagem física, se a lógica de medição e de "
  "diagnóstico se comporta como esperado em cada situação prevista, e gerar dados que sirvam de referência para comparar com "
  "os resultados da bancada real.")

H1("2. COMO A BANCADA VIRTUAL FUNCIONA")
P("O ponto central do método é que o código ensaiado é o mesmo que roda no ESP32. O arquivo voltguard_core.h, que contém o "
  "cálculo da corrente eficaz, a validação das leituras de temperatura, a taxa de elevação e a máquina de estados do "
  "diagnóstico, foi compilado sem nenhuma modificação. Só o que estaria do lado de fora do microcontrolador foi trocado por "
  "modelos, reunidos no arquivo voltguard_bancada.h.")
P("A simulação avança em tempo virtual, segundo a segundo, com a dinâmica térmica calculada em passos de 0,1 s. A cada "
  "segundo o modelo gera uma janela de 833 amostras do sinal do sensor, exatamente como a função analogReadMilliVolts() "
  "entregaria, e o núcleo do firmware calcula a corrente, lê as temperaturas e atualiza o diagnóstico. Uma hora de ensaio "
  "simulado leva menos de um segundo no computador.")
H2("2.1 Modelos e parâmetros adotados")
TAB(["Elemento", "Modelo", "Parâmetros"], [
    ["Sensor SCT-013-030", "Senoide de 60 Hz com 4 % de 3ª harmônica; relação 30 A para 1 V eficaz", "Erro de relação sorteado entre ±1 % nos cenários"],
    ["Divisor de referência", "Nível médio somado ao sinal", "1,32 V (Rev. B) ou 1,65 V (versão 4)"],
    ["ADC do ESP32", "Ruído gaussiano, quantização de 1 mV, compressão fora de 0,15 a 2,45 V, saturação em 3,1 V", "Ruído de 3,5 mV eficaz"],
    ["Cabo monitorado", "Primeira ordem: ΔT tende a k·I² com constante de tempo τ", "k = 0,060 °C/A², τ = 300 s"],
    ["Mau contato", "Aquecimento adicional proporcional a I²", "1,5 °C/A² no cenário C4"],
    ["Fonte de calor externa", "Leva a superfície do cabo à temperatura da fonte", "60 °C ou 70 °C, τ = 25 s"],
    ["Sonda DS18B20", "Atraso térmico, resolução 0,0625 °C, offset fixo, 85 °C na 1ª leitura, −127 °C se desconectada", "τ = 6 s, offset sorteado entre ±0,3 °C"],
    ["Ambiente", "Constante durante o cenário", "Sorteado entre 29 °C e 31 °C"],
], [36, 72, 52])
H2("2.2 Limitações")
P("Os resultados dependem dos modelos acima, e os valores de ruído, constante térmica e atraso das sondas foram adotados a "
  "partir de valores típicos, não medidos. Por isso, este relatório demonstra que a lógica do firmware está correta e "
  "coerente com a física do problema, mas não prova a exatidão do protótipo físico. Os erros do sensor real, a não "
  "linearidade específica de cada ESP32 e o comportamento térmico do cabo verdadeiro só aparecem na bancada real, conforme "
  "o procedimento VG-PE-05. Os números deste relatório devem ser usados como referência para comparação.")

# ================================ 3 RESULTADOS ================================
H1("3. RESULTADOS")
H2("3.1 E1: exatidão da corrente em toda a faixa")
P("A corrente foi variada de 1 A a 30 A, com 20 janelas de medição em cada ponto, para as duas configurações do divisor. "
  "Neste ensaio o erro de relação do sensor foi zerado, de modo a isolar o efeito do circuito e do firmware. Na bancada real "
  "esse erro é removido pela calibração do Ensaio 5.")
FIGURA("e1_exatidao.png", 160, "Figura 1. Erro de medição em função da corrente para a Rev. B e para a versão 4.")
linhas = [[v1(r["i_ref_A"]), v(r["revB_A"]), v(r["revB_erro_pct"]), "sim" if r["revB_fora"] == "1" else "não",
           v(r["v4_A"]), v(r["v4_erro_pct"])] for r in e1 if float(r["i_ref_A"]) in (2, 10, 15, 17, 20, 22, 25, 28, 30)]
TAB(["Referência (A)", "Rev. B (A)", "Erro Rev. B (%)", "Aviso de faixa", "Versão 4 (A)", "Erro v4 (%)"], linhas,
    [27, 25, 27, 27, 27, 27], centro=(0, 1, 2, 3, 4, 5))
P(f"Entre 2 A e 15 A o maior erro da Rev. B foi de {v(R['e1_erro_max_2_15A_pct'])} %, bem dentro do critério de 5 %. "
  "Com a referência antiga de 1,65 V o erro começa a crescer acima de 17 A e chega a cerca de 4 % em 25 A e a quase 7 % "
  "em 30 A. Com a referência de 1,32 V a medição permanece exata até cerca de 24 A, e a partir de 25 A o firmware passa a "
  "avisar que o sinal saiu da faixa linear. Esse resultado confirma a correção feita no divisor.")

H2("3.2 E2: ruído sem carga")
P(f"Sem corrente no condutor e com o piso de ruído desligado, a leitura média foi de {v(R['e2_ruido_medio_A'])} A e a máxima "
  f"de {v(R['e2_ruido_max_A'])} A. Com o piso padrão de 0,15 A a leitura sem carga ficou em "
  f"{v(R['e2_leitura_com_piso_A'])} A em todas as janelas. O valor do piso está adequado ao ruído adotado no modelo e deve "
  "ser conferido no Ensaio 4 da bancada real, porque o ruído verdadeiro varia de placa para placa.")

FIGURA("e3_baixa_corrente.png", 150, "Figura 2. Erro em correntes baixas com uma e com cinco passagens do condutor pelo núcleo.", "3.3 E3: correntes baixas")
P("Com uma única passagem, o erro em 0,3 A chega a cerca de 6 %, porque o sinal fica próximo do ruído do conversor. "
  "Passando o condutor cinco vezes pelo núcleo e informando cfg.nEspiras = 5, o erro cai para menos de 0,3 % em toda a "
  "faixa ensaiada. É a técnica recomendada para demonstrar o sistema com cargas pequenas, como uma lâmpada.")

H2("3.4 E4: ensaio térmico e identificação da constante k")
P("O cabo foi submetido a 10 A durante 40 minutos e depois deixado esfriar por 20 minutos. A partir da elevação de "
  "temperatura medida pelas sondas, foi ajustada uma curva exponencial, da qual se obtêm a elevação final e a constante "
  "de tempo.")
FIGURA("e4_termico.png", 160, "Figura 3. Ensaio térmico simulado com o ajuste exponencial da elevação de temperatura.")
TAB(["Grandeza", "Valor do modelo", "Valor identificado", "Diferença"], [
    ["Constante k (°C/A²)", "0,0600", f"{AJ['k_fit']:.4f}".replace(".", ","), f"{abs(AJ['k_fit'] - 0.06) / 0.06 * 100:.1f} %".replace(".", ",")],
    ["Constante de tempo τ (s)", "300", f"{AJ['tau_s']:.0f}", f"{abs(AJ['tau_s'] - 300) / 300 * 100:.1f} %".replace(".", ",")],
], [50, 35, 40, 35], centro=(1, 2, 3))
P("O procedimento recuperou os parâmetros do cabo com diferença inferior a 3 %, o que mostra que o ensaio térmico proposto "
  "no VG-PE-05 é suficiente para calibrar o diagnóstico. O valor identificado foi usado como cfg.kTermico em todos os "
  "cenários seguintes, exatamente como deve ser feito com o valor medido na bancada real. A constante de tempo de cerca de "
  "5 minutos também explica por que a sobrecarga real precisa de tempo para aquecer o cabo, e por que a demonstração usa "
  "uma fonte de calor externa.")

H2("3.5 Cenários de diagnóstico")
P("Os sete cenários foram executados três vezes cada, com sementes aleatórias diferentes, o que muda o ruído, a fase do "
  "sinal, o erro do sensor, o offset das sondas e a temperatura ambiente. Foi usada a configuração de demonstração da seção 7 "
  "do VG-PE-05: limite de corrente de 5 A e tempos de confirmação de 10 s. Cada cenário começa com 60 s sem carga.")
desc = {"C1": "2 A sem aquecimento anormal", "C2": "8 A por 25 s, sem resposta térmica",
        "C3": "8 A com ar quente a 70 °C na sonda", "C4": "4 A com aquecimento de mau contato",
        "C5": "sem corrente, sonda a 60 °C", "C6": "sonda de ambiente desconectada por 20 s",
        "C7": "sobrecarga por 90 s e resfriamento"}
esp = {"C1": "NORMAL", "C2": "ALERTA PREVENTIVO", "C3": "SOBRECARGA", "C4": "POSSÍVEL MAU CONTATO",
       "C5": "AQUECIMENTO EXTERNO", "C6": "FALHA DE SENSOR e volta a NORMAL", "C7": "volta a NORMAL"}
ref = {"C1": 60, "C2": 60, "C3": 60, "C4": 60, "C5": 60, "C6": 80, "C7": 150}
linhas = []
for c in R["cenarios"]:
    oks = sum(1 for r in c["rep"] if r["ok"])
    tds = [r["t_det"] - ref[c["id"]] for r in c["rep"]]
    linhas.append([c["id"], desc[c["id"]], esp[c["id"]], f"{oks} de 3 aprovadas",
                   f"{min(tds)} a {max(tds)} s" if c["id"] not in ("C1",) else "não se aplica"])
TAB(["ID", "Estímulo", "Estado esperado", "3 repetições", "Tempo de resposta"], linhas, [11, 48, 45, 26, 30], centro=(0, 3, 4))
P("Todos os cenários foram aprovados nas três repetições. O tempo de resposta é contado a partir do início do estímulo. "
  "Em C6 corresponde à volta ao estado normal depois da reconexão, e em C7 ao retorno ao estado normal depois que a carga "
  "é desligada. Os gráficos de cada cenário estão no Anexo A.")
P("Três comportamentos merecem destaque. No cenário C4 o sistema passa primeiro por ALERTA DE TEMPERATURA e só declara mau "
  "contato depois que a elevação excede o esperado para a corrente por mais de 10 s, sem nunca confundir a situação com "
  "sobrecarga, já que a corrente estava abaixo do limite. No cenário C5 a elevação de 30 °C sem corrente foi corretamente "
  "classificada como aquecimento externo, e não como mau contato. No cenário C7, depois que a carga é desligada, o cabo ainda "
  "quente aparece como AQUECIMENTO EXTERNO por cerca de três minutos, o que é coerente com a lógica, pois o calor restante "
  "não vem mais de corrente circulando, e em seguida o estado volta a NORMAL.")

H2("3.6 Estabilidade perto do limite")
tr = R["estabilidade_trocas"]
P(f"A corrente foi alternada a cada segundo entre 4,8 A e 5,3 A durante dois minutos, em torno do limite de 5 A. O número "
  f"de trocas de estado foi de {tr[0]}, {tr[1]} e {tr[2]} nas três repetições, ou seja, o sistema entrou uma única vez em "
  "ALERTA PREVENTIVO e permaneceu nele. Sem a histerese de 10 %, o estado mudaria a cada segundo.")

H1("4. CONCLUSÃO")
P("A bancada virtual executou todo o roteiro do procedimento VG-PE-05 contra o código real do firmware, e todos os "
  "critérios foram atendidos: erro de corrente abaixo de 5 % entre 2 A e 15 A, faixa linear ampliada para cerca de 24 A, "
  "leitura nula sem carga, identificação da constante térmica com diferença inferior a 3 %, os sete cenários de diagnóstico "
  "corretos nas três repetições e nenhuma oscilação de estado perto do limite.")
P("Recomenda-se iniciar a bancada real com cfg.kTermico = 0,06 e substituí-lo pelo valor obtido no ensaio térmico físico. "
  "Os gráficos deste relatório servem de gabarito: se a curva real do Ensaio 4 ou a sequência de estados de algum cenário "
  "diferir muito das apresentadas aqui, a diferença indica onde o modelo ou o protótipo precisam de ajuste.")

H1("5. COMO REPRODUZIR")
P("Na pasta ensaio/sim do pacote, os comandos abaixo recompilam a bancada, executam todos os ensaios, gravam os dados "
  "em CSV na pasta dados e geram os gráficos na pasta fig. Qualquer parâmetro dos modelos pode ser alterado no arquivo "
  "voltguard_bancada.h para estudar outras condições, como mais ruído ou outro cabo.")
COD("g++ -O2 -std=c++17 -I../../firmware/VoltGuard bancada_pc.cpp -o bancada\n./bancada\npython3 graficos.py")
P("O mesmo roteiro roda dentro do ESP32 ou do Wokwi com o programa VoltGuard_Ensaio.ino, que imprime o resultado de cada "
  "cenário e a linha final RESULTADO GERAL: APROVADO.")

story.append(PageBreak())
H1("ANEXO A. GRÁFICOS DOS CENÁRIOS")
P("Em cada gráfico, o painel superior mostra a corrente medida pelo firmware, o painel do meio mostra a elevação de "
  "temperatura medida pelas sondas e a faixa inferior mostra o estado do diagnóstico ao longo do tempo. Verde indica estado "
  "normal, amarelo indica atenção, vermelho indica condição crítica e cinza indica falha de sensor. A faixa cinza estreita no "
  "início corresponde à primeira leitura do DS18B20, que vale 85 °C e é corretamente rejeitada pelo firmware.")
for i, c in enumerate(R["cenarios"]):
    FIGURA(f"cen_{c['id']}.png", 150, f"Figura A{i + 1}. Cenário {c['id']}: {desc[c['id']]}.")

out = RAIZ + "/ensaio/VoltGuard_Relatorio_Ensaio_Simulado_RevB.pdf"
Doc(out).build(story)
print(out)
