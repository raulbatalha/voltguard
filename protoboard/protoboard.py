"""Montagem do VoltGuard em duas protoboards de 830 pontos: desenho, lista de fios e
conferencia automatica da ligacao contra o esquema VG-DE-01."""
from pathlib import Path as _P
RAIZ = str(_P(__file__).resolve().parents[1])  # raiz do repositorio
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch, Polygon
from matplotlib.path import Path
from matplotlib.patches import PathPatch

U = 2.54  # passo em mm
NCOL = 63
# ---------------------------- geometria (em passos) ----------------------------
Y = {}
for r, y in zip("jihgf", [3, 4, 5, 6, 7]): Y[("B", r)] = y
for r, y in zip("edcba", [10, 11, 12, 13, 14]): Y[("B", r)] = y
for r, y in zip("jihgf", [24, 25, 26, 27, 28]): Y[("A", r)] = y
for r, y in zip("edcba", [31, 32, 33, 34, 35]): Y[("A", r)] = y
RAIL = {"B_GND": 0, "B_3V3": 1, "A_GND": 37, "A_5V": 38}
RAIL_COR = {"B_GND": "#2a63c9", "B_3V3": "#d03b3b", "A_GND": "#2a63c9", "A_5V": "#d03b3b"}
RAIL_TXT = {"B_GND": "GND", "B_3V3": "3V3", "A_GND": "GND", "A_5V": "5V"}


def furo(ref):
    """'B-f26' -> (x, y) em passos; 'B_3V3:26' -> trilho."""
    if ":" in ref:
        rail, c = ref.split(":"); return (int(c), RAIL[rail])
    pl, rest = ref.split("-"); r, c = rest[0], int(rest[1:])
    return (c, Y[(pl, r)])


def no(ref):
    """identificador eletrico do furo (tira de 5 furos ou trilho)."""
    if ":" in ref: return ref.split(":")[0]
    pl, rest = ref.split("-"); r, c = rest[0], int(rest[1:])
    meia = "sup" if r in "abcde" else "inf"
    return f"{pl}{meia}{c}"


# ---------------------------- ESP32-DevKitC V4 ----------------------------
TOPO = ["GND", "23", "22", "TX", "RX", "21", "GND", "19", "18", "5", "17", "16", "4", "0", "2", "15", "D1", "D0", "CLK"]
BASE = ["3V3", "EN", "VP", "VN", "34", "35", "32", "33", "25", "26", "27", "14", "12", "GND", "13", "D2", "D3", "CMD", "5V"]
ESP = {}
for i, p in enumerate(TOPO): ESP.setdefault("ESP." + p, []).append(f"A-j{3 + i}")
for i, p in enumerate(BASE): ESP.setdefault("ESP." + p, []).append(f"B-a{3 + i}")

# ---------------------------- componentes ----------------------------
# nome: (tipo, {pino: furo}, rotulo)
COMP = {
    "R1": ("R", {"1": "B-f26", "2": "B-f30"}, "15 kΩ"),
    "R2": ("R", {"1": "B-g30", "2": "B-g34"}, "10 kΩ"),
    "C1": ("CE", {"+": "B-h30", "-": "B-h34"}, "10 µF"),
    "C2": ("CC", {"1": "B-i30", "2": "B-i34"}, "100 nF"),
    "J1": ("JACK", {"S": "B-f37", "R": "B-f38", "T": "B-f39"}, "J1 P2 (SCT)"),
    "R4": ("R", {"1": "B-g39", "2": "B-g43"}, "1 kΩ"),
    "C3": ("CC", {"1": "B-h43", "2": "B-h46"}, "10 nF"),
    "R3": ("R", {"1": "B-i47", "2": "B-i51"}, "4,7 kΩ"),
    "J2": ("BORNE", {"VDD": "B-f50", "DQ": "B-f51", "GND": "B-f52"}, "J2 T-PONTO"),
    "J3": ("BORNE", {"VDD": "B-f55", "DQ": "B-f56", "GND": "B-f57"}, "J3 T-AMB"),
    "R5": ("R", {"1": "A-c26", "2": "A-c30"}, "330 Ω"),
    "D1": ("LED", {"A": "A-d30", "K": "A-d31"}, "#0ca30c"),
    "R6": ("R", {"1": "A-c33", "2": "A-c37"}, "330 Ω"),
    "D2": ("LED", {"A": "A-d37", "K": "A-d38"}, "#eda100"),
    "R7": ("R", {"1": "A-c40", "2": "A-c44"}, "330 Ω"),
    "D3": ("LED", {"A": "A-d44", "K": "A-d45"}, "#e34948"),
    "R8": ("R", {"1": "A-c48", "2": "A-c52"}, "1 kΩ"),
    "Q1": ("NPN", {"C": "A-e51", "B": "A-e52", "E": "A-e53"}, "BC547"),
    "BZ1": ("BUZ", {"-": "A-b58", "+": "A-b61"}, "BZ1"),
    "D4": ("D", {"A": "A-c51", "K": "A-c56"}, "1N4148"),
}

