// ==UserScript==
// @name         Dziennik WF -> VULCAN frekwencja
// @namespace    dziennik-wf
// @version      0.3
// @description  Wypelnia kolumne frekwencji WF w VULCAN z danych z Dziennika WF. FILL-ONLY, nie zapisuje.
// @match        https://dziennik-dziennik.vulcan.net.pl/lodz/016197/*
// @grant        none
// ==/UserScript==
(function(){
'use strict';
if(window.__wfvulcan)return; window.__wfvulcan=1;

// --- nasz status -> nazwa symbolu w legendzie VULCAN ---
function symbolFor(status){
  var s=(status||'').toUpperCase().replace(/Ć/g,'C').replace(/[^A-Z+#•—-]/g,'');
  if(s.indexOf('SP')>=0 && s!=='') { if(/SP/.test(s)) return 'spóźnienie'; }
  var M={'C':'obecność','•':'obecność',
    'NC':'nie ćwiczy na zajęciach WF','NĆ':'nie ćwiczy na zajęciach WF','BS':'nie ćwiczy na zajęciach WF',
    'NB':'nieobecność','—':'nieobecność','-':'nieobecność',
    'NU':'nieob. uspraw.','U':'nieob. uspraw.',
    'ZW':'nie ćwiczy na zajęciach WF','Z':'nie ćwiczy na zajęciach WF',  // decyzja 09-17: 'zwolniony' VULCAN = nieobecny z powodu zwolnienia, u nas martwy; ZW appki = na sali, nie cwiczy -> nc
    'S':'spóźnienie','SP':'spóźnienie',
    'NS':'nieob. uspr. szkolne','#':'obecność zdalna'};
  return M[s]||null;
}
// --- normalizacja nazwisk (bez PL znakow, male litery) ---
function norm(s){return (s||'').toLowerCase()
  .replace(/[ąàâ]/g,'a').replace(/ć/g,'c').replace(/[ęèê]/g,'e').replace(/ł/g,'l')
  .replace(/ń/g,'n').replace(/[óòô]/g,'o').replace(/ś/g,'s').replace(/[żź]/g,'z')
  .replace(/[^a-z0-9\s]/g,'')   // SKLEJ: usun znaki niewidzialne (zero-width, miekki myslnik) i interpunkcje BEZ dodawania spacji
  .replace(/\s+/g,' ').trim();}
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'})[c];});}

// --- sterowanie ExtJS przez symulowane klikniecia (UDOWODNIONE) ---
function fire(el,t){el.dispatchEvent(new MouseEvent(t,{bubbles:true,cancelable:true,view:window}));}
function firePE(el,t){try{el.dispatchEvent(new PointerEvent(t,{bubbles:true,cancelable:true,view:window,pointerId:1,pointerType:'mouse',isPrimary:true}));}catch(e){}}
function click(el){firePE(el,'pointerover');firePE(el,'pointerdown');fire(el,'mousedown');firePE(el,'pointerup');fire(el,'mouseup');fire(el,'click');}
// zdejmij WSZYSTKIE moje obwodki (feedback) z kratek VULCANa - inaczej wisza po Anuluj/zmianie symbolu
function clearMarks(){[].forEach.call(document.querySelectorAll('td[data-value-field="Wpis"]'),function(c){c.style.outline='';});}

function editableCells(){return [].slice.call(document.querySelectorAll('td[data-value-field="Wpis"].f-editable'));}
function nameCells(){return [].filter.call(document.querySelectorAll('td.v-grid-body-cell'),function(t){
  var x=(t.textContent||'').trim();
  return t.getAttribute('data-value-field')!=='Wpis' && x.indexOf(' ')>0 && /[A-Za-zĄĆĘŁŃÓŚŻŹ]/.test(x[0]);});}
// ktory wiersz legendy jest teraz zaznaczony (nazwa symbolu) — null gdy zaden
function armedName(){var res=null;
  [].forEach.call(document.querySelectorAll('tr.x-grid-row.x-grid-row-selected, tr.x-grid-row.x-grid-row-focused'),function(r){
    var tds=r.querySelectorAll('td'); if(tds.length<2)return; var n=(tds[1].textContent||'').trim();
    if(SHORT.hasOwnProperty(n) && (res===null || /selected/.test(r.className))) res=n;});
  return res;}
function legendRow(symbolName){var res=null,target=norm(symbolName);
  [].forEach.call(document.querySelectorAll('tr.x-grid-row'),function(r){
    var tds=r.querySelectorAll('td'); if(tds.length>=2 && norm(tds[1].textContent)===target) res=r;});
  return res;}

// pary kratka<->nazwisko po pozycji (ta sama wysokosc = ten sam uczen)
function buildPairs(){
  var eds=editableCells(),ncs=nameCells(),out=[];
  // pewniejsze: jesli tyle samo kratek co nazwisk -> laczymy po kolejnosci wierszy
  if(eds.length && eds.length===ncs.length){
    out=eds.map(function(c,i){return {cell:c, name:(ncs[i].textContent||'').replace(/\s+/g,' ').trim()};});
  } else {
    // awaryjnie: po pozycji na ekranie
    eds.forEach(function(c){
      var top=c.getBoundingClientRect().top,best=null,bd=12;
      ncs.forEach(function(n){var d=Math.abs(n.getBoundingClientRect().top-top); if(d<bd){bd=d;best=n;}});
      if(best) out.push({cell:c, name:(best.textContent||'').replace(/\s+/g,' ').trim()});
    });
  }
  // VULCAN dubluje te sama kratke w DOM (identyczna data-key) -> dedup, zostaw widoczna kopie, zachowaj kolejnosc
  var by={},order=[];
  out.forEach(function(p){
    var k=p.cell.getAttribute('data-key')||('__'+p.name);
    var vis=(p.cell.offsetParent!==null&&p.cell.getBoundingClientRect().height>0)?1:0;
    if(!(k in by)){ by[k]={p:p,vis:vis}; order.push(k); }
    else if(vis&&!by[k].vis){ by[k].p=p; by[k].vis=vis; }
  });
  return order.map(function(k){return by[k].p;});
}
// parsuj wklejone dane -> {normKey: status}
function parseInput(txt){
  var map={};
  (txt||'').split(/\r?\n/).forEach(function(line){
    line=line.replace(/\s+$/,''); if(!line.trim())return;
    var m=line.split(/\t|;|\||\s{2,}|:\s/);
    if(m.length<2){ m=line.split(/\s+/); if(m.length<2)return; }
    var status=m.pop().trim();
    var name=m.join(' ').trim();
    if(name) map[norm(name)]=status;
  });
  return map;
}
// dopasuj input do par: pelne nazwisko, potem samo nazwisko (1. token) jesli jednoznaczne
function match(pairs,inputMap){
  var res=[], keys=Object.keys(inputMap), used={};
  // indeks nazwisk (1. token) z siatki
  var bySurname={};
  pairs.forEach(function(p){var sn=norm(p.name).split(' ')[0]; (bySurname[sn]=bySurname[sn]||[]).push(p);});
  pairs.forEach(function(p){
    var full=norm(p.name);
    var st = inputMap[full];
    if(st===undefined){ // sprobuj po samym nazwisku
      var sn=full.split(' ')[0];
      // szukaj w input klucza, ktorego 1. token == sn
      // nazwisko moze byc 1. tokenem (VULCAN: "Nowak Jan") LUB ostatnim (appka WF: "Jan Nowak")
      for(var i=0;i<keys.length;i++){ var tk=keys[i].split(' '); if((tk[0]===sn||tk[tk.length-1]===sn) && bySurname[sn] && bySurname[sn].length===1){ st=inputMap[keys[i]]; used[keys[i]]=1; break; } }
    } else used[full]=1;
    var sym = st!==undefined ? symbolFor(st) : null;
    res.push({pair:p, status:(st===undefined?null:st), symbol:sym});
  });
  var unmatchedInput = keys.filter(function(k){return !used[k];});
  return {rows:res, unmatchedInput:unmatchedInput};
}

// symbol (nazwa legendy) -> krotki znak w kratce (do weryfikacji)
var SHORT={'obecność':'•','nieobecność':'—','nieob. uspraw.':'u','spóźnienie':'s','nieob. uspr. szkolne':'ns','zwolniony':'z','obecność zdalna':'#','nie ćwiczy na zajęciach WF':'nc'};
// Szczebel 2A: usprawiedliwienie z e-dziennika (u/ns/z) jest NOWSZA prawda niz NB z apki -> nie nadpisuj nieobecnoscia.
// Kierunek prawdy: VULCAN wygrywa dla usprawiedliwien, apka dla cwiczenia/stroju/spoznienia.
var EXCUSED=['u','ns','z'];
function keepExcused(symbolName,cellTexts){
  if(symbolName!=='nieobecność')return false;
  return (cellTexts||[]).some(function(t){return EXCUSED.indexOf((t||'').trim().toLowerCase())>=0;});
}

// ---------------- UI ----------------
var P=document.createElement('div');
P.style.cssText='position:fixed;top:10px;right:10px;z-index:2147483647;width:340px;background:#fff;border:2px solid #1E2D4F;border-radius:8px;font:13px/1.4 Arial,sans-serif;color:#1A1A1A;box-shadow:0 6px 24px rgba(0,0,0,.3)';
P.innerHTML=''
+'<div style="background:#1E2D4F;color:#fff;padding:8px 10px;font-weight:bold;border-radius:5px 5px 0 0;display:flex;justify-content:space-between">Dziennik WF -> VULCAN <span style="opacity:.6;font-weight:normal">v19</span><span id="wfX" style="cursor:pointer">✕</span></div>'
+'<div style="padding:10px">'
+'<div style="font-size:12px;color:#4A4543;margin-bottom:6px">Wklej statusy dnia: <b>Nazwisko Imię</b> [tab / ; / 2 spacje] <b>status</b> (C, NĆ, BS, NB, NU, ZW, SP)</div>'
+'<textarea id="wfIn" style="width:100%;height:120px;box-sizing:border-box;font:12px monospace" placeholder="Nowak Jan\tC\nKowalska Zofia\tNU"></textarea>'
+'<div style="margin-top:8px;display:flex;gap:6px">'
+'<button id="wfPrev" style="flex:1;padding:8px;border:1px solid #1E2D4F;background:#fff;border-radius:5px;cursor:pointer">Podgląd</button>'
+'<button id="wfGo" style="flex:1;padding:8px;border:0;background:#1E7A34;color:#fff;border-radius:5px;cursor:pointer;font-weight:bold">Wypełnij</button>'
+'</div>'
+'<div id="wfLog" style="margin-top:8px;max-height:200px;overflow:auto;font:12px monospace;white-space:pre-wrap;color:#1A1A1A"></div>'
+'<div style="margin-top:6px;font-size:11px;color:#8C2520">Nic nie zapisuje. Po wypełnieniu sprawdź i kliknij „Zapisz" w VULCAN sam.</div>'
+'</div>';
document.body.appendChild(P);
clearMarks(); // wyczysc resztkowe obwodki po poprzedniej wersji (reuzyte wezly DOM)
var log=function(m,c){document.getElementById('wfLog').innerHTML='<span style="color:'+(c||'#1A1A1A')+'">'+m+'</span>';};
document.getElementById('wfX').onclick=function(){clearMarks(); P.remove(); window.__wfvulcan=0;};

function preview(){
  clearMarks(); // kazda akcja startuje od czystej siatki - obwodki nie wisza po Anuluj/zmianie symbolu
  var pairs=buildPairs();
  if(!pairs.length){log('Nie widzę kratek WF. Czy okno EDYCJI frekwencji jest otwarte?','#8C2520');return null;}
  var inp=parseInput(document.getElementById('wfIn').value);
  if(!Object.keys(inp).length){log('Wklej najpierw dane.','#8C2520');return null;}
  var m=match(pairs,inp);
  var ok=m.rows.filter(function(r){return r.symbol;});
  var noInput=m.rows.filter(function(r){return r.status===null;});
  var badStatus=m.rows.filter(function(r){return r.status!==null && !r.symbol;});
  var _eds=editableCells().length,_ncs=nameCells().length;
  var html='Uczniów w kolumnie: '+pairs.length+' (kratki '+_eds+' / nazwiska '+_ncs+', '+(_eds&&_eds===_ncs?'po kolejności':'geometria')+')  |  do wpisania: <b>'+ok.length+'</b>\n';
  if(ok.length) html+='\nSPRAWDŹ dopasowania:\n'+ok.map(function(r){var k=r.pair.cell.getAttribute('data-key')||'';var uid=k?k.split('-').pop():'?';return '• '+esc(r.pair.name)+' → '+esc(r.status)+'  [uid '+esc(uid)+']';}).join('\n')+'\n';
  if(badStatus.length) html+='\n⚠ nieznany status ('+badStatus.length+'): '+esc(badStatus.map(function(r){return r.pair.name+'='+r.status;}).join(', '))+'\n';
  if(m.unmatchedInput.length) html+='\n⚠ z wklejonych nie znalazłem ('+m.unmatchedInput.length+'): '+esc(m.unmatchedInput.join(', '))+'\n';
  if(noInput.length) html+='\n(bez danych, pominę: '+noInput.length+')\n';
  log(html);
  return m;
}
document.getElementById('wfPrev').onclick=preview;
document.getElementById('wfGo').onclick=function(){
  var m=preview(); if(!m)return;
  var todo=m.rows.filter(function(r){return r.symbol;});
  // v19: nie kasuj diagnostyki Podglądu (18.09: 7b l.7 padło bez śladu, ręczny wpis, przyczyna nieznana)
  if(!todo.length){var L=document.getElementById('wfLog'); L.innerHTML='<span style="color:#8C2520">Nie ma nic do wpisania. Niżej co widziałem — zrób zrzut:</span>\n'+L.innerHTML; return;}
  var i=0,done=0,skip=0,fail=[],excused=[];
  // rozne myslniki Unicode (— – ‒ − -) = ta sama kreska 'nieobecnosc' (bug 09-17: VULCAN wpisuje inny znak niz w SHORT)
  var txt=function(c){return (c.textContent||'').trim().replace(/[‐-―−\-]/g,'—');};
  function copiesOf(cell){var k=cell.getAttribute('data-key'); if(!k)return [cell];
    var all=[].filter.call(document.querySelectorAll('td[data-value-field="Wpis"]'),function(c){return c.getAttribute('data-key')===k;});
    return all.length?all:[cell];}
  function apply(r,attempt,cb){
    var cps=copiesOf(r.pair.cell);
    var leg=legendRow(r.symbol);
    if(!leg){ cb(false,'brak symbolu '+r.symbol+' (czy lista symboli jest widoczna?)'); return; }
    // zrodlo prawdy dla weryfikacji: znak pokazany w 1. komorce wiersza legendy (ten sam glif, ktory VULCAN wpisuje); SHORT tylko awaryjnie
    var legSym=txt(leg.querySelectorAll('td')[0]);
    var want=legSym||SHORT[r.symbol];
    var same=function(t){return t===want || t===SHORT[r.symbol];};
    var beforeAll=cps.map(txt);
    if(keepExcused(r.symbol,beforeAll)){ r.kept=beforeAll.filter(Boolean)[0]||'u'; excused.push(r.pair.name+' ('+r.kept+')'); cps.forEach(function(c){c.style.outline='2px solid #B08F4E';}); cb(true); return; }
    if(want && beforeAll.some(same)){ skip++; cps.forEach(function(c){c.style.outline='2px solid #B08F4E';}); cb(true); return; }
    var legT=leg.querySelector('span[class*="clickab"]')||leg.querySelector('.x-grid-cell-inner')||leg.querySelector('td')||leg;
    // 1) ARMuj symbol w legendzie i SPRAWDZ, ktory wiersz VULCAN naprawde zaznaczyl (bug 09-17: NB<->ZW zamienione)
    var armTry=0;
    // 0) ZAZNACZ kratke tego ucznia ZANIM klikniesz legende. VULCAN obsluguje oba gesty naraz: klik legendy
    //    uzbraja pedzel ORAZ wpisuje symbol do zaznaczonej kratki -> bez tego kratka ucznia i dostawala symbol ucznia i+1 (bug 09-17)
    cps.forEach(function(c){click(c);});
    (function arm(){
      click(legT); armTry++;
      setTimeout(function(){
        var got=armedName();
        if(got!==r.symbol && armTry<3){ arm(); return; }
        paint(got);
      },260);
    })();
    function paint(armed){
      cps.forEach(function(c){click(c);});        // 2) PAINT: klik w kratke (obie kopie DOM)
      setTimeout(function(){
        var afterAll=cps.map(txt);
        var okHit = want ? afterAll.some(same) : afterAll.some(function(t,ix){return t!==beforeAll[ix];});
        if(okHit){ cps.forEach(function(c){c.style.outline='2px solid #1E7A34';}); cb(true); }
        else if(attempt<2){ apply(r,attempt+1,cb); }
        else {
          var codes=function(s){return s.split('').map(function(ch){return ch.charCodeAt(0);}).join('+');};
          var diag='legenda "'+want+'"='+codes(want||'')+' | '+cps.map(function(c,ix){return '#'+ix+' "'+txt(c)+'"='+codes(txt(c))+' '+(/selected|focus/i.test(c.className)?'SEL':'-')+'/vis'+(c.offsetParent!==null?'T':'N');}).join(' | ');
          var legSel=/selected|focus/i.test(leg.className)?'legZ=SEL':'legZ=nieSEL';
          cps.forEach(function(c){c.style.outline='2px solid #8C2520';});
          cb(false,'nie zareagowało (arm→paint) [chciałem '+r.symbol+', uzbrojone: '+(armed||'nic')+' | '+diag+' | '+legSel+']');
        }
      },260);
    }
  }
  (function step(){
    if(i>=todo.length){
      // KONTROLA KONCOWA: po calej serii czytam kazda kratke jeszcze raz (lapie nadpisanie przez pozniejsze kliki)
      setTimeout(function(){
        var bad=[];
        todo.forEach(function(r){
          if(r.kept)return; // usprawiedliwiony w VULCAN - celowo nie ruszany
          var leg=legendRow(r.symbol); var want=leg?txt(leg.querySelectorAll('td')[0]):SHORT[r.symbol];
          var got=copiesOf(r.pair.cell).map(txt);
          if(!got.some(function(t){return t===want||t===SHORT[r.symbol];})){ bad.push(r.pair.name+': jest "'+got.join('/')+'", ma być "'+want+'"'); copiesOf(r.pair.cell).forEach(function(c){c.style.outline='2px solid #8C2520';}); }
        });
        var err=fail.length||bad.length;
        log('Gotowe: wpisano '+done+', już poprawne '+skip+(excused.length?(', zostawione '+excused.length):'')+', z '+todo.length+'.'+(fail.length?('\n⚠ nie udało się: '+esc(fail.join(', '))):'')
          +(excused.length?('\n✋ już usprawiedliwieni w VULCAN (popraw w apce na NU): '+esc(excused.join(', '))):'')
          +(bad.length?('\n⚠ kontrola końcowa — rozjazd: '+esc(bad.join('; '))):'\n✔ kontrola końcowa: wszystkie kratki zgodne.')
          +'\n\nSprawdź kolumnę (zielone=wpisane, złote=już OK, czerwone=błąd) i kliknij „Zapisz" w VULCAN sam.', err?'#8C2520':'#1E7A34');
      },400);
      return;
    }
    var r=todo[i++];
    log('Wpisuję… '+i+'/'+todo.length,'#1E2D4F');
    apply(r,1,function(ok,why){ if(ok&&!r.kept)done++; else fail.push(r.pair.name+(why?'('+why+')':'')); setTimeout(step,120); });
  })();
};
log('Gotowy. Otwórz okno edycji frekwencji WF, wklej dane, „Podgląd" → „Wypełnij".','#1E7A34');
})();
