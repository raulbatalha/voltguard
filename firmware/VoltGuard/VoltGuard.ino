// =====================================================================
//  VoltGuard - firmware do prototipo (ESP32-DevKitC V4) - Rev. B
//  Monitoramento de corrente (SCT-013-030) e temperatura (2x DS18B20)
//
//  Bibliotecas (Gerenciador de Bibliotecas da Arduino IDE):
//    OneWire, DallasTemperature, PubSubClient (somente se USAR_MQTT = 1)
//  Placa: "ESP32 Dev Module" (pacote esp32 by Espressif Systems)
//
//  Ligacoes (ver desenho VG-DE-01):
//    GPIO34 <- R4 1k <- ponta (tip) do SCT; corpo (sleeve) do SCT -> VREF 1,32 V
//    GPIO4  <-> barramento OneWire (DS18B20 ponto + ambiente), pull-up 4,7k
//    GPIO25 LED verde | GPIO26 LED amarelo | GPIO27 LED vermelho
//    GPIO13 -> R 1k -> base do BC547 -> buzzer ativo 5 V
// =====================================================================
#include <OneWire.h>
#include <DallasTemperature.h>
#include "voltguard_core.h"

// ------------------------------ Opcoes de compilacao ------------------------------
#ifndef MODO_SIMULACAO
#define MODO_SIMULACAO 0  // 1 = Wokwi: potenciometro no GPIO34 define a corrente simulada
#endif
#ifndef USAR_MQTT
#define USAR_MQTT 0       // 1 = publica telemetria e alertas por Wi-Fi/MQTT
#endif

#if USAR_MQTT
#include <WiFi.h>
#include <PubSubClient.h>
const char* WIFI_SSID   = "Wokwi-GUEST";   // trocar pela rede local
const char* WIFI_SENHA  = "";
const char* MQTT_BROKER = "broker.hivemq.com";
const uint16_t MQTT_PORTA = 1883;
WiFiClient wifiCli;
PubSubClient mqtt(wifiCli);
char topicoBase[40];
#endif

// ------------------------------------ Pinos ------------------------------------
const int PIN_SCT    = 34;  // ADC1 - funciona com Wi-Fi ligado
const int PIN_1WIRE  = 4;   // GPIO2 evitado (strapping)
const int PIN_LED_OK = 25;
const int PIN_LED_AL = 26;
const int PIN_LED_CR = 27;
const int PIN_BUZZER = 13;

// ----------------------------- Aquisicao da corrente -----------------------------
const float    FREQ_REDE_HZ = 60.0f;   // rede brasileira
const int      CICLOS       = 10;      // janela de 10 ciclos = 166,7 ms
const uint32_t T_AMOSTRA_US = 200;     // 5 kSa/s
const int      N_AMOSTRAS   = (int)(CICLOS * 1e6f / FREQ_REDE_HZ / T_AMOSTRA_US);  // 833
uint16_t amostras[N_AMOSTRAS + 4];

vg::Config cfg;
vg::Diagnostico diag(cfg);
vg::Tendencia<32> tendDt;   // 32 pontos x 5 s = 160 s de janela

OneWire oneWire(PIN_1WIRE);
DallasTemperature ds(&oneWire);
DeviceAddress endPonto, endAmb;
bool temPonto = false, temAmb = false;
float tPonto = NAN, tAmb = NAN;
bool  tPontoOk = false, tAmbOk = false;

float iRms = 0;
bool  adcForaFaixa = false;
int   descartesIniciais = 3;   // aguarda estabilizar C1 e o calculo
vg::Saida ultima{};

