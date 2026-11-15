#pragma once
#include <cstdio>
#include "WiFi.h"
struct PubSubClient{ PubSubClient(WiFiClient&){} bool c=false; bool connected(){return c;} bool connect(const char*){c=true;return true;}
 void loop(){} void setServer(const char*,int){} bool publish(const char*t,const char*p,bool r){printf("[MQTT %s%s] %s\n",t,r?" retido":"",p);return true;} };
