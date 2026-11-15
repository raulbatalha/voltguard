// =====================================================================
//  VoltGuard - nucleo de processamento (C++ puro, sem dependencia de hardware)
//  Rev. B - incorpora as correcoes do parecer tecnico:
//    * corrente RMS por janela de ciclos inteiros, com piso de ruido
//      e deteccao de saida da faixa linear do ADC;
//    * elevacao de temperatura sobre o ambiente (dT = Tponto - Tamb);
//    * taxa de elevacao por regressao linear em janela (C/min);
//    * "mau contato" so com corrente presente (dT acima do esperado k*I^2);
//    * histerese e tempos de confirmacao/liberacao dos alarmes;
//    * tratamento de falha do DS18B20 (-127 C) e valor de reset (85 C).
//  Este arquivo compila tanto no ESP32 (Arduino) quanto no PC (testes).
// =====================================================================
#pragma once
#include <math.h>
#include <stdint.h>

namespace vg {

// ------------------------------- Parametros -------------------------------
struct Config {
  // --- Sensor de corrente ---
  float sctAmperePorVolt = 30.0f;  // SCT-013-030: 30 A eficazes -> 1 V eficaz
  int   nEspiras         = 1;      // voltas do condutor dentro do nucleo
  float calibracao       = 1.000f; // ajuste fino contra alicate amperimetro
  float pisoRuidoA       = 0.15f;  // abaixo disso a corrente e considerada zero
  uint16_t adcMin_mV     = 150;    // faixa linear do ADC (atenuacao 11 dB)
  uint16_t adcMax_mV     = 2450;

  // --- Limites de diagnostico (ajustar ao condutor monitorado) ---
  float iLimiteA          = 8.0f;   // corrente de alerta
  float iMinimaA          = 1.0f;   // corrente minima para avaliar mau contato
  float dtLimiteC         = 25.0f;  // elevacao maxima sobre o ambiente
  float tAbsMaxC          = 60.0f;  // temperatura absoluta critica no ponto
  float taxaLimiteCmin    = 1.0f;   // taxa de elevacao critica (C/min)
  float kTermico          = 0.10f;  // dT esperado = k * I^2 (C/A^2) - levantar em ensaio
  float margemMauContatoC = 8.0f;   // excesso de dT sobre o esperado
  float histerese         = 0.90f;  // condicao libera abaixo de 90% do limite

