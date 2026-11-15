"""Procedimento de Ensaio e Demonstracao VoltGuard (VG-PE-05 Rev. B)."""
from pathlib import Path as _P
RAIZ = str(_P(__file__).resolve().parents[1])  # raiz do repositorio
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table,
                                TableStyle, KeepTogether, PageBreak)

F = "/usr/share/fonts/truetype/liberation/"
for n, f in [("Serif", "LiberationSerif-Regular"), ("Serif-B", "LiberationSerif-Bold"),
             ("Serif-I", "LiberationSerif-Italic"), ("Sans", "LiberationSans-Regular"),
             ("Sans-B", "LiberationSans-Bold")]:
    pdfmetrics.registerFont(TTFont(n, F + f + ".ttf"))
from reportlab.lib.fonts import addMapping
addMapping("Serif", 0, 0, "Serif"); addMapping("Serif", 1, 0, "Serif-B"); addMapping("Serif", 0, 1, "Serif-I")

S = {
    "corpo": ParagraphStyle("corpo", fontName="Serif", fontSize=10.5, leading=14.2, alignment=TA_JUSTIFY, spaceAfter=5),
    "item": ParagraphStyle("item", fontName="Serif", fontSize=10.5, leading=14.2, alignment=TA_JUSTIFY,
                           leftIndent=9 * mm, firstLineIndent=-6 * mm, spaceAfter=3),
    "h1": ParagraphStyle("h1", fontName="Sans-B", fontSize=12, leading=15, spaceBefore=10, spaceAfter=5, keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName="Sans-B", fontSize=10.5, leading=13.5, spaceBefore=7, spaceAfter=3, keepWithNext=1),
    "tab": ParagraphStyle("tab", fontName="Serif", fontSize=9, leading=11),
    "tabc": ParagraphStyle("tabc", fontName="Serif", fontSize=9, leading=11, alignment=TA_CENTER),
    "tabh": ParagraphStyle("tabh", fontName="Sans-B", fontSize=8.5, leading=10.5),
    "cod": ParagraphStyle("cod", fontName="Courier", fontSize=9, leading=11.5, leftIndent=9 * mm,
                          backColor=colors.HexColor("#f2f2f2"), borderPadding=(3, 4, 3, 4), spaceBefore=3, spaceAfter=7),
    "capa1": ParagraphStyle("c1", fontName="Sans-B", fontSize=22, leading=27, alignment=TA_CENTER),
    "capa2": ParagraphStyle("c2", fontName="Sans-B", fontSize=14, leading=18, alignment=TA_CENTER),
    "capa3": ParagraphStyle("c3", fontName="Serif", fontSize=11, leading=15, alignment=TA_CENTER),
}

story = []
P = lambda t, s="corpo": story.append(Paragraph(t, S[s]))
H1 = lambda t: story.append(Paragraph(t, S["h1"]))
H2 = lambda t: story.append(Paragraph(t, S["h2"]))
I = lambda n, t: story.append(Paragraph(f"{n}&nbsp;&nbsp;{t}", S["item"]))
COD = lambda t: story.append(Paragraph(t.replace("\n", "<br/>").replace(" ", "&nbsp;"), S["cod"]))


def TAB(cab, linhas, larg, altura=None, centro=()):
    dados = [[Paragraph(c, S["tabh"]) for c in cab]]
    for l in linhas:
        dados.append([Paragraph(str(c), S["tabc"] if j in centro else S["tab"]) for j, c in enumerate(l)])
    t = Table(dados, colWidths=[w * mm for w in larg], rowHeights=None if altura is None else [None] + [altura * mm] * len(linhas),
              repeatRows=1)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e3e3e3")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    story.append(t)
    story.append(Spacer(1, 5))


def ESPACO(h=4): story.append(Spacer(1, h))


# ================================ CAPA ================================
story += [Spacer(1, 45 * mm),
          Paragraph("VOLTGUARD", S["capa1"]), Spacer(1, 4 * mm),
          Paragraph("Sistema de monitoramento e prevenção de sobrecargas<br/>em infraestruturas elétricas", S["capa3"]),
          Spacer(1, 22 * mm),
          Paragraph("PROCEDIMENTO DE ENSAIO E DEMONSTRAÇÃO<br/>DO PROTÓTIPO", S["capa2"]),
          Spacer(1, 6 * mm),
          Paragraph("Documento VG-PE-05, Revisão B", S["capa3"]),
          Spacer(1, 40 * mm)]
