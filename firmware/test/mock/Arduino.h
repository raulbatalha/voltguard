#pragma once
#include <cstring>
#include <cstdint>
#include <cstdio>
#include <cstdarg>
#include <cmath>
#include <cstdlib>
#define PI 3.14159265358979f
#define OUTPUT 1
#define ADC_11db 3
typedef uint8_t byte;
inline uint32_t g_ms=0, g_us=0;
inline uint32_t millis(){return g_ms;}
#include <cstring>
inline uint32_t micros(){return g_us+=50;}
inline void delay(uint32_t d){g_ms+=d;}
inline uint32_t g_pot=1650; inline uint32_t analogReadMilliVolts(int){return g_pot;}
inline void analogReadResolution(int){} inline void analogSetPinAttenuation(int,int){}
inline void pinMode(int,int){} inline void digitalWrite(int,int){}
inline void tone(int,int){} inline void noTone(int){}
inline long random(long a,long b){return a+rand()%(b-a);}
template<class T> T constrain(T x,T a,T b){return x<a?a:(x>b?b:x);}
#define HEX 16
struct SerialT{ void begin(int){} void println(const char*s=""){puts(s);} void print(const char*s){fputs(s,stdout);}
 void print(char c){putchar(c);} void print(int v,int b){printf(b==16?"%X":"%d",v);}
 int printf(const char*f,...){va_list a;va_start(a,f);int r=vprintf(f,a);va_end(a);return r;} };
inline SerialT Serial;
struct EspT{ uint64_t getEfuseMac(){return 0xA1B2C3D4E5F6ULL;} }; inline EspT ESP;