  uint32_t tConfirmaSobrecargaMs = 30000;   // corrente alta + resposta termica
  uint32_t tSobrecargaLongaMs    = 300000;  // corrente alta mantida (5 min)
  uint32_t tConfirmaMauContatoMs = 60000;
  uint32_t tLiberaMs             = 10000;   // estado so "melhora" apos 10 s estavel
};

// ------------------------------- Corrente RMS -------------------------------
struct ResultadoRms {
  float media_mV;   // nivel medio (referencia do divisor)
  float vRms_mV;    // tensao eficaz do SCT (sem o nivel medio)
  float iRmsA;      // corrente eficaz no condutor
  bool  foraFaixa;  // alguma amostra fora da faixa linear do ADC
  int   n;
};

// amostras em mV (analogReadMilliVolts), cobrindo numero inteiro de ciclos
inline ResultadoRms calculaRms(const uint16_t* a, int n, const Config& c) {
  ResultadoRms r{0, 0, 0, false, n};
  if (n < 10) return r;
  double soma = 0;
  for (int k = 0; k < n; k++) {
    soma += a[k];
    if (a[k] < c.adcMin_mV || a[k] > c.adcMax_mV) r.foraFaixa = true;
  }
  const double media = soma / n;
  double q = 0;
  for (int k = 0; k < n; k++) { const double d = a[k] - media; q += d * d; }
  r.media_mV = (float)media;
  r.vRms_mV  = (float)sqrt(q / n);
  float i = (r.vRms_mV / 1000.0f) * c.sctAmperePorVolt * c.calibracao
            / (float)(c.nEspiras < 1 ? 1 : c.nEspiras);
  r.iRmsA = (i < c.pisoRuidoA) ? 0.0f : i;
  return r;
}

// --------------------------- Validacao do DS18B20 ---------------------------
// Retorna true se a leitura e aceitavel.
//  -127 C  -> sensor desconectado (DallasTemperature: DEVICE_DISCONNECTED_C)
//    85 C  -> valor de reset; rejeitado se for a 1a leitura ou salto > 20 C
inline bool temperaturaValida(float novo, float anterior, bool temAnterior) {
  if (isnan(novo) || novo <= -55.0f || novo > 125.0f) return false;
  if (novo == 85.0f && (!temAnterior || fabsf(novo - anterior) > 20.0f)) return false;
  return true;
}

// --------------------- Taxa de elevacao (regressao linear) ---------------------
template <int N>
class Tendencia {
 public:
  void adiciona(uint32_t tMs, float valor) {
    t_[pos_] = tMs; v_[pos_] = valor;
    pos_ = (pos_ + 1) % N; if (cont_ < N) cont_++;
  }
  void limpa() { cont_ = 0; pos_ = 0; }
  // inclinacao em unidades por minuto; valido=false se poucos pontos/janela curta
  float porMinuto(bool& valido, uint32_t janelaMinMs = 30000) const {
    valido = false;
    if (cont_ < 5) return 0;
    int ini = (pos_ - cont_ + N) % N;
    uint32_t t0 = t_[ini];
    uint32_t tUlt = t_[(pos_ - 1 + N) % N];
    if (tUlt - t0 < janelaMinMs) return 0;
    double sx = 0, sy = 0, sxx = 0, sxy = 0;
    for (int k = 0; k < cont_; k++) {
      int j = (ini + k) % N;
      double x = (t_[j] - t0) / 60000.0;  // minutos
      double y = v_[j];
      sx += x; sy += y; sxx += x * x; sxy += x * y;
    }
    double den = cont_ * sxx - sx * sx;
    if (fabs(den) < 1e-12) return 0;
    valido = true;
    return (float)((cont_ * sxy - sx * sy) / den);
  }
  int contagem() const { return cont_; }
 private:
  uint32_t t_[N] = {0};
  float v_[N] = {0};
  int pos_ = 0, cont_ = 0;
};

// --------------------------------- Diagnostico ---------------------------------
enum Estado : uint8_t {
  NORMAL = 0,
  AQUECIMENTO_EXTERNO,   // ponto quente sem corrente: calor nao vem do circuito
  ALERTA_TEMPERATURA,    // dT alto com corrente, sem caracterizar mau contato
  ALERTA_PREVENTIVO,     // corrente acima do limite, ainda sem resposta termica
  MAU_CONTATO,           // dT muito acima do esperado para a corrente medida
  SOBRECARGA,            // corrente alta confirmada com resposta termica
  FALHA_SENSOR
};

inline const char* nomeEstado(Estado e) {
  switch (e) {
    case NORMAL:              return "NORMAL";
    case AQUECIMENTO_EXTERNO: return "AQUECIMENTO EXTERNO";
    case ALERTA_TEMPERATURA:  return "ALERTA DE TEMPERATURA";
    case ALERTA_PREVENTIVO:   return "ALERTA PREVENTIVO";
    case MAU_CONTATO:         return "POSSIVEL MAU CONTATO";
    case SOBRECARGA:          return "SOBRECARGA";
    case FALHA_SENSOR:        return "FALHA DE SENSOR";
  }
  return "?";
}

// 0 = normal, 1 = atencao, 2 = critico, 3 = falha
inline uint8_t severidade(Estado e) {
  switch (e) {
    case NORMAL: return 0;
    case AQUECIMENTO_EXTERNO: case ALERTA_TEMPERATURA: case ALERTA_PREVENTIVO: return 1;
    case MAU_CONTATO: case SOBRECARGA: return 2;
    case FALHA_SENSOR: return 3;
  }
  return 0;
}

struct Entradas {
  uint32_t tMs;
  float iA;          // corrente eficaz
  float tPontoC;     // temperatura no ponto monitorado
  float tAmbC;       // temperatura ambiente (2o DS18B20)
  float taxaCmin;    // taxa de elevacao de dT (C/min)
  bool  taxaValida;
  bool  sensoresOk;  // ambos os DS18B20 com leitura valida
};

struct Saida {
  Estado estado;
  float dtC;            // elevacao sobre o ambiente
  float dtEsperadoC;    // k * I^2
  float excessoC;       // dt - dtEsperado
  bool  mudou;          // estado mudou neste ciclo
};

class Diagnostico {
 public:
  explicit Diagnostico(const Config& c) : c_(c) {}