capa = Table([[Paragraph("Responsável pelo ensaio:", S["tab"]), ""],
              [Paragraph("Local:", S["tab"]), ""],
              [Paragraph("Data de execução:", S["tab"]), ""],
              [Paragraph("Versão do firmware:", S["tab"]), Paragraph("VoltGuard.ino Rev. B", S["tab"])],
              [Paragraph("Emissão do documento:", S["tab"]), Paragraph("14/11/2026", S["tab"])]],
             colWidths=[48 * mm, 92 * mm], rowHeights=[9 * mm] * 5)
capa.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.black), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
story += [capa, PageBreak()]

# ================================ 1 OBJETIVO ================================
H1("1. OBJETIVO")
P("Este procedimento estabelece a forma de verificar, em laboratório, se o protótipo VoltGuard mede corrente e "
  "temperatura com exatidão aceitável e se identifica corretamente cada uma das condições de diagnóstico previstas "
  "no firmware. Também orienta a demonstração do funcionamento perante banca avaliadora, de modo que cada resultado "
  "apresentado possa ser conferido por quem assiste.")
P("Os ensaios estão organizados em três etapas. A primeira dispensa qualquer componente físico e pode ser executada "
  "em computador. A segunda trata da medição em bancada. A terceira reproduz, sob comando do operador, as situações "
  "de diagnóstico e o envio de alertas.")

H1("2. DOCUMENTOS DE REFERÊNCIA")
TAB(["Documento", "Conteúdo"], [
    ["VG-DE-01", "Esquema elétrico e lista de materiais"],
    ["VG-DM-02 e VG-DM-03", "Caixa: base e tampa"],
    ["VG-MO-04", "Conjunto montado, arranjo da placa e sequência de montagem"],
    ["VoltGuard.ino Rev. B", "Firmware do protótipo (pasta firmware/VoltGuard)"],
    ["LEIA-ME.md", "Instruções de simulação, gravação e impressão"],
], [45, 115])

H1("3. MATERIAIS E INSTRUMENTOS")
P("Antes de iniciar, confira se os itens abaixo estão disponíveis. Os instrumentos de referência precisam ter "
  "resolução melhor que a grandeza que se deseja verificar, pois é contra eles que o VoltGuard será comparado.")
TAB(["Item", "Qtd.", "Finalidade"], [
    ["Protótipo VoltGuard montado, com as duas sondas DS18B20 e o sensor SCT-013-030", "1", "Objeto do ensaio"],
    ["Computador com Arduino IDE e cabo USB de dados", "1", "Gravação e leitura do monitor serial"],
    ["Multímetro digital", "1", "Medição da tensão de referência"],
    ["Alicate amperímetro com medição true RMS", "1", "Referência de corrente"],
    ["Termômetro digital de referência", "1", "Referência de temperatura"],
    ["Extensão com separador de linha (fase e neutro acessíveis em separado)", "1", "Passagem de um único condutor pelo SCT"],
    ["Tomada protegida por dispositivo DR", "1", "Segurança do ensaio"],
    ["Cargas resistivas: secador de cabelo (1000 W ou mais), chaleira ou ferro de passar, lâmpada incandescente ou halógena", "1 de cada", "Correntes de ensaio"],
    ["Dois copos, água à temperatura ambiente e água quente (cerca de 60 °C)", "1 conjunto", "Ensaios de temperatura"],
    ["Celular com acesso à internet", "1", "Recepção dos alertas remotos"],
    ["Cronômetro (pode ser o do celular)", "1", "Tempo de resposta"],
], [100, 20, 40], centro=(1,))

# ================================ 4 SEGURANCA ================================
H1("4. CONDIÇÕES DE SEGURANÇA")
P("O VoltGuard não tem nenhuma ligação elétrica com a rede. O sensor de corrente apenas envolve o condutor isolado e "
  "as sondas de temperatura encostam na isolação do cabo. Ainda assim, os ensaios envolvem cargas ligadas em 127 V ou "
  "220 V, e por isso as regras a seguir são obrigatórias.")
