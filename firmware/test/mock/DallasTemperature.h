#pragma once
#include "OneWire.h"
#include <cstring>
typedef uint8_t DeviceAddress[8];
inline float g_t[2]={36.0f,33.0f};
struct DallasTemperature{ DallasTemperature(OneWire*){}
 void begin(){} int getDeviceCount(){return 2;}
 bool getAddress(uint8_t*a,int i){memset(a,i+0x28,8);return true;}
 void setResolution(const uint8_t*,int){} void setWaitForConversion(bool){} void requestTemperatures(){}
 float getTempC(const uint8_t*a){return g_t[a[0]==0x28?0:1];} };
