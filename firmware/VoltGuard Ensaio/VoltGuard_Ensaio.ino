// =====================================================================
//  VoltGuard - Ensaio automatico na bancada virtual (Rev. B)
//  Roda o roteiro VG-PE-05 dentro do ESP32 (ou do Wokwi) usando o nucleo
//  REAL do firmware e modelos fisicos no lugar dos sensores. Nao precisa
//  de nenhum sensor ligado. Ao final imprime "RESULTADO GERAL: APROVADO"
//  e acende o LED verde (GPIO25); se algo falhar, acende o vermelho (GPIO27).
//  Copie para esta pasta os arquivos voltguard_core.h e voltguard_bancada.h.
// =====================================================================
#define VGB_N_AMOSTRAS 167   // 10 ciclos a 1 kSa/s: 5x mais rapido, mesma exatidao
#define VGB_TS 1e-3f
#include "voltguard_core.h"
#include "voltguard_bancada.h"

const int LED_OK = 25, LED_FALHA = 27;
int aprovados = 0, total = 0;

void registra(const char* id, const char* desc, bool ok, const char* detalhe) {
  total++; if (ok) aprovados++;
  Serial.printf("[%s] %-48s %s  %s\n", id, desc, ok ? "APROVADO " : "REPROVADO", detalhe);
}

struct AccTermico { double soma; int n; };
void acumulaTermico(const vgb::Amostra& a, void* p) {
  AccTermico* c = (AccTermico*)p;
  if (a.t_s > 60 + 2400 - 120 && a.t_s <= 60 + 2400) { c->soma += a.dt; c->n++; }
}

void setup() {
  Serial.begin(115200);
  delay(300);
  pinMode(LED_OK, OUTPUT); pinMode(LED_FALHA, OUTPUT);
  Serial.println("\nVoltGuard Bancada Virtual Rev. B");
  Serial.println("Roteiro VG-PE-05 executado em tempo virtual contra o nucleo real do firmware\n");
  uint32_t t0 = millis();
  char det[96];

  // E1 - exatidao entre 2 e 15 A
  vg::Config cfg;
  vgb::ModeloAdc m; m.ganhoSct = 1.0f;
  float pts[] = {2, 5, 10, 15};
  float emax = 0;
  for (float i : pts) { float r = vgb::mede(i, 1, m, cfg, 10, 11); float e = fabsf(r - i) / i * 100; if (e > emax) emax = e; }
  snprintf(det, sizeof det, "erro maximo %.2f %% (limite 5 %%)", emax);
  registra("E1", "Exatidao da corrente, 2 a 15 A", emax < 5.0f, det);

  // E1b - faixa linear ate 24 A com referencia 1,32 V
  float r24 = vgb::mede(24, 1, m, cfg, 10, 12);
  snprintf(det, sizeof det, "24 A medidos como %.2f A", r24);
  registra("E1b", "Faixa linear ate 24 A (referencia 1,32 V)", fabsf(r24 - 24) / 24 < 0.02f, det);

  // E2 - ruido sem carga
  float r0 = vgb::mede(0, 1, m, cfg, 20, 13);
  snprintf(det, sizeof det, "leitura sem carga %.3f A", r0);
  registra("E2", "Leitura nula sem carga (piso de ruido)", r0 < 0.01f, det);

  // E3 - baixa corrente com 5 espiras
  vg::Config c5; c5.nEspiras = 5; c5.pisoRuidoA = 0.03f;
  float r1 = vgb::mede(1.0f, 5, m, c5, 10, 14);
  snprintf(det, sizeof det, "1 A medido como %.3f A", r1);
  registra("E3", "Corrente baixa (1 A, 5 espiras)", fabsf(r1 - 1.0f) < 0.05f, det);

  // E4 - ensaio termico e identificacao de k
  static const vgb::Fase FT[] = {{60, 0, 0, 0, false, -1, -1}, {2400, 10.0f, 0, 0, false, -1, -1}};
  vgb::Cenario ct{"E4", "Ensaio termico", FT, 2};
  AccTermico acc{0, 0};
  vgb::executa(ct, cfg, 5, acumulaTermico, &acc);
  float k = (float)(acc.soma / acc.n / 100.0);
  snprintf(det, sizeof det, "k identificado %.4f C/A2 (modelo 0,0600)", k);
  registra("E4", "Ensaio termico 10 A / 40 min", fabsf(k - 0.06f) / 0.06f < 0.05f, det);

  // Cenarios de diagnostico, 3 repeticoes cada
  vg::Config cd = vgb::configDemo(k);
  for (int c = 0; c < vgb::N_CENARIOS; c++) {
    int ok = 0; char motivo[96] = "";
    for (int rep = 0; rep < 3; rep++) {
      vgb::ResultadoCenario r = vgb::executa(vgb::CENARIOS[c], cd, 1000 + 37 * c + rep);
      if (r.aprovado) ok++; else strncpy(motivo, r.motivo, sizeof motivo - 1);
    }
    snprintf(det, sizeof det, "%d de 3 %s", ok, ok == 3 ? "" : motivo);
    registra(vgb::CENARIOS[c].id, vgb::CENARIOS[c].nome, ok == 3, det);
  }

  // Estabilidade
  int tr = vgb::ensaioEstabilidade(cd, 500);
  snprintf(det, sizeof det, "%d troca(s) de estado em 120 s", tr);
  registra("E7", "Estabilidade com corrente oscilando no limite", tr <= 1, det);

  bool geral = (aprovados == total);
  Serial.printf("\nEnsaios aprovados: %d de %d  (tempo de execucao %lu ms)\n", aprovados, total,
                (unsigned long)(millis() - t0));
  Serial.printf("RESULTADO GERAL: %s\n", geral ? "APROVADO" : "REPROVADO");
  digitalWrite(LED_OK, geral); digitalWrite(LED_FALHA, !geral);
}

void loop() { delay(1000); }
