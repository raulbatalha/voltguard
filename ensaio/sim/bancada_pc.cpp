// Bancada virtual no PC: executa o roteiro VG-PE-05 contra o nucleo real do firmware.
// Compilar: g++ -O2 -std=c++17 -I../../firmware/VoltGuard bancada_pc.cpp -o bancada && ./bancada
#include <cstdio>
#include <string>
#include "voltguard_bancada.h"
using namespace vgb;

static FILE* abre(const std::string& n) { FILE* f = fopen(("dados/" + n).c_str(), "w"); return f; }
static void regCsv(const Amostra& a, void* p) {
  fprintf((FILE*)p, "%lu,%.3f,%.3f,%.3f,%.4f,%.4f,%.4f,%s,%d\n", (unsigned long)a.t_s, a.iReal, a.iMed, a.tCabo,
          a.tPonto, a.tAmb, a.dt, isnan(a.taxa) ? "" : std::to_string(a.taxa).c_str(), a.estado);
}
static int reprovacoes = 0;
static const char* CAB = "t_s,i_real_A,i_medida_A,t_cabo_C,t_ponto_C,t_amb_C,dT_C,taxa_C_min,estado\n";

int main() {
  if (system("mkdir -p dados") != 0) return 2;
  FILE* js = fopen("dados/resumo.json", "w");
  fprintf(js, "{\n");

  // ---------------- E1: exatidao da corrente ----------------
  vg::Config cfg;
  FILE* f = abre("e1_exatidao.csv");
  fprintf(f, "i_ref_A,revB_A,revB_erro_pct,revB_fora,v4_A,v4_erro_pct,v4_fora\n");
  float correntes[] = {1, 2, 3, 5, 8, 10, 12, 15, 17, 20, 22, 25, 28, 30};
  ModeloAdc mB; mB.vref_mV = 1320; mB.ganhoSct = 1.0f;
  ModeloAdc m4; m4.vref_mV = 1650; m4.ganhoSct = 1.0f;
  float erroMax215 = 0;
  for (float i : correntes) {
    bool fB, f4;
    float b = mede(i, 1, mB, cfg, 20, 11, &fB), v = mede(i, 1, m4, cfg, 20, 11, &f4);
    float eb = (b - i) / i * 100, e4 = (v - i) / i * 100;
    if (i >= 2 && i <= 15 && fabsf(eb) > erroMax215) erroMax215 = fabsf(eb);
    fprintf(f, "%.1f,%.4f,%.3f,%d,%.4f,%.3f,%d\n", i, b, eb, fB, v, e4, f4);
  }
  fclose(f);
  fprintf(js, "\"e1_erro_max_2_15A_pct\": %.3f,\n", erroMax215);

  // ---------------- E2: ruido sem carga ----------------
  vg::Config c0; c0.pisoRuidoA = 0.0f;
  float maxR = 0, somaR = 0;
  for (int j = 0; j < 60; j++) { float r = mede(0.0f, 1, mB, c0, 1, 100 + j); somaR += r; if (r > maxR) maxR = r; }
  fprintf(js, "\"e2_ruido_max_A\": %.4f, \"e2_ruido_medio_A\": %.4f,\n", maxR, somaR / 60);
  float com = mede(0.0f, 1, mB, cfg, 60, 7);
  fprintf(js, "\"e2_leitura_com_piso_A\": %.4f,\n", com);

  // ---------------- E3: correntes baixas com 5 espiras ----------------
  f = abre("e3_baixa_corrente.csv");
  fprintf(f, "i_ref_A,espiras1_A,espiras1_erro_pct,espiras5_A,espiras5_erro_pct\n");
  vg::Config c5; c5.nEspiras = 5; c5.pisoRuidoA = 0.03f;
  float lows[] = {0.3f, 0.5f, 1.0f, 2.0f, 3.0f};
  for (float i : lows) {
    float a = mede(i, 1, mB, cfg, 20, 21), b = mede(i, 5, mB, c5, 20, 21);
    fprintf(f, "%.2f,%.4f,%.2f,%.4f,%.2f\n", i, a, (a - i) / i * 100, b, (b - i) / i * 100);
  }
  fclose(f);

  // ---------------- E4: ensaio termico (identificacao de k) ----------------
  static const Fase FT[] = {{60, 0, 0, 0, false, -1, -1}, {2400, 10.0f, 0, 0, false, -1, -1}, {1200, 0, 0, 0, false, -1, -1}};
  Cenario ct{"E4", "Ensaio termico 10 A", FT, 3};
  struct Acc { FILE* f; double soma; int n; } acc{abre("e4_termico.csv"), 0, 0};
  fprintf(acc.f, "%s", CAB);
  auto regT = [](const Amostra& a, void* p) {
    Acc* c = (Acc*)p; regCsv(a, c->f);
    if (a.t_s > 60 + 2400 - 120 && a.t_s <= 60 + 2400) { c->soma += a.dt; c->n++; }
  };
  executa(ct, cfg, 5, regT, &acc);
  fclose(acc.f);
  float kEst = (float)(acc.soma / acc.n / 100.0);
  fprintf(js, "\"e4_k_real\": 0.060, \"e4_k_estimado\": %.5f,\n", kEst);

  // ---------------- E5/E6: cenarios de diagnostico ----------------
  vg::Config cd = configDemo(kEst);
  fprintf(js, "\"cenarios\": [\n");
  for (int k = 0; k < N_CENARIOS; k++) {
    const Cenario& C = CENARIOS[k];
    fprintf(js, "  {\"id\": \"%s\", \"nome\": \"%s\", \"rep\": [", C.id, C.nome);
    for (int rep = 0; rep < 3; rep++) {
      FILE* fc = nullptr;
      if (rep == 0) { fc = abre(std::string("cen_") + C.id + ".csv"); fprintf(fc, "%s", CAB); }
      ResultadoCenario r = executa(C, cd, 1000 + 37 * k + rep, fc ? regCsv : nullptr, fc);
      if (fc) fclose(fc);
      fprintf(js, "{\"ok\": %s, \"t_det\": %lu, \"trocas\": %d, \"motivo\": \"%s\"}%s", r.aprovado ? "true" : "false",
              (unsigned long)r.tDeteccao_s, r.trocasEstado, r.motivo, rep < 2 ? ", " : "");
      if (!r.aprovado) reprovacoes++;
      printf("%s rep%d: %s (%s) deteccao=%lus trocas=%d\n", C.id, rep + 1, r.aprovado ? "APROVADO" : "REPROVADO",
             r.motivo, (unsigned long)r.tDeteccao_s, r.trocasEstado);
    }
    fprintf(js, "]}%s\n", k < N_CENARIOS - 1 ? "," : "");
  }
  fprintf(js, "],\n");
  // estabilidade
  int tr[3];
  for (int rep = 0; rep < 3; rep++) tr[rep] = ensaioEstabilidade(cd, 500 + rep);
  fprintf(js, "\"estabilidade_trocas\": [%d, %d, %d]\n}\n", tr[0], tr[1], tr[2]);
  printf("Estabilidade: %d %d %d trocas\n", tr[0], tr[1], tr[2]);
  printf("k estimado = %.4f (real 0.060) | erro max 2-15 A = %.2f %% | ruido max = %.3f A\n", kEst, erroMax215, maxR);
  fclose(js);
  if (erroMax215 >= 5.0f) reprovacoes++;
  if (fabsf(kEst - 0.06f) / 0.06f >= 0.05f) reprovacoes++;
  for (int k = 0; k < 3; k++) if (tr[k] > 1) reprovacoes++;
  printf("RESULTADO GERAL: %s (%d reprovacao(oes))\n", reprovacoes ? "REPROVADO" : "APROVADO", reprovacoes);
  return reprovacoes ? 1 : 0;
}