# ---------------------------- fios (jumpers) ----------------------------
# (de, para, cor, funcao)
FIOS = [
    ("B-e3", "B_3V3:3", "red", "3V3 do ESP32 para o trilho 3V3"),
    ("B-e16", "B_GND:16", "black", "GND do ESP32 para o trilho GND inferior"),
    ("A-f3", "A_GND:3", "black", "GND do ESP32 para o trilho GND superior"),
    ("B-e21", "A_5V:24", "#c2185b", "5V do ESP32 para o trilho 5V"),
    ("B-j26", "B_3V3:26", "red", "3V3 para R1"),
    ("B-j34", "B_GND:34", "black", "GND para R2, C1 e C2"),
    ("B-j30", "B-j37", "#8e44ad", "VREF para o corpo (S) do jaque"),
    ("B-j46", "B_GND:46", "black", "GND para C3"),
    ("B-i43", "B-c7", "#2a78d6", "Sinal do SCT para o GPIO34"),
    ("B-j47", "B_3V3:47", "red", "3V3 para R3 (pull-up)"),
    ("B-j50", "B_3V3:50", "red", "3V3 para J2 VDD"),
    ("B-j52", "B_GND:52", "black", "GND para J2"),
    ("B-j55", "B_3V3:55", "red", "3V3 para J3 VDD"),
    ("B-j57", "B_GND:57", "black", "GND para J3"),
    ("B-h51", "B-h56", "#1baf7a", "Barramento 1-Wire entre J2 e J3"),
    ("A-g15", "B-g51", "#1baf7a", "GPIO4 para o barramento 1-Wire"),
    ("B-c11", "A-e26", "#0ca30c", "GPIO25 para R5 (LED verde)"),
    ("B-d12", "A-e33", "#eda100", "GPIO26 para R6 (LED amarelo)"),
    ("B-e13", "A-e40", "#e34948", "GPIO27 para R7 (LED vermelho)"),
    ("A-a31", "A_GND:31", "black", "Catodo D1 para GND"),
    ("A-a38", "A_GND:38", "black", "Catodo D2 para GND"),
    ("A-a45", "A_GND:45", "black", "Catodo D3 para GND"),
    ("B-b17", "A-e48", "#eb6834", "GPIO13 para R8 (base do Q1)"),
    ("A-a53", "A_GND:53", "black", "Emissor do Q1 para GND"),
    ("A-a56", "A_5V:56", "#c2185b", "Catodo do D4 para 5V"),
    ("A-d51", "A-d58", "#7f8c8d", "Coletor do Q1 para o buzzer (-)"),
    ("A-a61", "A_5V:61", "#c2185b", "Buzzer (+) para 5V"),
]

