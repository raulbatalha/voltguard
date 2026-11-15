"""Guia de montagem em protoboard VG-MP-07."""
from pathlib import Path as _P
RAIZ = str(_P(__file__).resolve().parents[1])  # raiz do repositorio
import sys, json, importlib.util
sys.path.insert(0, RAIZ + "/ensaio")
import estilo_doc as E
from estilo_doc import P, H1, H2, I, COD, TAB, story, S, Doc
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak, Image, KeepTogether
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER

E.TITULO_CAB = "VOLTGUARD   Guia de Montagem em Protoboard"
E.CODIGO_CAB = "VG-MP-07   Rev. B"
E.TITULO_PDF = "VoltGuard: Guia de Montagem em Protoboard"
S["leg"] = ParagraphStyle("leg", fontName="Serif-I", fontSize=9, leading=11, alignment=TA_CENTER, spaceBefore=2, spaceAfter=6)

spec = importlib.util.spec_from_file_location("pb", RAIZ + "/protoboard/protoboard.py")
pb = importlib.util.module_from_spec(spec); spec.loader.exec_module(pb)
erros = pb.verifica()

story += [Spacer(1, 45 * mm), Paragraph("VOLTGUARD", S["capa1"]), Spacer(1, 4 * mm),
          Paragraph("Sistema de monitoramento e prevenção de sobrecargas<br/>em infraestruturas elétricas", S["capa3"]),
          Spacer(1, 22 * mm), Paragraph("GUIA DE MONTAGEM EM PROTOBOARD", S["capa2"]), Spacer(1, 6 * mm),
          Paragraph("Documento VG-MP-07, Revisão B", S["capa3"]), Spacer(1, 10 * mm),
          Paragraph("Corresponde ao esquema elétrico VG-DE-01 e ao firmware VoltGuard.ino Rev. B.", S["capa3"]), PageBreak()]

H1("1. OBJETIVO")
P("Este guia mostra, furo por furo, como montar o circuito do VoltGuard em protoboard para os ensaios de bancada, antes "
  "da passagem para a placa perfurada. A posição de cada componente e de cada fio foi conferida por um programa que "
  "compara a montagem com o esquema elétrico, como descrito na seção 7.")

H1("2. MATERIAL")
TAB(["Item", "Qtd.", "Observação"], [
    ["Protoboard de 830 pontos", "2", "Uma delas perde o trilho de alimentação de um lado (ver 3.1)"],
    ["Jumpers macho-macho, cores variadas", "30", "Vermelho para 3V3, rosa para 5V, preto para GND"],
    ["ESP32-DevKitC V4 (38 pinos)", "1", "U1"],
    ["Resistores 15 kΩ, 10 kΩ, 4,7 kΩ", "1 de cada", "R1, R2, R3"],
    ["Resistores 1 kΩ", "2", "R4, R8"],
    ["Resistores 330 Ω", "3", "R5, R6, R7"],
    ["Capacitor eletrolítico 10 µF / 16 V", "1", "C1 (tem polaridade)"],
    ["Capacitores cerâmicos 100 nF e 10 nF", "1 de cada", "C2 e C3"],
    ["LEDs 5 mm verde, amarelo e vermelho", "1 de cada", "D1, D2, D3 (perna longa = ânodo)"],
    ["Diodo 1N4148, transistor BC547, buzzer ativo 5 V", "1 de cada", "D4, Q1, BZ1"],
    ["Jaque P2 fêmea com terminais (ou módulo adaptador)", "1", "J1, ligação do SCT-013-030"],
    ["Bornes KF301 de 3 vias (passo 5 mm) ou barra de pinos", "2", "J2 e J3, ligação das sondas DS18B20"],
], [78, 22, 60], centro=(1,))

H1("3. PREPARAÇÃO")
H2("3.1 Por que duas protoboards")
P("O ESP32-DevKitC V4 é mais largo que uma protoboard comum: suas duas fileiras de pinos ficam a 25,4 mm uma da outra e, "
  "numa placa só, o corpo da placa cobriria todos os furos livres de um dos lados. A solução usual é usar duas protoboards "
  "lado a lado, com o ESP32 apoiado sobre a emenda, de modo que cada fileira de pinos fique numa placa e sobrem quatro furos "
  "livres por pino de cada lado.")
