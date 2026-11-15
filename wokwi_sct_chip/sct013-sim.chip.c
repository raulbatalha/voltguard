// =====================================================================
//  Chip personalizado do Wokwi: SCT-013-030 + divisor de referencia
//  Entrega no pino OUT a tensao que chegaria ao GPIO34 do ESP32:
//      v(t) = VREF + (I / 30) * sqrt(2) * sen(2*pi*60*t)
//  O Wokwi nao simula circuitos analogicos (divisor, capacitores), por isso
//  o chip ja entrega o sinal final. Controles: corrente (A) e vref (V).
// =====================================================================
#include "wokwi-api.h"
#include <math.h>
#include <stdlib.h>

#define PI_F 3.14159265f

typedef struct {
  pin_t out;
  uint32_t attr_corrente;
  uint32_t attr_vref;
} chip_state_t;

static void atualiza(void *user_data) {
  chip_state_t *chip = (chip_state_t *)user_data;
  double t = (double)get_sim_nanos() * 1e-9;
  float i = attr_read_float(chip->attr_corrente);
  float vref = attr_read_float(chip->attr_vref);
  float v = vref + (i / 30.0f) * 1.41421356f * sinf(2.0f * PI_F * 60.0f * (float)fmod(t, 1.0));
  if (v < 0.0f) v = 0.0f;
  if (v > 3.3f) v = 3.3f;
  pin_dac_write(chip->out, v);
}

void chip_init(void) {
  chip_state_t *chip = malloc(sizeof(chip_state_t));
  chip->out = pin_init("OUT", ANALOG);
  chip->attr_corrente = attr_init_float("corrente", 0.0f);
  chip->attr_vref = attr_init_float("vref", 1.32f);
  const timer_config_t config = { .callback = atualiza, .user_data = chip };
  timer_t timer = timer_init(&config);
  timer_start(timer, 100, true);   // atualiza a cada 100 us (10 kHz)
}