  Saida atualiza(const Entradas& e) {
    Saida s{estado_, 0, 0, 0, false};
    Estado candidato;

    if (!e.sensoresOk) {
      candidato = FALHA_SENSOR;
      resetaTimers();
    } else {
      s.dtC = e.tPontoC - e.tAmbC;
      s.dtEsperadoC = c_.kTermico * e.iA * e.iA;
      s.excessoC = s.dtC - s.dtEsperadoC;

      // condicoes com histerese
      correnteAlta_ = histe(correnteAlta_, e.iA, c_.iLimiteA);
      const bool dtAltoNovo = histe(dtAlto_, s.dtC, c_.dtLimiteC);
      const bool absAltoNovo = histe(absAlto_, e.tPontoC, c_.tAbsMaxC);
      dtAlto_ = dtAltoNovo; absAlto_ = absAltoNovo;
      const bool termicoAlto = dtAlto_ || absAlto_;
      taxaAlta_ = e.taxaValida && histe(taxaAlta_, e.taxaCmin, c_.taxaLimiteCmin);
      mauContatoCond_ = (e.iA >= c_.iMinimaA) &&
                        histe(mauContatoCond_, s.excessoC, c_.margemMauContatoC);

      marca(correnteAlta_, tCorrenteAlta_, e.tMs);
      marca(mauContatoCond_, tMauContato_, e.tMs);

      const uint32_t durCorr = correnteAlta_ ? e.tMs - tCorrenteAlta_ : 0;
      const uint32_t durMC   = mauContatoCond_ ? e.tMs - tMauContato_ : 0;

      if (correnteAlta_ && ((durCorr >= c_.tConfirmaSobrecargaMs && (termicoAlto || taxaAlta_)) ||
                            durCorr >= c_.tSobrecargaLongaMs))
        candidato = SOBRECARGA;
      else if (mauContatoCond_ && durMC >= c_.tConfirmaMauContatoMs)
        candidato = MAU_CONTATO;
      else if (correnteAlta_)
        candidato = ALERTA_PREVENTIVO;
      else if (termicoAlto && e.iA < c_.iMinimaA)
        candidato = AQUECIMENTO_EXTERNO;
      else if (termicoAlto || taxaAlta_ || mauContatoCond_)
        candidato = ALERTA_TEMPERATURA;  // inclui excesso termico ainda nao confirmado
      else
        candidato = NORMAL;
    }

    // piora imediatamente; melhora so apos tLibera estavel
    if (candidato == estado_) {
      tCandidato_ = 0; temCandidato_ = false;
    } else if (severidade(candidato) >= severidade(estado_) || estado_ == FALHA_SENSOR) {
      estado_ = candidato; s.mudou = true; temCandidato_ = false;
    } else {
      if (!temCandidato_ || candidatoAtual_ != candidato) {
        candidatoAtual_ = candidato; tCandidato_ = e.tMs; temCandidato_ = true;
      } else if (e.tMs - tCandidato_ >= c_.tLiberaMs) {
        estado_ = candidato; s.mudou = true; temCandidato_ = false;
      }
    }
    s.estado = estado_;
    return s;
  }

  Estado estado() const { return estado_; }

 private:
  bool histe(bool atual, float valor, float limite) const {
    return atual ? (valor > limite * c_.histerese) : (valor > limite);
  }
  static void marca(bool cond, uint32_t& t0, uint32_t agora) {
    if (!cond) t0 = 0; else if (t0 == 0) t0 = agora ? agora : 1;
  }
  void resetaTimers() {
    tCorrenteAlta_ = tMauContato_ = 0;
    correnteAlta_ = dtAlto_ = absAlto_ = taxaAlta_ = mauContatoCond_ = false;
  }

  const Config& c_;
  Estado estado_ = NORMAL;
  bool correnteAlta_ = false, dtAlto_ = false, absAlto_ = false, taxaAlta_ = false,
       mauContatoCond_ = false;
  uint32_t tCorrenteAlta_ = 0, tMauContato_ = 0;
  bool temCandidato_ = false;
  Estado candidatoAtual_ = NORMAL;
  uint32_t tCandidato_ = 0;
};

}  // namespace vg