I("4.1", "Todo ensaio com carga energizada deve ser acompanhado por pessoa responsável pelo laboratório.")
I("4.2", "As cargas são ligadas exclusivamente por meio da extensão com separador de linha, conectada a tomada protegida por DR. "
         "Em nenhuma hipótese a capa de um cabo deve ser aberta para separar fase e neutro.")
I("4.3", "O sensor SCT envolve um único condutor. Se envolver fase e neutro juntos, os campos se anulam e a leitura fica próxima de zero.")
I("4.4", "A condição de mau contato é sempre emulada por aquecimento externo da sonda. Provocar um mau contato real num borne "
         "energizado é risco de incêndio e não faz parte deste procedimento.")
I("4.5", "Água quente deve ser manuseada em recipiente estável, longe do protótipo e das tomadas.")
I("4.6", "Qualquer cheiro de queimado, aquecimento anormal ou ruído na extensão encerra o ensaio imediatamente.")

# ================================ 5 ETAPA A ================================
H1("5. ETAPA A: VERIFICAÇÃO SEM HARDWARE")
H2("5.1 Testes automáticos do firmware")
P("O núcleo de cálculo e diagnóstico do firmware foi escrito de modo a compilar também no computador. Isso permite "
  "verificar a lógica antes de existir a placa. Na pasta <i>firmware/test</i>, execute:")
COD("g++ -std=c++17 -I../VoltGuard test_core.cpp -o teste\n./teste")
P("O programa executa 25 verificações: cálculo da corrente eficaz em várias intensidades, rejeição do ruído sem carga, "
  "detecção de sinal fora da faixa do conversor, tratamento das leituras inválidas do DS18B20, cálculo da taxa de "
  "elevação de temperatura e a resposta do diagnóstico em cada cenário. <b>Critério de aprovação:</b> a última linha "
  "deve indicar 25/25 verificações aprovadas.")

H2("5.2 Circuito de condicionamento no Falstad")
P("Abra no navegador o endereço contido no arquivo <i>wokwi/falstad_link.txt</i>. O simulador mostra o divisor de "
  "referência, o sensor representado por uma fonte senoidal de 60 Hz e a entrada GPIO34 do ESP32. Clique com o "
  "botão direito sobre o voltímetro e escolha a opção de ver no osciloscópio.")
P("Com a fonte ajustada em 1,414 V de pico, valor que corresponde a 30 A no sensor, observe que o sinal oscila em "
  "torno de 1,32 V. Em seguida, altere o resistor R1 de 15 kΩ para 10 kΩ, que era o valor do documento original, e "
  "repita a observação. A referência sobe para 1,65 V e o pico ultrapassa 3 V, acima do limite de 2,45 V em que o "
  "conversor do ESP32 é confiável. Essa comparação demonstra a correção feita no circuito.")
TAB(["Configuração", "Referência medida (V)", "Pico máximo (V)", "Pico mínimo (V)", "Dentro de 0,15 a 2,45 V?"],
    [["R1 = 15 kΩ (Rev. B)", "", "", "", ""], ["R1 = 10 kΩ (versão 4)", "", "", "", ""]],
    [38, 32, 27, 27, 36], altura=8)

H2("5.3 Sistema completo no Wokwi")
P("Monte o projeto no Wokwi seguindo o item 3 do LEIA-ME. No simulador, o potenciômetro define a corrente de 0 a 15 A "
  "e cada sonda de temperatura pode ser ajustada com um clique. O firmware gera internamente a senoide que o sensor "
  "entregaria e aplica o mesmo cálculo usado no protótipo real. Reproduza os cenários da seção 7 e anote o estado "
  "exibido no monitor serial. Recomenda-se gravar a tela durante essa simulação, pois o vídeo serve como reserva caso "
  "o hardware apresente problema no dia da apresentação.")

# ================================ 6 ETAPA B ================================
H1("6. ETAPA B: ENSAIOS EM BANCADA")
P("Os ensaios devem ser feitos na ordem apresentada. Um ensaio só começa depois que o anterior foi aprovado, porque "
  "cada um depende do funcionamento verificado no passo anterior.")

