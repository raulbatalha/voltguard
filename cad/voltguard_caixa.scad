// =====================================================================
//  VoltGuard - Caixa do prototipo para impressao 3D (Rev. B)
//  Desenho tecnico: VG-DM-03 (base) e VG-DM-04 (tampa)
//  Unidade: mm | Material recomendado: PETG (ou ABS/ASA)
//  Gerar STL:  openscad -D 'parte="base"' -o base.stl voltguard_caixa.scad
//              openscad -D 'parte="tampa"' -o tampa.stl voltguard_caixa.scad
// =====================================================================
parte = "montagem";  // "base" | "tampa" | "montagem"

// ------------------------------ Parametros gerais ------------------------------
parede   = 2.5;     // espessura das paredes
fundo    = 2.5;     // espessura do fundo
iL = 100; iW = 60; iH = 30;          // dimensoes internas (x, y, z)
eL = iL + 2*parede;                 // 105
eW = iW + 2*parede;                 // 65
eH = fundo + iH;                    // 32.5 (altura da base)
raio_ext = 3;                       // arredondamento das arestas verticais

// Tampa
tampa_e  = 3.0;     // espessura da tampa
aba_e    = 1.5;     // espessura da aba de encaixe
aba_h    = 4.0;     // profundidade da aba
folga    = 0.3;     // folga de encaixe por lado

// Torres de fixacao da tampa (parafuso M3 x 10 autoatarraxante)
torre_d   = 7.0;
torre_off = 4.0;    // centro a partir das paredes internas
furo_m3_rosca = 2.6;
furo_m3_pass  = 3.4;
csk_d         = 6.5; // escareado na tampa

// Placa perfurada 70 x 50 mm com furos de 2 mm a 2,5 mm das bordas (conferir)
pcb_L = 70; pcb_W = 50; pcb_x = 9; pcb_y = 5;  // posicao interna
pcb_furo_inset = 2.5;
espac_h = 5;  espac_d = 6;  furo_m2 = 2.2;

// Recortes (coordenadas absolutas da caixa)
usb_y = parede + pcb_y + 2 + 14;  usb_z = fundo + 18.2;  usb_w = 13; usb_h = 9;  // parede esquerda
pg7_d = 12.7; pg7_z = fundo + 15; pg7_y = [parede + 20, parede + 40];              // parede direita
p2_d  = 6.2;  p2_x  = parede + 83.5; p2_z = fundo + 15;                             // parede frontal
vent_n = 6; vent_w = 2; vent_h = 12; vent_x0 = 22; vent_passo = 7; vent_z0 = fundo + 8; // parede traseira

// Orelhas de fixacao em parede
orelha_L = 12; orelha_W = 24; orelha_e = 3; orelha_furo = 4.5; orelha_rasgo = 6;

// Sinalizacao na tampa
led_d = 5.2;  led_y = 46;  led_x = [24, 44, 64];  led_txt = ["OK", "ALERTA", "CRITICO"];
buz_x = 86;   buz_y = 44;  buz_d_int = 12.3;  buz_parede = 1.6;  buz_h = 5;
grav = 0.6;   // profundidade da gravacao

$fn = 64;

// ------------------------------------ Utilitarios ------------------------------------
module caixa_arred(L, W, H, r) {
  hull() for (x = [r, L - r], y = [r, W - r]) translate([x, y, 0]) cylinder(r = r, h = H);
}
torres_pos = [for (x = [parede + torre_off, eL - parede - torre_off],
                   y = [parede + torre_off, eW - parede - torre_off]) [x, y]];

// --------------------------------------- Base ---------------------------------------
module base() {
  difference() {
    union() {
      difference() {
        caixa_arred(eL, eW, eH, raio_ext);
        translate([parede, parede, fundo]) cube([iL, iW, iH + 1]);
      }
      // torres da tampa
      for (p = torres_pos) translate([p[0], p[1], 0]) cylinder(d = torre_d, h = eH);
      // espacadores da placa
      for (x = [pcb_x + pcb_furo_inset, pcb_x + pcb_L - pcb_furo_inset],
           y = [pcb_y + pcb_furo_inset, pcb_y + pcb_W - pcb_furo_inset])
        translate([parede + x, parede + y, 0]) cylinder(d = espac_d, h = fundo + espac_h);
      // orelhas
      for (lado = [0, 1]) orelha(lado);
    }
    // furos das torres (rosca M3 no plastico), 12 mm de profundidade
    for (p = torres_pos) translate([p[0], p[1], eH - 12]) cylinder(d = furo_m3_rosca, h = 13);
    // furos dos espacadores (M2 autoatarraxante)
    for (x = [pcb_x + pcb_furo_inset, pcb_x + pcb_L - pcb_furo_inset],
         y = [pcb_y + pcb_furo_inset, pcb_y + pcb_W - pcb_furo_inset])
      translate([parede + x, parede + y, 1.0]) cylinder(d = furo_m2, h = fundo + espac_h);
    // USB (parede esquerda)
    translate([-1, usb_y - usb_w/2, usb_z - usb_h/2]) cube([parede + 2, usb_w, usb_h]);
    // prensa-cabos PG7 (parede direita) - sondas DS18B20
    for (y = pg7_y) translate([eL - parede - 1, y, pg7_z]) rotate([0, 90, 0]) cylinder(d = pg7_d, h = parede + 2);
    // jaque P2 do SCT (parede frontal)
    translate([p2_x, -1, p2_z]) rotate([-90, 0, 0]) cylinder(d = p2_d, h = parede + 2);
    // ventilacao (parede traseira)
    for (i = [0 : vent_n - 1])
      translate([vent_x0 + i*vent_passo, eW - parede - 1, vent_z0]) cube([vent_w, parede + 2, vent_h]);
    // identificacao gravada nas paredes
    translate([p2_x, grav - 0.01, p2_z + 7]) rotate([90, 0, 0])
      linear_extrude(grav + 0.1) text("SCT", size = 4, halign = "center", font = "Liberation Sans:style=Bold");
    for (k = [0, 1]) translate([eL - grav + 0.01, pg7_y[k], pg7_z + 9.5]) rotate([90, 0, 90])
      linear_extrude(grav + 0.1) text(k == 0 ? "T-PONTO" : "T-AMB", size = 3, halign = "center", font = "Liberation Sans:style=Bold");
    translate([grav - 0.01, usb_y, usb_z + 6.5]) rotate([90, 0, -90])
      linear_extrude(grav + 0.1) text("USB 5V", size = 3, halign = "center", font = "Liberation Sans:style=Bold");
  }
}