# ---------------------------- netlist esperada (VG-DE-01) ----------------------------
NETS = {
    "3V3": ["ESP.3V3", "R1.1", "R3.1", "J2.VDD", "J3.VDD"],
    "GND": ["ESP.GND", "R2.2", "C1.-", "C2.2", "C3.2", "J2.GND", "J3.GND", "D1.K", "D2.K", "D3.K", "Q1.E"],
    "VREF": ["R1.2", "R2.1", "C1.+", "C2.1", "J1.S"],
    "TIP": ["J1.T", "R4.1"],
    "ADC34": ["R4.2", "C3.1", "ESP.34"],
    "ONEWIRE": ["R3.2", "J2.DQ", "J3.DQ", "ESP.4"],
    "G25": ["ESP.25", "R5.1"], "LED1": ["R5.2", "D1.A"],
    "G26": ["ESP.26", "R6.1"], "LED2": ["R6.2", "D2.A"],
    "G27": ["ESP.27", "R7.1"], "LED3": ["R7.2", "D3.A"],
    "G13": ["ESP.13", "R8.1"], "BASE": ["R8.2", "Q1.B"],
    "COLETOR": ["Q1.C", "BZ1.-", "D4.A"],
    "5V": ["ESP.5V", "BZ1.+", "D4.K"],
    "J1R": ["J1.R"],
}


def verifica():
    pai = {}
    def f(x):
        pai.setdefault(x, x)
        while pai[x] != x: pai[x] = pai[pai[x]]; x = pai[x]
        return x
    def une(a, b): pai[f(a)] = f(b)
    pino_no = {}
    usados = {}
    for nome, (tipo, pinos, _) in COMP.items():
        for p, h in pinos.items():
            pino_no[f"{nome}.{p}"] = no(h)
            usados.setdefault(h, []).append(f"{nome}.{p}")
    for p, hs in ESP.items():
        for h in hs: usados.setdefault(h, []).append(p)
        pino_no[p] = no(hs[0])
        for h in hs[1:]: une(no(hs[0]), no(h))       # pinos GND internos do ESP32
    for a, b, _, _ in FIOS:
        une(no(a), no(b))
        for h in (a, b):
            if ":" not in h: usados.setdefault(h, []).append("fio")
    erros = []
    # furo ocupado por mais de um terminal
    for h, quem in usados.items():
        if len(quem) > 1: erros.append(f"furo {h} usado por {quem}")
    # cada rede deve estar num unico no, e redes distintas em nos distintos
    raiz_rede = {}
    for rede, pinos in NETS.items():
        rs = {f(pino_no[p]) for p in pinos}
        if len(rs) != 1: erros.append(f"rede {rede} partida em {len(rs)} grupos: {pinos}")
        raiz_rede[rede] = rs.pop()
    vistos = {}
    for rede, r in raiz_rede.items():
        if r in vistos: erros.append(f"CURTO entre as redes {vistos[r]} e {rede}")
        vistos[r] = rede
    # pinos do ESP32 nao usados nao podem estar ligados a nenhuma rede
    usadosESP = {p for ps in NETS.values() for p in ps if p.startswith("ESP.")}
    for p in ESP:
        if p not in usadosESP and f(pino_no[p]) in vistos:
            erros.append(f"pino {p} ligado indevidamente a {vistos[f(pino_no[p])]}")
    return erros