H2("6.1 Ensaio 1: gravação e comunicação")
P("Grave o firmware com a placa configurada como ESP32 Dev Module e abra o monitor serial em 115200 baud. "
  "<b>Critério de aprovação:</b> aparecem as mensagens \"VoltGuard Rev. B\" e \"DS18B20 encontrados: 2\", seguidas dos "
  "endereços das duas sondas e de uma linha de medição por segundo.")

H2("6.2 Ensaio 2: medição de temperatura")
P("Coloque as duas sondas e o termômetro de referência no mesmo copo com água à temperatura ambiente e aguarde dois "
  "minutos. Anote as três leituras. Repita com água quente. Depois segure apenas a sonda do ponto monitorado na mão e "
  "confirme que é ela, e não a de ambiente, que sobe. Se estiverem trocadas, inverta as sondas nos bornes J2 e J3.")
TAB(["Condição", "Referência (°C)", "T ponto (°C)", "T ambiente (°C)", "Maior diferença (°C)"],
    [["Água ambiente", "", "", "", ""], ["Água quente", "", "", "", ""]], [36, 31, 31, 31, 31], altura=8)
P("<b>Critério de aprovação:</b> diferença de no máximo 0,5 °C entre cada sonda e a referência.")

H2("6.3 Ensaio 3: tensão de referência")
P("Com o protótipo alimentado pela USB e sem o sensor de corrente conectado, meça com o multímetro a tensão entre o "
  "ponto comum de R1 e R2 e o GND. <b>Critério de aprovação:</b> 1,32 V com tolerância de 0,08 V.")
TAB(["Grandeza", "Valor medido", "Aprovado?"], [["Tensão de referência (V)", "", ""]], [70, 50, 40], altura=8)

H2("6.4 Ensaio 4: ruído sem carga")
P("Conecte o sensor ao jaque P2 e instale-o na extensão, sem nenhuma carga ligada. Para enxergar o ruído real, "
  "acrescente temporariamente no início da função setup() a linha abaixo, grave e observe por um minuto:")
COD("cfg.pisoRuidoA = 0.0f;")
P("Anote o maior valor de corrente exibido. Esse é o ruído do conjunto. Depois remova a linha ou ajuste o piso para um "
  "valor um pouco acima do ruído encontrado. <b>Critério de aprovação:</b> ruído inferior a 0,3 A com uma volta do "
  "condutor e, com o piso ajustado, leitura de 0,00 A sem carga.")
TAB(["Grandeza", "Valor", "Observação"], [["Maior leitura sem carga (A)", "", ""], ["Piso adotado (A)", "", ""]],
    [70, 40, 50], altura=8)

H2("6.5 Ensaio 5: calibração e exatidão da corrente")
P("Ligue as cargas uma de cada vez na extensão. Para cada uma, aguarde dez segundos e anote ao mesmo tempo a leitura "
  "do alicate, colocado no mesmo condutor, e a do VoltGuard. O erro percentual é a diferença entre as duas leituras "
  "dividida pela leitura do alicate, multiplicada por cem.")
P("Se o erro for sistemático, isto é, sempre para o mesmo lado, corrija a constante de calibração com a regra abaixo "
  "e repita a tabela inteira. O valor atual está em cfg.calibracao, que vale 1,000 na primeira vez.")
COD("nova = atual x (I alicate / I VoltGuard)")
P("Para correntes abaixo de 3 A, como a da lâmpada, passe o condutor cinco vezes pelo núcleo do sensor e informe esse "
  "número no firmware com a linha cfg.nEspiras = 5;. O alicate continua medindo uma única passagem.")
TAB(["Carga", "Espiras", "Alicate (A)", "VoltGuard (A)", "Erro (%)", "Aprovado?"],
    [["Lâmpada", "5", "", "", "", ""], ["Chaleira ou ferro", "1", "", "", "", ""], ["Secador, potência mínima", "1", "", "", "", ""],
     ["Secador, potência máxima", "1", "", "", "", ""]], [42, 18, 25, 25, 22, 28], altura=8, centro=(1,))
P("<b>Critério de aprovação:</b> erro de no máximo 5 % em todas as cargas, entre 2 A e 15 A.")