module orelha(lado) {
  x0 = lado == 0 ? -orelha_L : eL;
  difference() {
    hull() {
      translate([lado == 0 ? 0 : eL - 1, eW/2 - orelha_W/2, 0]) cube([1, orelha_W, orelha_e]);
      for (s = [-1, 1])
        translate([lado == 0 ? -orelha_L + orelha_W/4 : eL + orelha_L - orelha_W/4, eW/2 + s*(orelha_W/2 - orelha_W/4), 0])
          cylinder(r = orelha_W/4, h = orelha_e);
    }
    hull() for (s = [-1, 1])
      translate([lado == 0 ? -orelha_L/2 : eL + orelha_L/2, eW/2 + s*orelha_rasgo/2, -1])
        cylinder(d = orelha_furo, h = orelha_e + 2);
  }
}

// --------------------------------------- Tampa ---------------------------------------
// Modelada na posicao de uso (face superior em z = tampa_e). Para imprimir,
// usar o STL "tampa", ja virado com a face superior apoiada na mesa.
module tampa_uso() {
  difference() {
    union() {
      caixa_arred(eL, eW, tampa_e, raio_ext);
      // aba de encaixe
      difference() {
        translate([parede + folga, parede + folga, -aba_h]) cube([iL - 2*folga, iW - 2*folga, aba_h]);
        translate([parede + folga + aba_e, parede + folga + aba_e, -aba_h - 1])
          cube([iL - 2*folga - 2*aba_e, iW - 2*folga - 2*aba_e, aba_h + 2]);
        for (p = torres_pos) translate([p[0], p[1], -aba_h - 1]) cylinder(d = torre_d + 2*folga + 0.6, h = aba_h + 1);
      }
      // porta-buzzer
      translate([buz_x, buz_y, -buz_h]) difference() {
        cylinder(d = buz_d_int + 2*buz_parede, h = buz_h);
        translate([0, 0, -1]) cylinder(d = buz_d_int, h = buz_h + 1);
      }
    }
    // furos dos parafusos com escareado
    for (p = torres_pos) translate([p[0], p[1], -1]) {
      cylinder(d = furo_m3_pass, h = tampa_e + 2);
      translate([0, 0, tampa_e + 1 - (csk_d - furo_m3_pass)/2]) cylinder(d1 = furo_m3_pass, d2 = csk_d, h = (csk_d - furo_m3_pass)/2 + 0.01);
    }
    // LEDs
    for (x = led_x) translate([x, led_y, -1]) cylinder(d = led_d, h = tampa_e + 2);
    // furos de som do buzzer
    translate([buz_x, buz_y, -1]) {
      cylinder(d = 2, h = tampa_e + 2);
      for (a = [0 : 60 : 300]) rotate(a) translate([3.2, 0, 0]) cylinder(d = 1.8, h = tampa_e + 2);
    }
    // gravacoes
    translate([0, 0, tampa_e - grav]) linear_extrude(grav + 0.1) {
      translate([eL/2, 26]) text("VOLTGUARD", size = 9, halign = "center", valign = "center", font = "Liberation Sans:style=Bold");
      translate([eL/2, 14]) text("MONITOR DE CORRENTE E TEMPERATURA", size = 2.6, halign = "center", valign = "center", font = "Liberation Sans:style=Bold");
      for (i = [0 : 2]) translate([led_x[i], led_y + 6.5]) text(led_txt[i], size = 3, halign = "center", valign = "center", font = "Liberation Sans:style=Bold");
      translate([buz_x, buz_y + 9.5]) text("ALARME", size = 3, halign = "center", valign = "center", font = "Liberation Sans:style=Bold");
    }
  }
}

module tampa_impressao() { translate([0, eW, tampa_e]) rotate([180, 0, 0]) tampa_uso(); }

// ------------------------------------- Selecao -------------------------------------
if (parte == "base") base();
else if (parte == "tampa") tampa_impressao();
else if (parte == "tampa_uso") tampa_uso();
else if (parte == "explodida") { color("SteelBlue") base(); color("Gainsboro") translate([0, 0, eH + 25]) tampa_uso(); }
else { color("SteelBlue") base(); color("Gainsboro") translate([0, 0, eH]) tampa_uso(); }