# ---------------------------- desenho ----------------------------
def desenha(arq):
    W, H = (NCOL + 4) * U, 41 * U
    fig = plt.figure(figsize=(W / 25.4 * 1.0, H / 25.4 * 1.0))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(-1.5 * U, (NCOL + 2.5) * U); ax.set_ylim(-1.8 * U, 39.8 * U)
    ax.set_aspect("equal"); ax.axis("off")
    P = lambda c, y: (c * U, y * U)
    # placas
    for y0, y1 in ((-1.0, 15.2), (22.8, 39.2)):
        ax.add_patch(FancyBboxPatch(P(-0.2, y0), (NCOL + 1.4) * U, (y1 - y0) * U, boxstyle="round,pad=0,rounding_size=1.2",
                                    fc="#f4f2ec", ec="#bdbab0", lw=0.8, zorder=0))
        ax.add_patch(Rectangle(P(0.3, (y0 + 0.0) if y0 > 0 else 8.15), (NCOL + 0.5) * U, 1.3 * U, fc="#e6e3da", ec="none", zorder=0)) if False else None
    ax.add_patch(Rectangle(P(0.3, 8.0), (NCOL + 0.4) * U, 1.0 * U, fc="#e4e1d7", ec="none", zorder=0))   # canal B
    ax.add_patch(Rectangle(P(0.3, 29.0), (NCOL + 0.4) * U, 1.0 * U, fc="#e4e1d7", ec="none", zorder=0))  # canal A
    # trilhos
    for rail, y in RAIL.items():
        ax.plot([0.6 * U, (NCOL + 0.4) * U], [(y + (0.5 if y in (1, 38) else -0.5)) * U] * 2, color=RAIL_COR[rail], lw=0.9, zorder=1)
        for c in range(1, NCOL + 1):
            if (c - 1) % 6 == 5: continue
            ax.add_patch(Rectangle(P(c - 0.17, y - 0.17), 0.34 * U, 0.34 * U, fc="#4a4945", ec="none", zorder=1))
        ax.text(-0.6 * U, y * U, RAIL_TXT[rail], fontsize=4.5, ha="right", va="center", color=RAIL_COR[rail], fontweight="bold")
    # furos
    for (pl, r), y in Y.items():
        for c in range(1, NCOL + 1):
            ax.add_patch(Rectangle(P(c - 0.17, y - 0.17), 0.34 * U, 0.34 * U, fc="#4a4945", ec="none", zorder=1))
        ax.text(0.2 * U, y * U, r, fontsize=4, ha="center", va="center", color="#7a776e")
        ax.text((NCOL + 0.8) * U, y * U, r, fontsize=4, ha="center", va="center", color="#7a776e")
    for c in (1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60):
        for yy in (8.5, 29.5):
            ax.text(c * U, yy * U, str(c), fontsize=3.8, ha="center", va="center", color="#7a776e")
    ax.text(-1.2 * U, 19 * U, "", fontsize=6)
    ax.text((NCOL + 1.9) * U, 7.0 * U, "PROTOBOARD B", fontsize=5, rotation=90, ha="center", va="center", color="#7a776e")
    ax.text((NCOL + 1.9) * U, 31.0 * U, "PROTOBOARD A", fontsize=5, rotation=90, ha="center", va="center", color="#7a776e")

    # ESP32
    ax.add_patch(FancyBboxPatch(P(1.4, 13.5), 21.6 * U, 11.0 * U, boxstyle="round,pad=0,rounding_size=0.8",
                                fc="#1f2d3a", ec="#0d151c", lw=0.8, zorder=5, alpha=0.93))
    ax.add_patch(Rectangle(P(2.0, 15.4), 7.0 * U, 7.2 * U, fc="#1a1a1a", ec="#555", lw=0.4, zorder=6))       # antena (PCB)
    ax.add_patch(Rectangle(P(3.2, 15.9), 10.8 * U, 6.2 * U, fc="#b8bcc2", ec="#7d8187", lw=0.5, zorder=6))   # modulo
    ax.text(*P(8.6, 19.0), "ESP32-WROOM-32", fontsize=4.2, ha="center", va="center", zorder=7, color="#2b2b2b")
    ax.add_patch(Rectangle(P(21.6, 17.6), 2.4 * U, 2.8 * U, fc="#c8c8c8", ec="#777", lw=0.5, zorder=6))       # USB
    ax.text(*P(18.0, 19.0), "U1\nESP32-DevKitC V4", fontsize=4.5, ha="center", va="center", color="white", zorder=7, fontweight="bold")
    for i, p in enumerate(TOPO):
        ax.add_patch(Circle(P(3 + i, 24), 0.22 * U, fc="#d4af37", ec="none", zorder=7))
        ax.text(*P(3 + i, 23.15), p, fontsize=3.0, ha="center", va="center", color="white", zorder=7, rotation=90)
    for i, p in enumerate(BASE):
        ax.add_patch(Circle(P(3 + i, 14), 0.22 * U, fc="#d4af37", ec="none", zorder=7))
        ax.text(*P(3 + i, 14.85), p, fontsize=3.0, ha="center", va="center", color="white", zorder=7, rotation=90)

    # componentes
    for nome, (tipo, pinos, rot) in COMP.items():
        pts = [P(*furo(h)) for h in pinos.values()]
        (x0, y0), (x1, y1) = pts[0], pts[-1]
        for (x, y) in pts: ax.add_patch(Circle((x, y), 0.2 * U, fc="#9a9a9a", ec="none", zorder=8))
        if tipo == "R":
            ax.plot([x0, x1], [y0, y1], color="#9a9a9a", lw=0.9, zorder=8)
            xm = (x0 + x1) / 2
            ax.add_patch(FancyBboxPatch((xm - 3.2, y0 - 1.0), 6.4, 2.0, boxstyle="round,pad=0,rounding_size=0.9",
                                        fc="#e8c98f", ec="#9b7f4a", lw=0.5, zorder=9))
            ax.text(xm, y0, f"{nome} {rot}", fontsize=3.4, ha="center", va="center", zorder=10)
        elif tipo == "CE":
            ax.plot([x0, x1], [y0, y1], color="#9a9a9a", lw=0.9, zorder=8)
            xm = (x0 + x1) / 2
            ax.add_patch(FancyBboxPatch((xm - 3.0, y0 - 1.1), 6.0, 2.2, boxstyle="round,pad=0,rounding_size=0.5",
                                        fc="#2b4f9e", ec="#1b3570", lw=0.5, zorder=9))
            ax.text(xm, y0, f"{nome} {rot}", fontsize=3.3, ha="center", va="center", zorder=10, color="white")
            ax.text(x0 + 0.6, y0 + 1.3, "+", fontsize=4.5, ha="center", va="bottom", zorder=10)
        elif tipo == "CC":
            ax.plot([x0, x1], [y0, y1], color="#9a9a9a", lw=0.9, zorder=8)
            xm = (x0 + x1) / 2
            ax.add_patch(FancyBboxPatch((xm - 2.6, y0 - 0.9), 5.2, 1.8, boxstyle="round,pad=0,rounding_size=0.9",
                                        fc="#e8913a", ec="#a85c17", lw=0.5, zorder=9))
            ax.text(xm, y0, f"{nome} {rot}", fontsize=3.2, ha="center", va="center", zorder=10)
        elif tipo == "LED":
            ax.plot([x0, x1], [y0, y1], color="#9a9a9a", lw=0.9, zorder=8)
            ax.add_patch(Circle(((x0 + x1) / 2, y0 + 1.5), 2.3, fc=rot, ec="#333", lw=0.5, zorder=9, alpha=0.95))
            ax.text((x0 + x1) / 2, y0 + 1.5, nome, fontsize=3.4, ha="center", va="center", zorder=10, color="white", fontweight="bold")
            ax.text(x1 + 0.9, y0 - 1.1, "K", fontsize=3, zorder=10)
        elif tipo == "D":
            ax.plot([x0, x1], [y0, y1], color="#9a9a9a", lw=0.9, zorder=8)
            xm = (x0 + x1) / 2
            ax.add_patch(Rectangle((xm - 2.8, y0 - 0.7), 5.6, 1.4, fc="#d9603b", ec="#8e3a20", lw=0.4, zorder=9))
            ax.add_patch(Rectangle((xm + 1.8, y0 - 0.7), 0.8, 1.4, fc="#222", ec="none", zorder=10))
            ax.text(xm - 0.4, y0 + 1.5, "D4 1N4148 (faixa = K)", fontsize=3, ha="center", va="bottom", zorder=10)
        elif tipo == "NPN":
            xm = (x0 + x1) / 2
            ax.add_patch(Polygon([(x0 - 1.2, y0 - 1.0), (x1 + 1.2, y0 - 1.0), (x1 + 1.2, y0 + 1.0), (x0 - 1.2, y0 + 1.0)],
                                 fc="#222", ec="none", zorder=9))
            ax.text(xm, y0, "Q1", fontsize=3.4, ha="center", va="center", zorder=10, color="white", fontweight="bold")
        elif tipo == "BUZ":
            ax.add_patch(Circle(((x0 + x1) / 2, y0 + 1.0), 5.5, fc="#202020", ec="#000", lw=0.5, zorder=9, alpha=0.95))
            ax.add_patch(Circle(((x0 + x1) / 2, y0 + 1.0), 1.0, fc="#555", ec="none", zorder=10))
            ax.text((x0 + x1) / 2, y0 + 4.2, "BZ1 buzzer 5 V", fontsize=3.2, ha="center", va="center", zorder=10, color="white")
            ax.text(x0, y0 - 1.6, "−", fontsize=5, ha="center", zorder=10, color="white")
            ax.text(x1, y0 - 1.6, "+", fontsize=5, ha="center", zorder=10, color="white")
        elif tipo in ("BORNE", "JACK"):
            fc = "#2f8f4e" if tipo == "BORNE" else "#2a2a2a"
            ax.add_patch(Rectangle((x0 - 1.5, y0 - 0.2), (x1 - x0) + 3.0, 5.2, fc=fc, ec="#111", lw=0.5, zorder=9))
            for (x, y), nm in zip(pts, pinos.keys()):
                ax.add_patch(Circle((x, y + 2.6), 0.9, fc="#c9c9c9" if tipo == "BORNE" else "#555", ec="#333", lw=0.3, zorder=10))
                ax.text(x, y + 0.6, nm, fontsize=2.8, ha="center", va="center", zorder=10, color="white")
            ax.text((x0 + x1) / 2, y0 + 6.2, rot, fontsize=3.4, ha="center", va="bottom", zorder=10)

    # fios
    for i, (a, b, cor, _) in enumerate(FIOS):
        (xa, ya), (xb, yb) = P(*furo(a)), P(*furo(b))
        def saida(y, i=i):          # deslocamento vertical ate um corredor livre
            yy = y / U
            if yy <= 7.5: return (8.5 + ((i % 3) - 1) * 0.3) * U   # metade inferior da placa B -> canal central B
            if 9.5 <= yy <= 14.5: return y + 1.2 * U  # metade superior da placa B -> abaixo do ESP32
            if 23.5 <= yy <= 28.5: return y - 1.2 * U # metade inferior da placa A
            return 29.6 * U                          # metade superior da placa A -> canal central A
        if abs(ya - yb) > 15 * U:   # fios entre placas contornam o ESP32 pela direita
            xr = 24.6 * U + (i % 6) * 0.55 * U
            sa, sb = saida(ya), saida(yb)
            verts = [(xa, ya), (xa, sa), (xr, sa), (xr, sb), (xb, sb), (xb, yb)]
            path = Path(verts, [Path.MOVETO] + [Path.LINETO] * 5)
        elif abs(xa - xb) > 6 * U and abs(ya - yb) > 0.1:
            sa = saida(ya)
            verts = [(xa, ya), (xa, sa), (xb, sa), (xb, yb)]
            path = Path(verts, [Path.MOVETO] + [Path.LINETO] * 3)
        elif abs(ya - yb) < 0.1:
            mid = ((xa + xb) / 2, ya - 1.6 * U)
            path = Path([(xa, ya), mid, (xb, yb)], [Path.MOVETO, Path.CURVE3, Path.CURVE3])
        else:
            path = Path([(xa, ya), (xb, yb)], [Path.MOVETO, Path.LINETO])
        ax.add_patch(PathPatch(path, fc="none", ec=cor, lw=1.3, zorder=11, capstyle="round", joinstyle="round", alpha=0.9))
        for (x, y) in ((xa, ya), (xb, yb)):
            ax.add_patch(Circle((x, y), 0.26 * U, fc=cor, ec="#222", lw=0.3, zorder=12))
    fig.savefig(arq, dpi=400)
    plt.close(fig)


if __name__ == "__main__":
    erros = verifica()
    json.dump({"erros": erros, "n_fios": len(FIOS), "n_comp": len(COMP), "n_redes": len(NETS)},
              open(RAIZ + "/protoboard/verificacao.json", "w"), indent=1, ensure_ascii=False)
    print("ERROS:", erros if erros else "nenhum")
    desenha(RAIZ + "/protoboard/protoboard_voltguard.png")
    import sys
    sys.exit(1 if erros else 0)
