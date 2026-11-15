// Testes do nucleo VoltGuard no PC:  g++ -std=c++17 -I../VoltGuard test_core.cpp -o t && ./t
#include <cstdio>
#include <cstdlib>
#include <random>
#include <vector>
#include "voltguard_core.h"
using namespace vg;

static int falhas = 0, total = 0;
#define CHECK(cond, msg) do { total++; if (!(cond)) { falhas++; printf("  FALHOU: %s\n", msg); } else printf("  ok: %s\n", msg); } while (0)

// gera janela de 10 ciclos a 60 Hz, 5 kSa/s, como o ADC entregaria (mV)
static std::vector<uint16_t> janela(float iA, int espiras, float vref_mV, float ruido_mV, unsigned seed = 1) {
  std::mt19937 g(seed); std::normal_distribution<float> n(0, ruido_mV);
  const int N = 834; std::vector<uint16_t> a(N);
  const float amp = iA * espiras / 30.0f * 1000.0f * sqrtf(2.0f);
  for (int k = 0; k < N; k++) {
    float v = vref_mV + amp * sinf(2 * M_PI * 60.0f * k / 5000.0f) + n(g);
    v = fminf(fmaxf(v, 0.0f), 3100.0f);  // saturacao do ADC
    a[k] = (uint16_t)lroundf(v);
  }
  return a;
}

