// Executa o sketch no PC com hardware simulado: 2 min com 10 A e aquecimento
#include "Arduino.h"
#include "DallasTemperature.h"
void setup(); void loop();
int main(){ setup();
 for(int s=0;s<200;s++){ for(int k=0;k<20;k++){ loop(); g_ms+=50; }
   g_pot = s<20 ? 0 : 2200;                       // 0 A e depois 10 A (sim.)
   if(s>=20) g_t[0]=36.0f+ (s-20)*0.2f;           // ponto aquece 12 C/min
   if(s!=0 && s%40!=0) continue; }
 return 0; }