H2("6.6 Ensaio 6: falha de sensor")
P("Com o sistema em funcionamento normal, solte o fio de dados da sonda de ambiente no borne J3. Depois, recoloque. "
  "<b>Critério de aprovação:</b> o estado passa para FALHA DE SENSOR com o LED amarelo piscando e, ao reconectar, "
  "volta ao estado NORMAL.")

# ================================ 7 ETAPA C ================================
H1("7. ETAPA C: ENSAIOS DE DIAGNÓSTICO")
P("Os tempos de confirmação definidos no firmware são adequados à operação real, mas longos para uma demonstração. "
  "Para os ensaios desta etapa, acrescente no início da função setup() as linhas abaixo. Ao apresentar, informe à banca "
  "que os tempos foram reduzidos para fins de demonstração.")
COD("cfg.iLimiteA = 5.0f;\ncfg.tConfirmaSobrecargaMs = 10000;\ncfg.tConfirmaMauContatoMs = 10000;\ncfg.tLiberaMs = 5000;")
P("Cada cenário deve ser repetido três vezes. Entre uma repetição e outra, retire o estímulo e espere o sistema "
  "voltar ao estado NORMAL. Anote o estado observado no monitor serial e nos LEDs.")
TAB(["Cenário", "Como provocar", "Estado esperado", "1ª", "2ª", "3ª"], [
    ["C1 Normal", "Lâmpada ligada, sondas no ar ambiente", "NORMAL, LED verde", "", "", ""],
    ["C2 Corrente alta", "Secador ligado na potência máxima, ar dirigido para longe das sondas", "ALERTA PREVENTIVO, LED amarelo", "", "", ""],
    ["C3 Sobrecarga", "Secador ligado e o ar quente dirigido para a sonda do ponto", "SOBRECARGA, LED vermelho e buzzer", "", "", ""],
    ["C4 Mau contato (emulado)", "Lâmpada com 5 espiras ou chaleira ligada e sonda do ponto em água a cerca de 45 °C", "ALERTA DE TEMPERATURA e depois POSSÍVEL MAU CONTATO", "", "", ""],
    ["C5 Aquecimento externo", "Nenhuma carga ligada e sonda do ponto em água a cerca de 60 °C", "AQUECIMENTO EXTERNO, LED amarelo", "", "", ""],
    ["C6 Falha de sensor", "Soltar o fio de dados de uma sonda", "FALHA DE SENSOR, amarelo piscando", "", "", ""],
], [30, 55, 42, 11, 11, 11], centro=(3, 4, 5))
P("O cenário C5 tem importância especial. Ele mostra que o sistema não confunde calor vindo de fora com defeito no "
  "circuito, porque um mau contato só aquece quando há corrente passando por ele. Essa foi uma das correções feitas "
  "em relação à versão anterior da lógica.")
P("<b>Critério de aprovação:</b> estado correto nas três repetições de cada cenário e nenhuma alternância de estado "
  "enquanto o estímulo é mantido.")

# ================================ 8 REMOTO ================================
H1("8. ENSAIO DE COMUNICAÇÃO REMOTA")
P("No VoltGuard.ino, ajuste USAR_MQTT para 1 e preencha o nome e a senha da rede Wi-Fi do laboratório. Ao ligar, o "
  "monitor serial informa os tópicos de publicação. No celular, abra um cliente MQTT, por exemplo o HiveMQ Web Client, "
  "conecte ao servidor broker.hivemq.com e assine o tópico voltguard/#.")
P("Provoque o cenário C3 e dispare o cronômetro no instante em que o LED vermelho acender. Pare quando a mensagem de "
  "alerta chegar ao celular.")
TAB(["Repetição", "Tempo até o alerta (s)", "Mensagem recebida corretamente?"],
    [["1", "", ""], ["2", "", ""], ["3", "", ""]], [30, 60, 70], altura=8, centro=(0,))
P("<b>Critério de aprovação:</b> mensagem recebida nas três repetições, em menos de 10 segundos.")

# ================================ 9 ROTEIRO ================================
H1("9. ROTEIRO DA DEMONSTRAÇÃO PARA A BANCA")
P("A demonstração completa cabe em cerca de dez minutos. A ordem proposta parte do que é mais seguro e previsível "
  "para o que depende do hardware, de modo que, se algo falhar no final, a maior parte do funcionamento já terá sido mostrada.")
