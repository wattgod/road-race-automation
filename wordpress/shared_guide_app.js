(function(){
"use strict";
document.documentElement.classList.add("gg-has-js");
function track(n,p){if(typeof gtag==="function")gtag("event",n,Object.assign({transport_type:"beacon"},p||{}));}
var STORAGE_KEY="gg_guide_unlocked";
var page=document.querySelector(".gg-neo-brutalist-page");
function isUnlocked(){try{return localStorage.getItem(STORAGE_KEY)==="1";}catch(e){return false;}}
function unlock(method){
try{localStorage.setItem(STORAGE_KEY,"1");}catch(e){}
if(page)page.classList.add("gg-guide-unlocked");
document.querySelectorAll(".gg-guide-chapnav-item--locked").forEach(function(el){el.classList.add("gg-guide-chapnav-item--unlocked");});
track("guide_unlock",{method:method||"unknown"});
}
if(isUnlocked()){
if(page)page.classList.add("gg-guide-unlocked");
document.querySelectorAll(".gg-guide-chapnav-item--locked").forEach(function(el){el.classList.add("gg-guide-chapnav-item--unlocked");});
track("guide_return_visit",{unlocked:true});
}
window.addEventListener("message",function(e){
if(e.origin&&e.origin.indexOf("substack.com")!==-1){
if(e.data&&(e.data.type==="subscription-created"||e.data==="subscription-created"))unlock("substack_subscribe");
}
});
var bypassBtn=document.getElementById("gg-guide-gate-bypass");
if(bypassBtn)bypassBtn.addEventListener("click",function(){unlock("manual_bypass");});
var scrollMilestones={25:false,50:false,75:false,100:false};
var progressBar=document.querySelector(".gg-guide-progress-bar");
var progressTicking=false;
window.addEventListener("scroll",function(){
if(!progressTicking){
requestAnimationFrame(function(){
var h=document.documentElement.scrollHeight-window.innerHeight;
var pct=h>0?(window.scrollY/h)*100:0;
if(progressBar){progressBar.style.width=Math.min(100,pct)+"%";progressBar.setAttribute("aria-valuenow",Math.round(Math.min(100,pct)));}
[25,50,75,100].forEach(function(m){if(!scrollMilestones[m]&&pct>=m){scrollMilestones[m]=true;track("guide_scroll_depth",{percent:m,unlocked:isUnlocked()});}});
progressTicking=false;
});
progressTicking=true;
}
},{passive:true});
var chapters=document.querySelectorAll(".gg-guide-chapter");
var navItems=document.querySelectorAll(".gg-guide-chapnav-item");
var chaptersRead={};
if(chapters.length&&"IntersectionObserver" in window){
var activeId=null;
var chapterObs=new IntersectionObserver(function(entries){
entries.forEach(function(entry){
if(entry.isIntersecting){
activeId=entry.target.id;
var chNum=entry.target.getAttribute("data-chapter");
navItems.forEach(function(nav){
nav.classList.toggle("gg-guide-chapnav-item--active",nav.getAttribute("data-chapter")===activeId);
});
if(chNum&&!chaptersRead[chNum]){chaptersRead[chNum]=true;track("guide_chapter_view",{chapter_number:parseInt(chNum,10),chapter_id:activeId});}
}
});
},{rootMargin:"-20% 0px -70% 0px",threshold:0});
chapters.forEach(function(ch){chapterObs.observe(ch);});
}
navItems.forEach(function(item){
item.addEventListener("click",function(e){
e.preventDefault();
var chapterId=item.getAttribute("data-chapter");
var target=document.getElementById(chapterId);
if(target&&target.classList.contains("gg-guide-gated")&&!isUnlocked()){
var gateEl=document.getElementById("gg-guide-gate");
if(gateEl)gateEl.scrollIntoView({behavior:"smooth",block:"start"});
}else if(target){target.scrollIntoView({behavior:"smooth",block:"start"});}
track("guide_chapnav_click",{chapter:chapterId});
});
});
var gateEl=document.getElementById("gg-guide-gate");
if(gateEl&&"IntersectionObserver" in window){
var gateTracked=false;
var gateObs=new IntersectionObserver(function(entries){
entries.forEach(function(entry){
if(entry.isIntersecting&&!gateTracked){gateTracked=true;track("guide_gate_impression",{});gateObs.unobserve(gateEl);}
});
},{threshold:0.3});
gateObs.observe(gateEl);
}
document.querySelectorAll(".gg-guide-accordion-trigger").forEach(function(trigger){
trigger.addEventListener("click",function(){
var expanded=trigger.getAttribute("aria-expanded")==="true";
trigger.setAttribute("aria-expanded",expanded?"false":"true");
});
});
document.querySelectorAll(".gg-guide-tabs").forEach(function(tabGroup){
var tabs=tabGroup.querySelectorAll(".gg-guide-tab");
var panels=tabGroup.querySelectorAll(".gg-guide-tab-panel");
tabs.forEach(function(tab){
tab.addEventListener("click",function(){
var targetId=tab.getAttribute("data-tab");
tabs.forEach(function(t){t.classList.remove("gg-guide-tab--active");t.setAttribute("aria-selected","false");});
panels.forEach(function(p){p.style.display="none";});
tab.classList.add("gg-guide-tab--active");
tab.setAttribute("aria-selected","true");
var panel=document.getElementById(targetId);
if(panel)panel.style.display="block";
});
});
});
document.querySelectorAll(".gg-guide-knowledge-check").forEach(function(kc){
var options=kc.querySelectorAll(".gg-guide-kc-option");
var explanation=kc.querySelector(".gg-guide-kc-explanation");
var answered=false;
options.forEach(function(opt){
opt.addEventListener("click",function(){
if(answered)return;
answered=true;
var isCorrect=opt.getAttribute("data-correct")==="true";
opt.classList.add(isCorrect?"gg-guide-kc-option--correct":"gg-guide-kc-option--incorrect");
if(!isCorrect){options.forEach(function(o){if(o.getAttribute("data-correct")==="true")o.classList.add("gg-guide-kc-option--correct");});}
options.forEach(function(o){if(o!==opt&&o.getAttribute("data-correct")!=="true")o.classList.add("gg-guide-kc-option--disabled");o.setAttribute("aria-disabled","true");});
if(explanation)explanation.style.display="block";
track("guide_knowledge_check",{correct:isCorrect});
});
});
});
document.querySelectorAll(".gg-guide-flashcard").forEach(function(card){
function flipCard(){card.classList.toggle("gg-guide-flashcard--flipped");track("guide_flashcard_flip",{card_id:card.id});}
card.addEventListener("click",flipCard);
card.addEventListener("keydown",function(e){if(e.key==="Enter"||e.key===" "){e.preventDefault();flipCard();}});
});
document.querySelectorAll(".gg-guide-scenario").forEach(function(scenario){
var options=scenario.querySelectorAll(".gg-guide-scenario-option");
var answered=false;
options.forEach(function(opt){
opt.addEventListener("click",function(){
if(answered)return;
answered=true;
opt.classList.add("gg-guide-scenario-option--selected");
options.forEach(function(o){if(o!==opt)o.classList.add("gg-guide-scenario-option--disabled");o.setAttribute("aria-disabled","true");});
track("guide_scenario_choice",{best:opt.getAttribute("data-best")==="true"});
});
});
});
document.querySelectorAll(".gg-guide-cta a, .gg-guide-finale-card a").forEach(function(link){
link.addEventListener("click",function(){
var ctaBlock=link.closest(".gg-guide-cta, .gg-guide-finale-card");
var ctaType="unknown";
if(ctaBlock){
if(ctaBlock.classList.contains("gg-guide-cta--newsletter")||ctaBlock.classList.contains("gg-guide-finale-card--newsletter"))ctaType="newsletter";
else if(ctaBlock.classList.contains("gg-guide-cta--training")||ctaBlock.classList.contains("gg-guide-finale-card--training"))ctaType="training_plan";
else if(ctaBlock.classList.contains("gg-guide-cta--coaching")||ctaBlock.classList.contains("gg-guide-finale-card--coaching"))ctaType="coaching";
}
track("cta_click",{source:"guide",cta_name:ctaType});
});
});
function clearCalcErrors(calc){
calc.querySelectorAll(".gg-guide-calc-input--error").forEach(function(el){el.classList.remove("gg-guide-calc-input--error");});
var errEl=calc.querySelector(".gg-guide-calc-error");
if(errEl){errEl.style.display="none";errEl.textContent="";}
}
function showCalcError(calc,msg){
var errEl=calc.querySelector(".gg-guide-calc-error");
if(errEl){errEl.textContent=msg;errEl.style.display="block";}
}
document.querySelectorAll(".gg-guide-calculator").forEach(function(calc){
var calcType=calc.getAttribute("data-calc-type");
var btn=calc.querySelector(".gg-guide-calc-btn");
var output=calc.querySelector(".gg-guide-calc-output");
calc.querySelectorAll(".gg-guide-calc-toggle").forEach(function(toggle){
var btns=toggle.querySelectorAll(".gg-guide-calc-toggle-btn");
btns.forEach(function(b){
b.addEventListener("click",function(){
btns.forEach(function(t){t.classList.remove("gg-guide-calc-toggle-btn--active");});
b.classList.add("gg-guide-calc-toggle-btn--active");
});
});
});
if(btn)btn.addEventListener("click",function(){
if(calcType==="ftp-zones")computeFtpZones(calc,output);
else if(calcType==="daily-nutrition")computeDailyNutrition(calc,output);
else if(calcType==="workout-fueling")computeWorkoutFueling(calc,output);
});
});
function computeFtpZones(calc,output){
clearCalcErrors(calc);
var ftpInput=calc.querySelector("#gg-calc-ftp-power");
var testInput=calc.querySelector("#gg-calc-ftp-test");
var ageInput=calc.querySelector("#gg-calc-ftp-age");
var ftp=0;
if(ftpInput&&ftpInput.value)ftp=parseInt(ftpInput.value,10);
if((!ftp||ftp<50)&&testInput&&testInput.value)ftp=Math.round(parseInt(testInput.value,10)*0.95);
if(!ftp||ftp<50||ftp>600){
if(ftpInput)ftpInput.classList.add("gg-guide-calc-input--error");
if(testInput)testInput.classList.add("gg-guide-calc-input--error");
showCalcError(calc,"Enter FTP (50-600w) or a 20-min test power.");
return;
}
var age=ageInput&&ageInput.value?parseInt(ageInput.value,10):0;
var hrmax=age>=16?Math.round(211-0.64*age):0;
var ftpDisp=output.querySelector(".gg-guide-calc-ftp-display");
if(ftpDisp)ftpDisp.textContent="Your FTP: "+ftp+" watts"+(hrmax?" | HRmax: "+hrmax+" bpm":"");
output.style.display="block";
var zones=output.querySelectorAll(".gg-guide-calc-zone");
zones.forEach(function(zone,i){
var minPct=parseInt(zone.getAttribute("data-min"),10);
var maxPct=parseInt(zone.getAttribute("data-max"),10);
var minW=Math.round(ftp*minPct/100);
var maxW=Math.round(ftp*maxPct/100);
var range=zone.querySelector(".gg-guide-calc-zone-range");
if(range)range.textContent=minW+"-"+maxW+"w";
var fill=zone.querySelector(".gg-guide-calc-zone-fill");
if(fill)setTimeout(function(){fill.style.width=Math.min(maxPct/2,100)+"%";},i*80);
var hrEl=zone.querySelector(".gg-guide-calc-zone-hr");
if(hrEl&&hrmax){
var hrMinPct=zone.getAttribute("data-hr-min");
var hrMaxPct=zone.getAttribute("data-hr-max");
if(hrMinPct&&hrMaxPct)hrEl.textContent=Math.round(hrmax*parseInt(hrMinPct,10)/100)+"-"+Math.round(hrmax*parseInt(hrMaxPct,10)/100)+" bpm";
}
});
track("guide_calculator_use",{type:"ftp_zones",ftp:ftp,has_hr:hrmax>0});
}
function setOut(id,t){var e=document.getElementById("gg-calc-out-"+id);if(e)e.textContent=t;}
function computeDailyNutrition(calc,output){
clearCalcErrors(calc);
var wi=calc.querySelector("#gg-calc-dn-weight");
var w=wi?parseFloat(wi.value):0;
if(!w||w<30||w>500){
if(wi)wi.classList.add("gg-guide-calc-input--error");
showCalcError(calc,"Enter a valid weight (30-500).");
return;
}
var tg=calc.querySelector(".gg-guide-calc-toggle[data-field='dn-unit']");
var u="kg";
if(tg){var a=tg.querySelector(".gg-guide-calc-toggle-btn--active");if(a)u=a.getAttribute("data-value")||"kg";}
var kg=u==="lbs"?w*0.4536:w;
var ds=calc.querySelector("#gg-calc-dn-day");
var d=ds?ds.value:"easy";
var cm={rest:[2,3],hard:[5,7],race:[8,10]}[d]||[3,5];
output.style.display="block";
setOut("protein",Math.round(kg*1.6)+"-"+Math.round(kg*2.2)+"g");
setOut("carbs",Math.round(kg*cm[0])+"-"+Math.round(kg*cm[1])+"g");
setOut("fat",Math.round(kg*0.8)+"-"+Math.round(kg*1.2)+"g");
setOut("calories",Math.round(kg*1.6*4+kg*cm[0]*4+kg*0.8*9)+"-"+Math.round(kg*2.2*4+kg*cm[1]*4+kg*1.2*9)+" kcal");
track("guide_calculator_use",{type:"daily_nutrition",weight_kg:Math.round(kg)});
}
function computeWorkoutFueling(calc,output){
clearCalcErrors(calc);
var di=calc.querySelector("#gg-calc-wf-duration");
var dur=di?parseFloat(di.value):0;
if(!dur||dur<0.5||dur>24){
if(di)di.classList.add("gg-guide-calc-input--error");
showCalcError(calc,"Enter a valid duration (0.5-24 hours).");
return;
}
var ints=calc.querySelector("#gg-calc-wf-intensity");
var rate={z2:50,tempo:65,race:75}[ints?ints.value:"z2"]||40;
var tc=Math.round(dur*rate),hy=Math.round(dur*500);
output.style.display="block";
setOut("total-carbs",tc+"g");
setOut("fuel-rate",rate+"g/hr");
setOut("hydration",(hy/1000).toFixed(1)+"L ("+Math.round(hy/500)+" bottles)");
setOut("gels",Math.ceil(tc/25)+" gels (or equivalent)");
track("guide_calculator_use",{type:"workout_fueling",duration:dur});
}
var RIDER_STORAGE="gg_guide_rider_type";
var riderSelector=document.getElementById("gg-guide-rider-selector");
var riderBadge=document.getElementById("gg-guide-rider-badge");
var riderBadgeType=document.getElementById("gg-guide-rider-badge-type");
var riderBadgeChange=document.getElementById("gg-guide-rider-badge-change");
function setRider(type){
try{localStorage.setItem(RIDER_STORAGE,type);}catch(e){}
if(!riderSelector)return;
var btns=riderSelector.querySelectorAll(".gg-guide-rider-btn");
var label="";
var ftp=200;
btns.forEach(function(b){
var isMatch=b.getAttribute("data-rider")===type;
b.classList.toggle("gg-guide-rider-btn--active",isMatch);
b.setAttribute("aria-checked",isMatch?"true":"false");
if(isMatch){label=b.querySelector(".gg-guide-rider-btn-label").textContent;ftp=parseInt(b.getAttribute("data-ftp")||"200",10);}
});
if(riderBadge&&label){riderBadge.style.display="flex";if(riderBadgeType)riderBadgeType.textContent=label;}
document.querySelectorAll(".gg-guide-tabs").forEach(function(tabGroup){
var matchTab=tabGroup.querySelector('.gg-guide-tab[data-rider-type="'+type+'"]');
if(matchTab){
var tabs=tabGroup.querySelectorAll(".gg-guide-tab");
var panels=tabGroup.querySelectorAll(".gg-guide-tab-panel");
tabs.forEach(function(t){t.classList.remove("gg-guide-tab--active");t.setAttribute("aria-selected","false");});
panels.forEach(function(p){p.style.display="none";});
matchTab.classList.add("gg-guide-tab--active");
matchTab.setAttribute("aria-selected","true");
var targetId=matchTab.getAttribute("data-tab");
var panel=document.getElementById(targetId);
if(panel)panel.style.display="block";
}
});
var ftpInput=document.getElementById("gg-calc-ftp-power");
if(ftpInput)ftpInput.placeholder="e.g., "+ftp;
/* Personalized content: show matching variant, hide others */
document.querySelectorAll(".gg-personalized").forEach(function(pc){
var variants=pc.querySelectorAll(".gg-personalized__variant");
variants.forEach(function(v){
var isMatch=v.getAttribute("data-rider-type")===type;
v.classList.toggle("gg-personalized--active",isMatch);
});
});
track("guide_rider_select",{rider_type:type});
}
if(riderSelector){
riderSelector.querySelectorAll(".gg-guide-rider-btn").forEach(function(btn){
btn.addEventListener("click",function(){setRider(btn.getAttribute("data-rider"));});
});
}
if(riderBadgeChange){
riderBadgeChange.addEventListener("click",function(){
if(riderSelector)riderSelector.scrollIntoView({behavior:"smooth",block:"start"});
});
}
try{var saved=localStorage.getItem(RIDER_STORAGE);if(saved)setRider(saved);}catch(e){}
var pageStartTime=Date.now();
window.addEventListener("beforeunload",function(){
var seconds=Math.round((Date.now()-pageStartTime)/1000);
track("guide_time_on_page",{seconds:seconds,chapters_read:Object.keys(chaptersRead).length});
});

/* ── Infographic Scroll Animations ── */
if("IntersectionObserver" in window){
var prefersReduced=window.matchMedia("(prefers-reduced-motion:reduce)").matches;
if(!prefersReduced){
var infoFigs=document.querySelectorAll("figure[data-asset-id]");
if(infoFigs.length){
var infoObs=new IntersectionObserver(function(entries,obs){
entries.forEach(function(entry){
if(entry.isIntersecting){
var fig=entry.target;
fig.classList.add("gg-in-view");
/* SVG bar animations: set target dimensions */
fig.querySelectorAll("[data-animate='bar']").forEach(function(el){
var tw=el.getAttribute("data-target-width");
var th=el.getAttribute("data-target-height");
if(tw)el.setAttribute("width",tw);
if(th)el.setAttribute("height",th);
});
/* SVG line-draw animations */
fig.querySelectorAll("[data-animate='line']").forEach(function(el){
var len=el.getTotalLength?el.getTotalLength():0;
if(len){el.style.strokeDasharray=len;el.style.strokeDashoffset="0";}
});
/* Counter animation (countUp) */
fig.querySelectorAll("[data-animate='counter'] [data-target]").forEach(function(el){
var target=parseFloat(el.getAttribute("data-target"));
if(isNaN(target))return;
var start=0;var dur=1200;var t0=performance.now();
function tick(now){
var pct=Math.min((now-t0)/dur,1);
var val=Math.round(start+(target-start)*pct);
el.textContent=val;
if(pct<1)requestAnimationFrame(tick);
}
requestAnimationFrame(tick);
});
/* Stroke gauge animation — CSS handles via .gg-in-view, just trigger class */
/* Pyramid / gantt / progress — CSS handles via .gg-in-view + --w custom property */
/* Profile draw animation */
fig.querySelectorAll("[data-animate='profile'] path").forEach(function(el){
var len=el.getTotalLength?el.getTotalLength():0;
if(len){el.style.strokeDasharray=len;el.style.strokeDashoffset="0";}
});
/* Scatter marker reveal — CSS handles via .gg-in-view + --delay */
/* Digit roller animation */
fig.querySelectorAll("[data-interactive='digit-roller']").forEach(function(roller){
var digits=roller.querySelectorAll(".gg-infographic-digit");
var targetVal=roller.getAttribute("data-value")||"0";
var padded=targetVal.padStart(digits.length,"0");
digits.forEach(function(d,i){
var strip=d.querySelector(".gg-infographic-digit-strip");
if(!strip)return;
var digit=parseInt(padded[i],10)||0;
strip.style.transform="translateY(-"+(digit*56)+"px)";
});
});
obs.unobserve(fig);
track("infographic_view",{asset_id:fig.getAttribute("data-asset-id")});
}
});
},{threshold:0.2});
infoFigs.forEach(function(fig){
/* Pre-set SVG bars to zero width/height */
fig.querySelectorAll("[data-animate='bar']").forEach(function(el){
var tw=el.getAttribute("data-target-width");
var th=el.getAttribute("data-target-height");
if(tw)el.setAttribute("width","0");
if(th)el.setAttribute("height","0");
});
/* Pre-set SVG lines for draw animation */
fig.querySelectorAll("[data-animate='line']").forEach(function(el){
var len=el.getTotalLength?el.getTotalLength():0;
if(len){el.style.strokeDasharray=len;el.style.strokeDashoffset=len;}
});
/* Pre-set profile paths for draw animation */
fig.querySelectorAll("[data-animate='profile'] path").forEach(function(el){
var len=el.getTotalLength?el.getTotalLength():0;
if(len){el.style.strokeDasharray=len;el.style.strokeDashoffset=len;}
});
/* Pre-set gauge strokes — CSS initial state handles via .gg-has-js */
/* Pre-set digit roller to initial position (all zeros visible) */
fig.querySelectorAll("[data-interactive='digit-roller'] .gg-infographic-digit-strip").forEach(function(strip){
strip.style.transform="translateY(0)";
});
infoObs.observe(fig);
});
}
}
}

/* ── Infographic Tooltips ── */
var ttDiv=null;
function showTooltip(el){
var tip=el.getAttribute("data-tooltip");
if(!tip)return;
if(!ttDiv){ttDiv=document.createElement("div");ttDiv.className="gg-infographic-tooltip";document.body.appendChild(ttDiv);}
ttDiv.textContent=tip;
ttDiv.classList.add("gg-infographic-tooltip--visible");
var r=el.getBoundingClientRect();
ttDiv.style.left=Math.max(8,r.left+r.width/2-130)+"px";
ttDiv.style.top=(r.top+window.scrollY-ttDiv.offsetHeight-8)+"px";
track("infographic_tooltip",{text:tip.slice(0,40)});
}
function hideTooltip(){if(ttDiv)ttDiv.classList.remove("gg-infographic-tooltip--visible");}
document.addEventListener("mouseover",function(e){var t=e.target.closest("[data-tooltip]");if(t&&t.closest(".gg-infographic"))showTooltip(t);});
document.addEventListener("mouseout",function(e){var t=e.target.closest("[data-tooltip]");if(t)hideTooltip();});
document.addEventListener("focusin",function(e){var t=e.target.closest("[data-tooltip]");if(t&&t.closest(".gg-infographic"))showTooltip(t);});
document.addEventListener("focusout",function(e){var t=e.target.closest("[data-tooltip]");if(t)hideTooltip();});

/* ── Interactive Handlers (event delegation) ── */
var prefersReduced=window.matchMedia("(prefers-reduced-motion:reduce)").matches;

/* Flip cards */
document.addEventListener("click",function(e){
var card=e.target.closest("[data-interactive='flip']");
if(!card)return;
card.classList.toggle("flipped");
track("infographic_interact",{type:"flip",asset_id:(card.closest("figure[data-asset-id]")||{}).getAttribute("data-asset-id")||""});
});
document.addEventListener("keydown",function(e){
if(e.key!=="Enter"&&e.key!==" ")return;
var card=e.target.closest("[data-interactive='flip']");
if(!card)return;
e.preventDefault();
card.classList.toggle("flipped");
});

/* Traffic light click-to-cycle */
document.addEventListener("click",function(e){
var row=e.target.closest("[data-interactive='traffic-light']");
if(!row)return;
var states=["go","caution","stop"];
var cur=row.getAttribute("data-state")||"go";
var idx=(states.indexOf(cur)+1)%states.length;
row.setAttribute("data-state",states[idx]);
track("infographic_interact",{type:"traffic-light",state:states[idx]});
});

/* Infographic accordion */
document.addEventListener("click",function(e){
var header=e.target.closest("[data-interactive='accordion'] .gg-infographic-accordion-header");
if(!header)return;
var item=header.closest(".gg-infographic-accordion-item");
if(item)item.classList.toggle("open");
track("infographic_interact",{type:"accordion"});
});

/* Radar morph */
document.addEventListener("click",function(e){
var btn=e.target.closest("[data-interactive='radar-morph'] .gg-infographic-radar-btn");
if(!btn)return;
var radar=btn.closest("[data-interactive='radar-morph']");
if(!radar)return;
var polygon=radar.querySelector("polygon.gg-infographic-radar-data");
if(!polygon)return;
var targetPts=btn.getAttribute("data-points");
if(!targetPts)return;
/* Update active button */
radar.querySelectorAll(".gg-infographic-radar-btn").forEach(function(b){b.classList.remove("active");});
btn.classList.add("active");
/* Animate polygon morph with rAF */
if(prefersReduced){polygon.setAttribute("points",targetPts);return;}
var fromPts=polygon.getAttribute("points").split(" ").map(function(p){var xy=p.split(",");return[parseFloat(xy[0]),parseFloat(xy[1])];});
var toPts=targetPts.split(" ").map(function(p){var xy=p.split(",");return[parseFloat(xy[0]),parseFloat(xy[1])];});
if(fromPts.length!==toPts.length){polygon.setAttribute("points",targetPts);return;}
var dur=600;var t0=performance.now();
function morphTick(now){
var pct=Math.min((now-t0)/dur,1);
var ease=pct<0.5?2*pct*pct:1-Math.pow(-2*pct+2,2)/2;
var pts=fromPts.map(function(f,i){return(f[0]+(toPts[i][0]-f[0])*ease).toFixed(1)+","+(f[1]+(toPts[i][1]-f[1])*ease).toFixed(1);}).join(" ");
polygon.setAttribute("points",pts);
if(pct<1)requestAnimationFrame(morphTick);
}
requestAnimationFrame(morphTick);
track("infographic_interact",{type:"radar-morph",race:btn.textContent.trim()});
});

/* Sortable table */
document.addEventListener("click",function(e){
var th=e.target.closest("[data-interactive='sortable-table'] th[data-col]");
if(!th)return;
var table=th.closest("table");
if(!table)return;
var tbody=table.querySelector("tbody");
if(!tbody)return;
var col=parseInt(th.getAttribute("data-col"),10);
var rows=Array.from(tbody.querySelectorAll("tr"));
var asc=th.getAttribute("data-sort-dir")!=="asc";
rows.sort(function(a,b){
var aText=(a.children[col]||{}).textContent||"";
var bText=(b.children[col]||{}).textContent||"";
var aNum=parseFloat(aText.replace(/[^0-9.\-]/g,""));
var bNum=parseFloat(bText.replace(/[^0-9.\-]/g,""));
if(!isNaN(aNum)&&!isNaN(bNum))return asc?aNum-bNum:bNum-aNum;
return asc?aText.localeCompare(bText):bText.localeCompare(aText);
});
rows.forEach(function(r){tbody.appendChild(r);});
table.querySelectorAll("th[data-col]").forEach(function(h){h.removeAttribute("data-sort-dir");var ind=h.querySelector(".gg-infographic-sort-indicator");if(ind)ind.textContent="";});
th.setAttribute("data-sort-dir",asc?"asc":"desc");
var indicator=th.querySelector(".gg-infographic-sort-indicator");
if(indicator)indicator.textContent=asc?"▲":"▼";
track("infographic_interact",{type:"sortable-table",column:col,direction:asc?"asc":"desc"});
});

/* Range calculator */
document.querySelectorAll("[data-interactive='range-calculator']").forEach(function(calc){
var sliders=calc.querySelectorAll("input[type='range']");
function updateCalc(){
var vals={};
sliders.forEach(function(s){vals[s.name]=parseFloat(s.value);var out=calc.querySelector("output[for='"+s.id+"']");if(out)out.textContent=s.value+(s.getAttribute("data-unit")||"");});
/* Hydration calc formula */
var dur=vals.duration||4;var temp=vals.temp||70;var intensity=vals.intensity||6;
var baseMl=500*dur;var heatAdj=temp>80?1.3:temp>70?1.1:1.0;
var intAdj=intensity>7?1.2:intensity>5?1.1:1.0;
var totalMl=Math.round(baseMl*heatAdj*intAdj);
var sodiumMg=Math.round(totalMl*0.7);
var outFluid=calc.querySelector("[data-result='fluid']");
var outSodium=calc.querySelector("[data-result='sodium']");
var outRate=calc.querySelector("[data-result='rate']");
if(outFluid)outFluid.textContent=(totalMl/1000).toFixed(1)+"L";
if(outSodium)outSodium.textContent=sodiumMg+"mg";
if(outRate)outRate.textContent=Math.round(totalMl/dur)+"ml/hr";
}
sliders.forEach(function(s){s.addEventListener("input",updateCalc);});
updateCalc();
});

/* Gear weight toggle */
document.addEventListener("click",function(e){
var item=e.target.closest("[data-interactive='gear-toggle'] .gg-infographic-gear-item");
if(!item)return;
item.classList.toggle("active");
var container=item.closest("[data-interactive='gear-toggle']");
if(!container)return;
var total=0;
container.querySelectorAll(".gg-infographic-gear-item.active").forEach(function(it){
total+=parseFloat(it.getAttribute("data-weight")||"0");
});
var valEl=container.querySelector(".gg-infographic-gear-total-value");
if(valEl)valEl.textContent=total.toFixed(1)+"kg";
var fillEl=container.querySelector(".gg-infographic-gear-bar-fill");
var maxW=parseFloat(container.getAttribute("data-max-weight")||"12");
if(fillEl)fillEl.style.width=Math.min(100,total/maxW*100)+"%";
track("infographic_interact",{type:"gear-toggle",total:total.toFixed(1)});
});

/* Before/after drag */
(function(){
var active=null;
function startDrag(e){
var ba=e.target.closest("[data-interactive='before-after']");
if(!ba)return;
active=ba;
e.preventDefault();
}
function moveDrag(e){
if(!active)return;
var rect=active.getBoundingClientRect();
var clientX=e.touches?e.touches[0].clientX:e.clientX;
var pct=Math.max(10,Math.min(90,((clientX-rect.left)/rect.width)*100));
var divider=active.querySelector(".gg-infographic-ba-divider");
var afterSide=active.querySelector(".gg-infographic-ba-side:last-of-type");
if(divider)divider.style.left=pct+"%";
if(afterSide)afterSide.style.clipPath="inset(0 0 0 "+pct+"%)";
}
function stopDrag(){
if(active){track("infographic_interact",{type:"before-after"});active=null;}
}
document.addEventListener("mousedown",startDrag);
document.addEventListener("mousemove",moveDrag);
document.addEventListener("mouseup",stopDrag);
document.addEventListener("touchstart",startDrag,{passive:false});
document.addEventListener("touchmove",moveDrag,{passive:false});
document.addEventListener("touchend",stopDrag);
})();

/* Timeline expand */
document.addEventListener("click",function(e){
var header=e.target.closest("[data-interactive='timeline'] .gg-infographic-timeline-header");
if(!header)return;
var node=header.closest(".gg-infographic-timeline-node");
if(node)node.classList.toggle("open");
var expand=header.querySelector(".gg-infographic-timeline-expand");
if(expand)expand.textContent=node.classList.contains("open")?"−":"+";
track("infographic_interact",{type:"timeline"});
});

/* Decision tree interaction */
document.addEventListener("click",function(e){
var btn=e.target.closest(".gg-decision-tree__option");
if(!btn)return;
var tree=btn.closest(".gg-decision-tree");
if(!tree)return;
var treeData;
try{treeData=JSON.parse(tree.getAttribute("data-tree")||"{}");}catch(ex){return;}
var target=btn.getAttribute("data-target");
var isResult=btn.getAttribute("data-is-result")==="true";
if(isResult){
var resultEl=tree.querySelector(".gg-decision-tree__result");
var bodyEl=tree.querySelector(".gg-decision-tree__body");
var restartEl=tree.querySelector(".gg-decision-tree__restart");
if(bodyEl)bodyEl.style.display="none";
if(resultEl){
var resultHtml='<div class="gg-decision-tree__result-title">WE RECOMMEND</div>';
resultHtml+='<div class="gg-decision-tree__result-race">';
resultHtml+='<a href="/race/'+target+'/">'+target.replace(/-/g," ").replace(/\w/g,function(c){return c.toUpperCase();})+'</a>';
resultHtml+='</div>';
resultEl.innerHTML=resultHtml;
resultEl.style.display="block";
}
if(restartEl)restartEl.style.display="block";
track("decision_tree_result",{race:target});
}else{
var node=treeData[target];
if(!node)return;
var qEl=tree.querySelector(".gg-decision-tree__question");
var optsEl=tree.querySelector(".gg-decision-tree__options");
if(qEl)qEl.textContent=node.question||"";
if(optsEl){
optsEl.innerHTML="";
(node.options||[]).forEach(function(opt){
var b=document.createElement("button");
b.className="gg-decision-tree__option";
b.setAttribute("data-target",opt.next||opt.result||"");
b.setAttribute("data-is-result",opt.result?"true":"false");
b.textContent=opt.text||"";
optsEl.appendChild(b);
});
}
track("decision_tree_step",{node:target});
}
});
document.addEventListener("click",function(e){
var btn=e.target.closest(".gg-decision-tree__restart");
if(!btn)return;
var tree=btn.closest(".gg-decision-tree");
if(!tree)return;
var treeData;
try{treeData=JSON.parse(tree.getAttribute("data-tree")||"{}");}catch(ex){return;}
var root=treeData.root;
if(!root)return;
var bodyEl=tree.querySelector(".gg-decision-tree__body");
var resultEl=tree.querySelector(".gg-decision-tree__result");
var qEl=tree.querySelector(".gg-decision-tree__question");
var optsEl=tree.querySelector(".gg-decision-tree__options");
if(bodyEl)bodyEl.style.display="block";
if(resultEl){resultEl.style.display="none";resultEl.innerHTML="";}
btn.style.display="none";
if(qEl)qEl.textContent=root.question||"";
if(optsEl){
optsEl.innerHTML="";
(root.options||[]).forEach(function(opt){
var b=document.createElement("button");
b.className="gg-decision-tree__option";
b.setAttribute("data-target",opt.next||opt.result||"");
b.setAttribute("data-is-result",opt.result?"true":"false");
b.textContent=opt.text||"";
optsEl.appendChild(b);
});
}
track("decision_tree_restart",{});
});

})();