// --------------------------------------------------------------------------------
#if MODO_SIMULACAO
// O Wokwi nao possui SCT. O potenciometro (0-3,3 V) define a corrente eficaz
// simulada (0 a 15 A) e o firmware sintetiza a senoide de 60 Hz que o SCT
// entregaria, passando-a pelo MESMO calculo RMS usado no prototipo real.
const float I_SIM_MAX_A = 15.0f;
const float VREF_SIM_mV = 1320.0f;
void adquireJanela() {
  uint32_t pot = analogReadMilliVolts(PIN_SCT);
  float iSet = I_SIM_MAX_A * (pot / 3300.0f);
  float amp = iSet * cfg.nEspiras / cfg.sctAmperePorVolt * 1000.0f * 1.41421f;
  for (int k = 0; k < N_AMOSTRAS; k++) {
    float t = k * T_AMOSTRA_US * 1e-6f;
    float v = VREF_SIM_mV + amp * sinf(2.0f * PI * FREQ_REDE_HZ * t) + (float)random(-3, 4);
    amostras[k] = (uint16_t)constrain(v, 0.0f, 3100.0f);
  }
}
#else
void adquireJanela() {
  uint32_t prox = micros();
  for (int k = 0; k < N_AMOSTRAS; k++) {
    while ((int32_t)(micros() - prox) < 0) { }
    amostras[k] = analogReadMilliVolts(PIN_SCT);  // usa calibracao de fabrica (eFuse)
    prox += T_AMOSTRA_US;
  }
}
#endif

void medeCorrente() {
  adquireJanela();
  vg::ResultadoRms r = vg::calculaRms(amostras, N_AMOSTRAS, cfg);
  if (descartesIniciais > 0) { descartesIniciais--; return; }
  iRms = r.iRmsA;
  adcForaFaixa = r.foraFaixa;
}

// ------------------------------- Temperatura -------------------------------
void imprimeEndereco(const DeviceAddress a) {
  for (int i = 0; i < 8; i++) { if (a[i] < 16) Serial.print('0'); Serial.print(a[i], HEX); }
}

void iniciaTemperatura() {
  ds.begin();
  int n = ds.getDeviceCount();
  Serial.printf("DS18B20 encontrados: %d\n", n);
  // Convencao: indice 0 = ponto monitorado, indice 1 = ambiente.
  // Se ficar invertido, troque os cabos ou inverta os indices abaixo.
  temPonto = ds.getAddress(endPonto, 0);
  temAmb   = ds.getAddress(endAmb, 1);
  if (temPonto) { Serial.print("  ponto   : "); imprimeEndereco(endPonto); Serial.println(); ds.setResolution(endPonto, 12); }
  if (temAmb)   { Serial.print("  ambiente: "); imprimeEndereco(endAmb);   Serial.println(); ds.setResolution(endAmb, 12); }
  ds.setWaitForConversion(false);  // conversao de 750 ms sem bloquear o loop
  ds.requestTemperatures();
}

void leTemperaturas() {
  if (temPonto) {
    float v = ds.getTempC(endPonto);
    tPontoOk = vg::temperaturaValida(v, tPonto, !isnan(tPonto));
    if (tPontoOk) tPonto = v;
  } else tPontoOk = false;
  if (temAmb) {
    float v = ds.getTempC(endAmb);
    tAmbOk = vg::temperaturaValida(v, tAmb, !isnan(tAmb));
    if (tAmbOk) tAmb = v;
  } else tAmbOk = false;
  ds.requestTemperatures();  // pede a proxima conversao
}

// ------------------------------- Sinalizacao -------------------------------
void sinaliza(vg::Estado e, uint32_t agora) {
  uint8_t sev = vg::severidade(e);
  bool pisca = (agora / 500) % 2;
  digitalWrite(PIN_LED_OK, sev == 0);
  digitalWrite(PIN_LED_AL, sev == 1 || (sev == 3 && pisca));
  digitalWrite(PIN_LED_CR, sev == 2);
  bool bip = (sev == 2) && pisca;
#if MODO_SIMULACAO
  if (bip) tone(PIN_BUZZER, 2000); else noTone(PIN_BUZZER);
#else
  digitalWrite(PIN_BUZZER, bip);   // buzzer ativo via transistor
#endif
}