TAB(["Tempo", "Atividade", "O que a banca deve perceber"], [
    ["2 min", "Falstad com R1 de 15 kΩ e depois de 10 kΩ; Wokwi com um cenário", "A correção do circuito e a lógica funcionando"],
    ["3 min", "Secador ligado, leitura do VoltGuard ao lado da leitura do alicate", "A medição confere com instrumento de referência"],
    ["4 min", "Cenários C2, C3, C4 e C5 em sequência", "Cada causa provável é identificada corretamente"],
    ["1 min", "Alerta chegando no celular", "O monitoramento remoto funciona"],
], [18, 82, 60])
P("Leve impressas as tabelas deste procedimento já preenchidas nos ensaios de preparação, e uma cópia em branco da "
  "tabela da seção 7 para preencher na frente da banca. Grave em vídeo todos os ensaios de preparação e salve o texto "
  "do monitor serial (selecionar tudo, copiar e colar num arquivo de texto). Esses registros são a evidência caso "
  "algum componente falhe no dia.")

# ================================ 10 CRITERIOS ================================
H1("10. QUADRO DE ACEITAÇÃO")
TAB(["Requisito", "Critério", "Resultado", "Situação"], [
    ["Lógica do firmware", "25/25 verificações", "", ""],
    ["Faixa do conversor", "Sinal entre 0,15 e 2,45 V a 30 A", "", ""],
    ["Medição de temperatura", "Diferença ≤ 0,5 °C", "", ""],
    ["Tensão de referência", "1,32 V ± 0,08 V", "", ""],
    ["Medição de corrente", "Erro ≤ 5 % entre 2 e 15 A", "", ""],
    ["Diagnóstico", "6 cenários corretos em 3 repetições", "", ""],
    ["Estabilidade", "Nenhuma alternância indevida de estado", "", ""],
    ["Falha de sensor", "Detectada e sinalizada", "", ""],
    ["Alerta remoto", "Recebido em menos de 10 s", "", ""],
], [42, 58, 35, 25], altura=8)
ESPACO(6)
P("O protótipo é considerado aprovado quando todos os requisitos do quadro acima forem atendidos. Requisitos não "
  "atendidos devem ser descritos no campo de observações, com a causa provável e a ação corretiva prevista.")
story.append(KeepTogether([
    Paragraph("Observações:", S["h2"]),
    Table([[""]] * 4, colWidths=[160 * mm], rowHeights=[8 * mm] * 4,
          style=TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.black)])),
    Spacer(1, 14 * mm),
    Table([["_______________________________", "_______________________________"],
           ["Executado por", "Verificado por"]], colWidths=[80 * mm, 80 * mm],
          style=TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("FONTNAME", (0, 0), (-1, -1), "Serif"),
                            ("FONTSIZE", (0, 0), (-1, -1), 10)])),
]))


# ================================ PAGINACAO ================================
class Doc(BaseDocTemplate):
    def __init__(self, fn):
        super().__init__(fn, pagesize=A4, leftMargin=25 * mm, rightMargin=20 * mm, topMargin=25 * mm, bottomMargin=22 * mm,
                         title="VoltGuard: Procedimento de Ensaio e Demonstração", author="Projeto VoltGuard")
        fr = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="f")
        self.addPageTemplates([PageTemplate(id="p", frames=[fr], onPage=self.moldura)])

    def moldura(self, c, d):
        if d.page == 1: return
        c.saveState()
        c.setFont("Sans", 8)
        W, H = A4
        c.line(25 * mm, H - 18 * mm, W - 20 * mm, H - 18 * mm)
        c.drawString(25 * mm, H - 16 * mm, "VOLTGUARD   Procedimento de Ensaio e Demonstração")
        c.drawRightString(W - 20 * mm, H - 16 * mm, "VG-PE-05   Rev. B")
        c.line(25 * mm, 15 * mm, W - 20 * mm, 15 * mm)
        c.drawRightString(W - 20 * mm, 11 * mm, f"Página {d.page}")
        c.restoreState()


out = RAIZ + "/ensaio/VoltGuard_Procedimento_de_Ensaio_RevB.pdf"
Doc(out).build(story)
print(out)