int main() {
  Config c;
  puts("[1] Corrente RMS");
  for (float i : {2.0f, 5.0f, 10.0f, 20.0f}) {
    auto a = janela(i, 1, 1320, 3);
    auto r = calculaRms(a.data(), (int)a.size(), c);
    char m[96]; snprintf(m, sizeof m, "%.1f A medido como %.2f A (erro < 2%%)", i, r.iRmsA);
    CHECK(fabsf(r.iRmsA - i) / i < 0.02f, m);
  }
  {
    auto a = janela(0, 1, 1320, 3);
    auto r = calculaRms(a.data(), (int)a.size(), c);
    char m[96]; snprintf(m, sizeof m, "sem carga, ruido 3 mV -> %.2f A (zerado pelo piso)", r.iRmsA);
    CHECK(r.iRmsA == 0.0f, m);
  }
  {
    auto a = janela(28, 1, 1650, 2);
    auto r = calculaRms(a.data(), (int)a.size(), c);
    CHECK(r.foraFaixa, "28 A com referencia 1,65 V sinaliza saida da faixa linear");
    auto b = janela(15, 1, 1320, 2);
    CHECK(!calculaRms(b.data(), (int)b.size(), c).foraFaixa, "15 A com referencia 1,32 V fica na faixa linear");
  }
  {
    Config c5 = c; c5.nEspiras = 5; c5.pisoRuidoA = 0.03f;
    auto a = janela(1.0f, 5, 1320, 3);
    auto r = calculaRms(a.data(), (int)a.size(), c5);
    char m[96]; snprintf(m, sizeof m, "1 A com 5 espiras -> %.3f A", r.iRmsA);
    CHECK(fabsf(r.iRmsA - 1.0f) < 0.03f, m);
  }

  puts("[2] Validacao DS18B20");
  CHECK(!temperaturaValida(-127.0f, 30, true), "-127 C rejeitado");
  CHECK(!temperaturaValida(85.0f, 0, false), "85 C na 1a leitura rejeitado");
  CHECK(!temperaturaValida(85.0f, 31, true), "85 C com salto de 54 C rejeitado");
  CHECK(temperaturaValida(85.0f, 82, true), "85 C real (vinha de 82 C) aceito");
  CHECK(temperaturaValida(34.5f, 34.0f, true), "34,5 C aceito");

  puts("[3] Taxa de elevacao");
  {
    Tendencia<32> t; bool ok;
    for (int k = 0; k < 25; k++) t.adiciona(k * 5000, 30.0f + 0.5f * (k * 5.0f / 60.0f));
    float r = t.porMinuto(ok);
    char m[96]; snprintf(m, sizeof m, "rampa 0,5 C/min estimada em %.3f C/min", r);
    CHECK(ok && fabsf(r - 0.5f) < 0.01f, m);
    Tendencia<32> u; u.adiciona(0, 30); u.adiciona(1000, 30.06f);
    u.porMinuto(ok); CHECK(!ok, "duas leituras consecutivas nao geram tendencia");
  }

  puts("[4] Diagnostico");
  auto roda = [&](Diagnostico& d, uint32_t t0, uint32_t dur, float i, float tp, float ta,
                  float taxa = 0, bool tv = true, bool ok = true) {
    Saida s{};
    for (uint32_t t = t0; t <= t0 + dur; t += 1000) s = d.atualiza({t, i, tp, ta, taxa, tv, ok});
    return s;
  };
  {
    Diagnostico d(c);
    auto s = roda(d, 1000, 5000, 0.0f, 45.0f, 33.0f);
    CHECK(s.estado == NORMAL, "45 C no ponto com ambiente de 33 C (dT 12) e sem corrente: NORMAL");
    s = roda(d, 7000, 5000, 0.0f, 62.0f, 33.0f);
    CHECK(s.estado == AQUECIMENTO_EXTERNO, "ponto quente SEM corrente: AQUECIMENTO EXTERNO (nao mau contato)");
  }
  {
    Diagnostico d(c);
    auto s = roda(d, 1000, 10000, 10.0f, 36.0f, 33.0f);
    CHECK(s.estado == ALERTA_PREVENTIVO, "10 A por 10 s, temperatura normal: ALERTA PREVENTIVO");
    s = roda(d, 12000, 30000, 10.0f, 60.0f, 33.0f, 1.5f);
    CHECK(s.estado == SOBRECARGA, "10 A mantidos + dT 27 C subindo: SOBRECARGA");
  }
  {
    Diagnostico d(c);
    auto s = roda(d, 1000, 300000, 10.0f, 36.0f, 33.0f);
    CHECK(s.estado == SOBRECARGA, "10 A mantidos por 5 min sem resposta termica: SOBRECARGA");
  }
  {
    Diagnostico d(c);  // 4 A -> dT esperado 1,6 C; medido 20 C -> excesso 18 C
    auto s = roda(d, 1000, 30000, 4.0f, 53.0f, 33.0f);
    CHECK(s.estado == ALERTA_TEMPERATURA, "4 A com dT 20 C antes de 60 s: ALERTA DE TEMPERATURA");
    s = roda(d, 32000, 40000, 4.0f, 53.0f, 33.0f);
    CHECK(s.estado == MAU_CONTATO, "4 A com dT 20 C por mais de 60 s: POSSIVEL MAU CONTATO");
  }
  {
    Diagnostico d(c);  // oscilando em torno do limite: histerese evita troca
    int trocas = 0; Saida s{};
    for (int k = 0; k < 60; k++) {
      float i = (k % 2) ? 8.2f : 7.9f;
      s = d.atualiza({(uint32_t)(1000 + k * 1000), i, 35, 33, 0, true, true});
      if (s.mudou) trocas++;
    }
    char m[96]; snprintf(m, sizeof m, "corrente oscilando 7,9/8,2 A: %d troca(s) de estado", trocas);
    CHECK(trocas == 1, m);
  }
  {
    Diagnostico d(c);
    auto s = roda(d, 1000, 3000, 2.0f, 34, 33, 0, true, false);
    CHECK(s.estado == FALHA_SENSOR, "sensor de temperatura ausente: FALHA DE SENSOR");
    s = roda(d, 5000, 2000, 2.0f, 34, 33);
    CHECK(s.estado == NORMAL, "sensor volta: retorna a NORMAL");
  }
  printf("\n%d/%d verificacoes aprovadas\n", total - falhas, total);
  return falhas ? 1 : 0;
}
