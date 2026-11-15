#pragma once
#define WL_CONNECTED 3
#define WIFI_STA 1
struct WiFiClient{}; struct WiFiT{int status(){return WL_CONNECTED;} void begin(const char*,const char*){} void mode(int){}}; inline WiFiT WiFi;
