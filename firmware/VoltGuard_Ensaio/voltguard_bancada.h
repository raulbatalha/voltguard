// =====================================================================
//  VoltGuard - Bancada virtual de ensaio (Rev. B)
//  Modelos fisicos que substituem o hardware para testar o NUCLEO REAL do
//  firmware (voltguard_core.h) em tempo virtual. O mesmo arquivo roda:
//    * no PC (bancada_pc.cpp)  -> gera CSV para graficos e relatorio;
//    * no ESP32 ou no Wokwi    -> VoltGuard_Ensaio.ino imprime APROVADO/REPROVADO.
//  Modelos incluidos:
//    SCT-013-030 + divisor + ADC do ESP32 (ruido, quantizacao, nao linearidade
//    acima de 2,45 V e saturacao), cabo com aquecimento k*I^2 e constante de
//    tempo, sonda DS18B20 (atraso termico, resolucao 0,0625 C, offset, 85 C na
//    energizacao, desconexao = -127 C), fonte de calor externa e mau contato.
// =====================================================================
#pragma once
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "voltguard_core.h"

#ifndef VGB_N_AMOSTRAS
#define VGB_N_AMOSTRAS 833      // 10 ciclos de 60 Hz a 5 kSa/s (igual ao firmware)
#endif
#ifndef VGB_TS
#define VGB_TS 200e-6f
#endif

namespace vgb {

// ------------------------------ Gerador aleatorio ------------------------------
struct Rng {
  uint32_t s;
  explicit Rng(uint32_t seed = 1) : s(seed ? seed : 1) {}
  uint32_t next() { s ^= s << 13; s ^= s >> 17; s ^= s << 5; return s; }
  float u() { return (next() >> 8) * (1.0f / 16777216.0f); }           // [0,1)
  float n() {                                                            // N(0,1)
    float a = u(), b = u();
    if (a < 1e-7f) a = 1e-7f;
    return sqrtf(-2.0f * logf(a)) * cosf(6.2831853f * b);
  }
};

// ------------------------- SCT + divisor + ADC do ESP32 -------------------------
struct ModeloAdc {
  float vref_mV    = 1320.0f;  // ponto medio do divisor (R1 15k / R2 10k)
  float ruido_mV   = 3.5f;     // ruido RMS tipico do ADC
  float ganhoSct   = 1.00f;    // erro de relacao do sensor (tolerancia)
  float harm3      = 0.04f;    // 3a harmonica relativa (cargas reais)
  float linMax_mV  = 2450.0f;  // limite da faixa linear (11 dB)
  float linMin_mV  = 150.0f;
  float sat_mV     = 3100.0f;

