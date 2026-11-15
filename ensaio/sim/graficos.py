"""Graficos da bancada virtual VoltGuard (dados em ./dados)."""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

D = os.path.join(os.path.dirname(__file__), "dados")
OUT = os.path.join(os.path.dirname(__file__), "fig")
os.makedirs(OUT, exist_ok=True)

AZUL, LARANJA, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
TXT, TXT2, GRADE, FUNDO = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
EST = {0: ("NORMAL", "#0ca30c"), 1: ("AQUEC. EXTERNO", "#fab219"), 2: ("ALERTA TEMP.", "#fab219"),
       3: ("ALERTA PREV.", "#fab219"), 4: ("MAU CONTATO", "#d03b3b"), 5: ("SOBRECARGA", "#d03b3b"),
       6: ("FALHA SENSOR", "#8a8985")}

plt.rcParams.update({
    "font.family": "Liberation Sans", "font.size": 9, "axes.edgecolor": GRADE, "axes.labelcolor": TXT2,
    "xtick.color": TXT2, "ytick.color": TXT2, "axes.grid": True, "grid.color": GRADE, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": "white", "axes.facecolor": "white",
    "legend.frameon": False, "axes.titlesize": 10, "axes.titleweight": "bold", "axes.titlecolor": TXT,
})


def csv(n):
    return np.genfromtxt(os.path.join(D, n), delimiter=",", names=True)


# ------------------------------ E1 exatidao ------------------------------
e1 = csv("e1_exatidao.csv")
fig, ax = plt.subplots(figsize=(7.2, 3.4))
ax.axhspan(-5, 5, color="#f0efec", zorder=0)
ax.text(1.2, 4.2, "faixa aceita (±5 %)", color=TXT2, fontsize=8)
ax.plot(e1["i_ref_A"], e1["v4_erro_pct"], color=LARANJA, lw=2, marker="s", ms=5, label="Versão 4 (referência 1,65 V)")
ax.plot(e1["i_ref_A"], e1["revB_erro_pct"], color=AZUL, lw=2, marker="o", ms=3.5, label="Rev. B (referência 1,32 V)")
ax.axvline(17, color=LARANJA, lw=0.8, ls=":"); ax.axvline(24.4, color=AZUL, lw=0.8, ls=":")
ax.text(16.6, -6.6, "limite linear v4 ≈17 A", color=TXT2, fontsize=7.5, ha="right")
ax.text(24.0, -6.6, "limite linear Rev. B ≈24 A", color=TXT2, fontsize=7.5, ha="right")
ax.set_xlabel("Corrente de referência (A)"); ax.set_ylabel("Erro da medição (%)")
ax.set_ylim(-7.5, 6); ax.set_xlim(0, 31)
ax.legend(loc="lower left", fontsize=8)
ax.set_title("E1  Erro de medição de corrente em toda a faixa do sensor", loc="left")
fig.tight_layout(); fig.savefig(f"{OUT}/e1_exatidao.png", dpi=200); plt.close(fig)

# ------------------------------ E3 baixa corrente ------------------------------
e3 = csv("e3_baixa_corrente.csv")
fig, ax = plt.subplots(figsize=(7.2, 3.0))
ax.plot(e3["i_ref_A"], e3["espiras1_erro_pct"], color=LARANJA, lw=2, marker="s", ms=4, label="1 passagem do condutor")
ax.plot(e3["i_ref_A"], e3["espiras5_erro_pct"], color=AZUL, lw=2, marker="o", ms=4, label="5 passagens (cfg.nEspiras = 5)")
ax.set_xlabel("Corrente de referência (A)"); ax.set_ylabel("Erro da medição (%)")
ax.legend(fontsize=8); ax.set_title("E3  Correntes baixas: efeito de passar o condutor 5 vezes pelo núcleo", loc="left")
fig.tight_layout(); fig.savefig(f"{OUT}/e3_baixa_corrente.png", dpi=200); plt.close(fig)