I("a)", "Retire o trilho de alimentação da borda inferior da protoboard A e o da borda superior da protoboard B. Na maioria "
        "dos modelos ele se solta puxando a lateral; o fundo adesivo pode ser cortado com estilete.")
I("b)", "Encoste as duas placas de modo que a linha j da placa A e a linha a da placa B fiquem a 25,4 mm uma da outra, com as "
        "colunas numeradas alinhadas. Encaixe o ESP32 sem forçar para confirmar o alinhamento e só então fixe as placas.")
I("c)", "Se as placas não alinharem, use uma placa de expansão para ESP32 de 38 pinos com bornes, ligando cada pino citado "
        "neste guia ao borne de mesmo nome. A lista de ligações da seção 6 continua válida.")
H2("3.2 Notação")
P("Cada furo é indicado pela placa, pela linha e pela coluna. Por exemplo, B-f26 é a placa B, linha f, coluna 26. Os "
  "trilhos são indicados pelo nome e pela coluna mais próxima, por exemplo B_3V3:26. Na placa B, o trilho vermelho é 3V3 e "
  "o azul é GND. Na placa A, o trilho vermelho é 5V e o azul é GND. Os cinco furos de cada coluna, de a até e ou de f até j, "
  "são ligados entre si internamente; os dois lados do canal central não se comunicam.")
P("<b>Atenção:</b> o trilho 3V3 da placa B e o trilho 5V da placa A nunca podem ser interligados. Nenhum pino do ESP32 "
  "suporta 5 V.")

story.append(PageBreak())
from PIL import Image as _PI
_PI.open(RAIZ + "/protoboard/protoboard_voltguard.png").convert("RGB").rotate(90, expand=True).save(RAIZ + "/protoboard/protoboard_rot.png")
img = Image(RAIZ + "/protoboard/protoboard_rot.png", width=136 * mm, height=136 * mm * 2680 / 1640)
story.append(KeepTogether([Paragraph("4. DESENHO DE MONTAGEM", S["h1"]), img,
    Paragraph("Figura 1. Montagem completa vista de cima. Gire a folha 90° no sentido horário: a protoboard A fica em cima "
              "e a B embaixo, com o ESP32 sobre a emenda. Arquivo em alta resolução: protoboard_voltguard.png.", S["leg"])]))
story.append(PageBreak())

H1("5. POSIÇÃO DOS COMPONENTES")
cod_cor = {"15 kΩ": "marrom, verde, laranja", "10 kΩ": "marrom, preto, laranja", "1 kΩ": "marrom, preto, vermelho",
           "4,7 kΩ": "amarelo, violeta, vermelho", "330 Ω": "laranja, laranja, marrom"}
nomes = {"R": "Resistor", "CE": "Capacitor eletrolítico", "CC": "Capacitor cerâmico", "JACK": "Jaque P2", "BORNE": "Borne 3 vias",
         "LED": "LED", "NPN": "Transistor NPN", "BUZ": "Buzzer ativo", "D": "Diodo"}
linhas = []
for nome, (tipo, pinos, rot) in pb.COMP.items():
    pos = ", ".join(f"{p} em {h}" for p, h in pinos.items())
    obs = cod_cor.get(rot, "")
    if tipo == "CE": obs = "perna (+) em B-h30"
    if tipo == "LED": obs = "perna longa (A) à esquerda"
    if tipo == "NPN": obs = "face plana para você: C, B, E"
    if tipo == "D": obs = "faixa (K) do lado do 5 V"
    if tipo == "BUZ": obs = "terminal + à direita"
    desc = nomes[tipo] + ("" if tipo in ("LED", "BORNE", "JACK", "BUZ") else f" {rot}")
    if tipo == "BORNE": desc = rot
    if tipo == "JACK": desc = "Jaque P2 do SCT"
    linhas.append([nome, desc, pos, obs])
TAB(["Ref.", "Componente", "Terminais", "Identificação"], linhas, [13, 40, 62, 45])

H1("6. LISTA DE FIOS")
P("Monte os fios na ordem da tabela. As cores são sugestão, mas manter vermelho para 3V3, rosa para 5V e preto para GND "
  "facilita muito a conferência visual.")
corn = {"red": "vermelho", "black": "preto", "#c2185b": "rosa", "#8e44ad": "violeta", "#2a78d6": "azul",
        "#1baf7a": "verde-água", "#0ca30c": "verde", "#eda100": "amarelo", "#e34948": "vermelho claro",
        "#eb6834": "laranja", "#7f8c8d": "cinza"}