// ----------------------------------- MQTT -----------------------------------
#if USAR_MQTT
void cuidaRede(uint32_t agora) {
  static uint32_t tTentativa = 0;
  if (WiFi.status() != WL_CONNECTED) {
    if (agora - tTentativa > 10000) { tTentativa = agora; WiFi.begin(WIFI_SSID, WIFI_SENHA); }
    return;
  }
  if (!mqtt.connected()) {
    if (agora - tTentativa > 5000) {
      tTentativa = agora;
      char id[24]; snprintf(id, sizeof id, "voltguard-%06lX", (unsigned long)(ESP.getEfuseMac() & 0xFFFFFF));
      mqtt.connect(id);
    }
    return;
  }
  mqtt.loop();
}
void publica(const vg::Saida& s, bool alerta) {
  if (!mqtt.connected()) return;
  char js[200], top[64];
  snprintf(js, sizeof js,
           "{\"i\":%.2f,\"tp\":%.2f,\"ta\":%.2f,\"dt\":%.2f,\"estado\":\"%s\",\"sev\":%u}",
           iRms, tPonto, tAmb, s.dtC, vg::nomeEstado(s.estado), vg::severidade(s.estado));
  snprintf(top, sizeof top, "%s/%s", topicoBase, alerta ? "alerta" : "telemetria");
  mqtt.publish(top, js, alerta);
}
#endif

// --------------------------------- setup/loop ---------------------------------
void setup() {
  Serial.begin(115200);
  delay(300);  // C1 (10 uF) carrega em ~250 ms
  Serial.println("\nVoltGuard Rev. B");
  pinMode(PIN_LED_OK, OUTPUT); pinMode(PIN_LED_AL, OUTPUT);
  pinMode(PIN_LED_CR, OUTPUT); pinMode(PIN_BUZZER, OUTPUT);
  analogReadResolution(12);
  analogSetPinAttenuation(PIN_SCT, ADC_11db);
  iniciaTemperatura();
  Serial.printf("Janela: %d amostras (%d ciclos de %.0f Hz)\n", N_AMOSTRAS, CICLOS, FREQ_REDE_HZ);
  Serial.printf("Limites: I=%.1f A | dT=%.1f C | Tabs=%.1f C | taxa=%.1f C/min | k=%.3f C/A2\n",
                cfg.iLimiteA, cfg.dtLimiteC, cfg.tAbsMaxC, cfg.taxaLimiteCmin, cfg.kTermico);
#if USAR_MQTT
  snprintf(topicoBase, sizeof topicoBase, "voltguard/%06lX", (unsigned long)(ESP.getEfuseMac() & 0xFFFFFF));
  mqtt.setServer(MQTT_BROKER, MQTT_PORTA);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_SENHA);
  Serial.printf("MQTT: topico %s/telemetria e %s/alerta\n", topicoBase, topicoBase);
#endif
}

void loop() {
  static uint32_t tCorr = 0, tTemp = 0, tTend = 0, tDiag = 0, tPub = 0;
  uint32_t agora = millis();

  if (agora - tCorr >= 500)  { tCorr = agora; medeCorrente(); }
  if (agora - tTemp >= 1000) { tTemp = agora; leTemperaturas(); }
  if (agora - tTend >= 5000 && tPontoOk && tAmbOk) { tTend = agora; tendDt.adiciona(agora, tPonto - tAmb); }

  if (agora - tDiag >= 1000) {
    tDiag = agora;
    bool taxaOk; float taxa = tendDt.porMinuto(taxaOk);
    vg::Entradas e{agora, iRms, tPonto, tAmb, taxa, taxaOk, tPontoOk && tAmbOk};
    ultima = diag.atualiza(e);

    Serial.printf("I=%6.2f A%s | Tponto=%6.2f C | Tamb=%6.2f C | dT=%5.2f C (esperado %4.1f) | taxa=%s%5.2f C/min | %s\n",
                  iRms, adcForaFaixa ? "*" : " ", tPonto, tAmb, ultima.dtC, ultima.dtEsperadoC,
                  taxaOk ? "" : "~", taxa, vg::nomeEstado(ultima.estado));
    if (adcForaFaixa) Serial.println("  * sinal fora da faixa linear do ADC: corrente subestimada");
    if (ultima.mudou) Serial.printf(">>> MUDANCA DE ESTADO: %s\n", vg::nomeEstado(ultima.estado));
#if USAR_MQTT
    if (ultima.mudou) publica(ultima, true);
#endif
  }
#if USAR_MQTT
  cuidaRede(agora);
  if (agora - tPub >= 5000) { tPub = agora; publica(ultima, false); }
#else
  (void)tPub;
#endif
  sinaliza(ultima.estado, agora);
}