# ------------------------------ E4 termico ------------------------------
e4 = csv("e4_termico.csv")
t = e4["t_s"] / 60.0
dT = e4["dT_C"]
# ajuste exponencial no aquecimento: dT = A (1 - exp(-(t - t0)/tau))
m = (e4["t_s"] > 60) & (e4["t_s"] <= 2460)
tt = e4["t_s"][m] - 60; yy = dT[m]
best = None
for tau in np.arange(100, 800, 2.0):
    x = 1 - np.exp(-tt / tau); A = (x @ yy) / (x @ x); err = ((yy - A * x) ** 2).sum()
    if best is None or err < best[0]: best = (err, tau, A)
_, tau, A = best
k_fit = A / 100.0
json.dump({"tau_s": float(tau), "A_C": float(A), "k_fit": float(k_fit)}, open(f"{D}/e4_ajuste.json", "w"))
fig, (a1, a2) = plt.subplots(2, 1, figsize=(7.2, 4.2), sharex=True, gridspec_kw={"height_ratios": [1, 2.4]})
a1.plot(t, e4["i_medida_A"], color=TXT2, lw=1.5); a1.set_ylabel("I (A)"); a1.set_ylim(-1, 12)
a1.set_title("E4  Ensaio térmico: 10 A por 40 min, depois desligado", loc="left")
a2.plot(t, dT, color=AZUL, lw=1.5, label="ΔT medido pelas sondas")
tf = np.linspace(0, 2400, 300)
a2.plot(tf / 60 + 1, A * (1 - np.exp(-tf / tau)), color=LARANJA, lw=2, ls="--", label=f"ajuste: ΔT = {A:.2f}·(1 − e^(−t/{tau:.0f} s))")
a2.set_ylabel("ΔT (°C)"); a2.set_xlabel("Tempo (min)"); a2.legend(fontsize=8, loc="lower center", bbox_to_anchor=(0.6, 0.04))
a2.annotate(f"k = ΔT/I² = {A:.2f}/100 = {k_fit:.4f} °C/A²", xy=(38, A), xytext=(14, A * 0.55), fontsize=8.5, color=TXT,
            arrowprops=dict(arrowstyle="-|>", color=TXT2, lw=0.8))
fig.tight_layout(); fig.savefig(f"{OUT}/e4_termico.png", dpi=200); plt.close(fig)

# ------------------------------ cenarios ------------------------------
res = json.load(open(f"{D}/resumo.json"))
for c in res["cenarios"]:
    d = csv(f"cen_{c['id']}.csv")
    t = d["t_s"] / 60.0
    fig, (a1, a2, a3) = plt.subplots(3, 1, figsize=(7.2, 3.9), sharex=True, gridspec_kw={"height_ratios": [1, 1.6, 0.55]})
    a1.plot(t, d["i_medida_A"], color=TXT2, lw=1.5); a1.set_ylabel("I (A)")
    a1.axhline(5, color=TXT2, lw=0.7, ls=":"); a1.text(t[-1], 5.3, "limite 5 A", ha="right", fontsize=7, color=TXT2)
    a1.set_title(f"{c['id']}  {c['nome']}", loc="left")
    a2.plot(t, d["dT_C"], color=AZUL, lw=1.6); a2.set_ylabel("ΔT (°C)")
    a2.axhline(25, color=TXT2, lw=0.7, ls=":"); a2.text(t[0], 25.8, "limite ΔT 25 °C", fontsize=7, color=TXT2)
    # faixa de estado
    a3.set_yticks([]); a3.grid(False); a3.set_ylim(0, 1)
    est = d["estado"].astype(int)
    ini = 0
    for i in range(1, len(est) + 1):
        if i == len(est) or est[i] != est[ini]:
            nome, cor = EST[est[ini]]
            x0 = t[ini] - 1 / 120; x1 = t[i - 1] + 1 / 120
            a3.axvspan(x0, x1, color=cor, alpha=0.9, lw=0)
            if (x1 - x0) > (t[-1] - t[0]) * 0.09:
                a3.text((x0 + x1) / 2, 0.5, nome, ha="center", va="center", fontsize=7, color="white", fontweight="bold")
            ini = i
    a3.set_xlabel("Tempo (min)"); a3.set_ylabel("Estado", rotation=0, ha="right", va="center")
    fig.tight_layout(h_pad=0.4); fig.savefig(f"{OUT}/cen_{c['id']}.png", dpi=200); plt.close(fig)
print("ok", tau, A, k_fit)