  uint16_t converte(float v, Rng& r) const {
    // compressao fora da faixa linear (comportamento tipico do ADC do ESP32)
    if (v > linMax_mV) v = linMax_mV + (v - linMax_mV) * 0.55f;
    if (v < linMin_mV) v = linMin_mV - (linMin_mV - v) * 0.55f;
    v += r.n() * ruido_mV;
    if (v < 0) v = 0;
    if (v > sat_mV) v = sat_mV;
    return (uint16_t)lroundf(v);
  }
};

// Gera uma janela de N amostras (periodo Ts) como analogReadMilliVolts entregaria
inline void geraJanela(uint16_t* buf, int n, float ts_s, float iRms, int espiras,
                       const ModeloAdc& m, Rng& r) {
  const float w = 6.2831853f * 60.0f;
  const float fase = r.u() * 6.2831853f;
  const float amp_mV = iRms * espiras / 30.0f * 1000.0f * 1.41421356f * m.ganhoSct;
  const float jitter = 2e-6f;
  for (int k = 0; k < n; k++) {
    float t = k * ts_s + r.n() * jitter;
    float s = sinf(w * t + fase) + m.harm3 * sinf(3.0f * (w * t + fase));
    buf[k] = m.converte(m.vref_mV + amp_mV * s / sqrtf(1.0f + m.harm3 * m.harm3), r);
  }
}

// --------------------------------- Termico ---------------------------------
struct Cabo {
  float k      = 0.060f;   // C/A^2 real do cabo (desconhecido pelo firmware)
  float tau_s  = 300.0f;   // constante de tempo do cabo
  float extraK = 0.0f;     // aquecimento adicional por mau contato (C/A^2)
  float fonteExt_C = 0.0f; // fonte externa de calor (0 = ausente)
  float tauExt_s = 25.0f;
  float T = 30.0f;         // temperatura da superficie do cabo no ponto da sonda
  void passo(float dt, float iA, float tAmb) {
    float alvo = tAmb + (k + extraK) * iA * iA;
    float tau = tau_s;
    if (fonteExt_C > 0 && fonteExt_C > alvo) { alvo = fonteExt_C; tau = tauExt_s; }
    T += (alvo - T) * (dt / tau);
  }
};

struct Sonda {
  float tau_s = 6.0f;      // atraso do encapsulamento inox
  float offset = 0.0f;     // erro de exatidao (DS18B20: ate +-0,5 C)
  float Tint = 30.0f;
  bool  desconectada = false;
  bool  primeira = true;
  void passo(float dt, float Tmeio) { Tint += (Tmeio - Tint) * (dt / tau_s); }
  float le() {
    if (desconectada) return -127.0f;
    if (primeira) { primeira = false; return 85.0f; }   // valor de reset
    return roundf((Tint + offset) / 0.0625f) * 0.0625f;
  }
};

// ------------------------------- Roteiro -------------------------------
struct Fase {
  uint16_t dur_s;
  float iA;
  float extraK;
  float fonteExt_C;
  bool  falhaAmb;
  int8_t esperadoFim;   // estado esperado ao fim da fase (-1 = nao verificar)
  int8_t proibido;      // estado que nao pode ocorrer na fase (-1 = nenhum)
};

struct Cenario {
  const char* id;
  const char* nome;
  const Fase* fases;
  int nFases;
};

// Registro de cada segundo (para CSV)
struct Amostra {
  uint32_t t_s; float iReal, iMed, tCabo, tPonto, tAmb, dt, taxa; int estado;
};
typedef void (*Registrador)(const Amostra&, void* ctx);

struct ResultadoCenario {
  bool aprovado;
  int  falhas;
  int  trocasEstado;
  uint32_t tDeteccao_s;     // instante em que o estado esperado da ultima fase verificada apareceu
  char motivo[96];
};

// Executa um cenario em tempo virtual. Corrente medida a cada 1 s, temperatura a
// cada 1 s, tendencia a cada 5 s (mesma cadencia do firmware).
inline ResultadoCenario executa(const Cenario& c, const vg::Config& cfg, uint32_t seed,
                                Registrador reg = nullptr, void* ctx = nullptr,
                                const ModeloAdc* adcIn = nullptr, int espiras = 1, float kCabo = 0.060f) {
  static uint16_t buf[VGB_N_AMOSTRAS + 4];
  const int N = VGB_N_AMOSTRAS;
  Rng r(seed);
  ModeloAdc adc = adcIn ? *adcIn : ModeloAdc();
  adc.ganhoSct = adcIn ? adcIn->ganhoSct : 1.0f + (r.u() - 0.5f) * 0.02f;   // +-1 %
  Cabo cabo; cabo.k = kCabo;
  const float tAmb = 30.0f + (r.u() - 0.5f) * 2.0f;
  cabo.T = tAmb;
  Sonda sp, sa; sp.Tint = sa.Tint = tAmb;
  sp.offset = (r.u() - 0.5f) * 0.6f; sa.offset = (r.u() - 0.5f) * 0.6f;

  vg::Diagnostico diag(cfg);
  vg::Tendencia<32> tend;
  float tP = NAN, tA = NAN; bool okP = false, okA = false;
  ResultadoCenario res; memset(&res, 0, sizeof res); res.aprovado = true;
  int estadoAnt = -1;
  uint32_t t = 0;
  int descartes = 2;
  float iMed = 0;

  for (int f = 0; f < c.nFases; f++) {
    const Fase& F = c.fases[f];
    cabo.extraK = F.extraK; cabo.fonteExt_C = F.fonteExt_C;
    sa.desconectada = F.falhaAmb;
    bool viuEsperado = false;
    for (uint16_t s = 0; s < F.dur_s; s++) {
      t++;
      for (int sub = 0; sub < 10; sub++) {             // dinamica termica em 0,1 s
        cabo.passo(0.1f, F.iA, tAmb);
        sp.passo(0.1f, cabo.T);
        sa.passo(0.1f, tAmb);
      }
      geraJanela(buf, N, VGB_TS, F.iA, espiras, adc, r);
      vg::ResultadoRms rr = vg::calculaRms(buf, N, cfg);
      if (descartes > 0) descartes--; else iMed = rr.iRmsA;

      float vP = sp.le(), vA = sa.le();
      okP = vg::temperaturaValida(vP, tP, !isnan(tP)); if (okP) tP = vP;
      okA = vg::temperaturaValida(vA, tA, !isnan(tA)); if (okA) tA = vA;
      if (t % 5 == 0 && okP && okA) tend.adiciona(t * 1000, tP - tA);
      bool tv; float taxa = tend.porMinuto(tv);
      vg::Entradas e{t * 1000, iMed, tP, tA, taxa, tv, okP && okA};
      vg::Saida sd = diag.atualiza(e);
      if (sd.mudou) res.trocasEstado++;
      if (F.proibido >= 0 && (int)sd.estado == F.proibido) {
        if (res.aprovado) {
          snprintf(res.motivo, sizeof res.motivo, "fase %d: estado proibido %s aos %lus", f + 1,
                   vg::nomeEstado(sd.estado), (unsigned long)t);
        }
        res.aprovado = false; res.falhas++;
      }
      if (F.esperadoFim >= 0 && (int)sd.estado == F.esperadoFim && !viuEsperado) {
        viuEsperado = true; res.tDeteccao_s = t;
      }
      if (reg) {
        Amostra a{t, F.iA, iMed, cabo.T, tP, tA, sd.dtC, tv ? taxa : NAN, (int)sd.estado};
        reg(a, ctx);
      }
      estadoAnt = (int)sd.estado;
    }
    if (F.esperadoFim >= 0 && estadoAnt != F.esperadoFim) {
      if (res.aprovado)
        snprintf(res.motivo, sizeof res.motivo, "fase %d: esperado %s, obtido %s", f + 1,
                 vg::nomeEstado((vg::Estado)F.esperadoFim), vg::nomeEstado((vg::Estado)estadoAnt));
      res.aprovado = false; res.falhas++;
    }
  }
  if (res.aprovado) snprintf(res.motivo, sizeof res.motivo, "ok");
  return res;
}

// ------------------------- Roteiro padrao (VG-PE-05) -------------------------
// Configuracao de demonstracao: limite 5 A, confirmacoes de 10 s (secao 7 do VG-PE-05)
inline vg::Config configDemo(float kTermico) {
  vg::Config c;
  c.iLimiteA = 5.0f;
  c.tConfirmaSobrecargaMs = 10000;
  c.tConfirmaMauContatoMs = 10000;
  c.tLiberaMs = 5000;
  c.kTermico = kTermico;
  return c;
}

using vg::NORMAL; using vg::AQUECIMENTO_EXTERNO; using vg::ALERTA_TEMPERATURA;
using vg::ALERTA_PREVENTIVO; using vg::MAU_CONTATO; using vg::SOBRECARGA; using vg::FALHA_SENSOR;

//                         dur   I     extraK fonte  falha  esperado            proibido
static const Fase F_C1[] = {{60, 0.0f, 0, 0, false, -1, -1},
                            {120, 2.0f, 0, 0, false, NORMAL, ALERTA_PREVENTIVO}};
static const Fase F_C2[] = {{60, 0.0f, 0, 0, false, -1, -1},
                            {25, 8.0f, 0, 0, false, ALERTA_PREVENTIVO, SOBRECARGA}};
static const Fase F_C3[] = {{60, 0.0f, 0, 0, false, -1, -1},
                            {90, 8.0f, 0, 70.0f, false, SOBRECARGA, -1}};
static const Fase F_C4[] = {{60, 0.0f, 0, 0, false, -1, -1},
                            {400, 4.0f, 1.50f, 0, false, MAU_CONTATO, SOBRECARGA}};
static const Fase F_C5[] = {{60, 0.0f, 0, 0, false, -1, -1},
                            {150, 0.0f, 0, 60.0f, false, AQUECIMENTO_EXTERNO, MAU_CONTATO}};
static const Fase F_C6[] = {{60, 2.0f, 0, 0, false, NORMAL, -1},
                            {20, 2.0f, 0, 0, true, FALHA_SENSOR, -1},
                            {30, 2.0f, 0, 0, false, NORMAL, -1}};
static const Fase F_C7[] = {{60, 0.0f, 0, 0, false, -1, -1},
                            {90, 8.0f, 0, 70.0f, false, SOBRECARGA, -1},
                            {900, 0.0f, 0, 0, false, NORMAL, -1}};

static const Cenario CENARIOS[] = {
  {"C1", "Normal (2 A)", F_C1, 2},
  {"C2", "Corrente alta sem resposta termica (8 A)", F_C2, 2},
  {"C3", "Sobrecarga (8 A e ar quente na sonda)", F_C3, 2},
  {"C4", "Mau contato emulado (4 A, aquecimento anormal)", F_C4, 2},
  {"C5", "Aquecimento externo sem corrente", F_C5, 2},
  {"C6", "Falha e reconexao da sonda de ambiente", F_C6, 3},
  {"C7", "Sobrecarga seguida de resfriamento", F_C7, 3},
};
static const int N_CENARIOS = sizeof(CENARIOS) / sizeof(CENARIOS[0]);

// Estabilidade: corrente oscilando em torno do limite durante 120 s.
// Retorna o numero de trocas de estado ocorridas DURANTE a oscilacao.
struct CtxTrocas { int ant; int trocas; uint32_t t0; };
inline void contaTrocas(const Amostra& a, void* p) {
  CtxTrocas* c = (CtxTrocas*)p;
  if (a.t_s > c->t0 && c->ant >= 0 && a.estado != c->ant) c->trocas++;
  c->ant = a.estado;
}
inline int ensaioEstabilidade(const vg::Config& cfg, uint32_t seed, Registrador extra = nullptr, void* ctxExtra = nullptr) {
  static Fase f[121];
  f[0] = {60, 0.0f, 0, 0, false, -1, -1};
  for (int k = 1; k <= 120; k++) f[k] = {1, (k % 2) ? 5.3f : 4.8f, 0, 0, false, -1, -1};
  Cenario c{"E7", "Estabilidade", f, 121};
  CtxTrocas ct{-1, 0, 60};
  (void)extra; (void)ctxExtra;
  executa(c, cfg, seed, contaTrocas, &ct);
  return ct.trocas;
}

// Exatidao: media de nJan janelas para a corrente dada. Retorna corrente medida media.
inline float mede(float iA, int espiras, const ModeloAdc& m, const vg::Config& cfg, int nJan, uint32_t seed,
                  bool* foraFaixa = nullptr) {
  static uint16_t buf[VGB_N_AMOSTRAS + 4];
  Rng r(seed);
  double soma = 0; bool ff = false;
  for (int j = 0; j < nJan; j++) {
    geraJanela(buf, VGB_N_AMOSTRAS, VGB_TS, iA, espiras, m, r);
    vg::ResultadoRms rr = vg::calculaRms(buf, VGB_N_AMOSTRAS, cfg);
    soma += rr.iRmsA; ff |= rr.foraFaixa;
  }
  if (foraFaixa) *foraFaixa = ff;
  return (float)(soma / nJan);
}

}  // namespace vgb