TAB(["Nº", "De", "Para", "Cor", "Função"],
    [[str(i + 1), a, b, corn.get(c, c), f] for i, (a, b, c, f) in enumerate(pb.FIOS)], [10, 22, 24, 24, 80], centro=(0,))

H1("7. SEQUÊNCIA DE MONTAGEM COM VERIFICAÇÕES")
P("Monte sempre com o cabo USB desligado. Ao fim de cada etapa, ligue o USB, faça a verificação indicada e desligue "
  "antes de continuar. Assim um erro aparece logo, e não no fim, quando é mais difícil achar a causa.")
etapas = [
    ["1", "ESP32 e alimentação: U1 e fios 1 a 4", "Multímetro: 3,3 V entre trilhos B_3V3 e B_GND; 5 V entre A_5V e A_GND"],
    ["2", "Divisor de referência: R1, R2, C1, C2 e fios 5 e 6", "Tensão na coluna 30 da placa B: 1,32 V ± 0,08 V"],
    ["3", "Entrada do SCT: J1, R4, C3 e fios 7 a 9", "Sem o SCT: firmware indica 0,00 A. Com SCT e carga: leitura coerente com o alicate"],
    ["4", "Temperatura: R3, J2, J3 e fios 10 a 16", "Monitor serial: DS18B20 encontrados: 2"],
    ["5", "LEDs: R5 a R7, D1 a D3 e fios 17 a 22", "LED verde aceso em estado NORMAL"],
    ["6", "Alarme: R8, Q1, D4, BZ1 e fios 23 a 27", "Buzzer soa em SOBRECARGA (cenário C3 do VG-PE-05)"],
]
TAB(["Etapa", "O que montar", "Verificação antes de seguir"], etapas, [14, 66, 80], centro=(0,))

H1("8. CONFERÊNCIA AUTOMÁTICA DA MONTAGEM")
P("A montagem deste guia está descrita no arquivo protoboard.py como dados: a posição de cada terminal e de cada fio. O "
  "programa reconstrói as ligações internas das protoboards, junta os furos ligados pelos fios e compara o resultado com as "
  f"{len(pb.NETS)} redes do esquema VG-DE-01. Ele aponta três tipos de erro: uma rede partida (algum ponto ficou sem ligação), "
  "um curto entre redes diferentes e dois terminais no mesmo furo.")
P(f"<b>Resultado para a montagem deste guia:</b> {'nenhum erro encontrado' if not erros else '; '.join(erros)}. "
  f"Foram conferidos {len(pb.COMP)} componentes, o ESP32 e {len(pb.FIOS)} fios.")
P("Para demonstrar que a conferência funciona, dois erros foram introduzidos de propósito. Com o terminal de C3 deslocado "
  "uma coluna, o programa acusou que a rede GND ficou partida. Com um fio ligando as colunas 30 e 34 da placa B, acusou "
  "curto entre as redes GND e VREF e o furo usado duas vezes. Se vocês mudarem a posição de algum componente, basta editar "
  "o arquivo e executar novamente:")
COD("python3 protoboard.py")

H1("9. CUIDADOS")
I("9.1", "C1 é polarizado: a perna mais longa (+) vai em B-h30, que é a referência, e a faixa (−) vai na coluna 34, que é GND.")
I("9.2", "Nos LEDs, a perna longa (ânodo) fica do lado do resistor. No diodo D4, a faixa (cátodo) fica do lado do 5 V.")
I("9.3", "BC547 com a face plana voltada para você: da esquerda para a direita, coletor, base e emissor. Outros transistores "
         "podem ter pinagem diferente; confira na folha de dados do componente comprado.")
I("9.4", "O SCT só é conectado ao jaque J1 depois da etapa 2 aprovada. O sensor nunca deve ser ligado diretamente ao ESP32 "
         "sem o divisor, porque a saída é alternada e fica negativa em metade do ciclo.")
I("9.5", "A protoboard é apenas para ensaio. Para uso prolongado ou demonstração final, transfira o circuito para a placa "
         "perfurada conforme o arranjo da folha VG-MO-04.")

out = RAIZ + "/protoboard/VoltGuard_Montagem_Protoboard_RevB.pdf"
Doc(out).build(story)
print(out, "erros:", erros)
