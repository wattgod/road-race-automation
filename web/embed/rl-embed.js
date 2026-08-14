(function(){
  "use strict";
  var SITE="https://roadielabs.com";
  var DATA_URL=SITE+"/embed/embed-data.json";
  var CSS=`
.rl-embed-card{font-family:'Sometype Mono',ui-monospace,monospace;border:3px solid #1a1a1a;background:#f5f5f0;padding:14px 16px;max-width:340px;color:#1a1a1a;line-height:1.4;box-sizing:border-box}
.rl-embed-card *{box-sizing:border-box;margin:0;padding:0;border-radius:0}
.rl-embed-card a{color:inherit;text-decoration:none}
.rl-embed-card a:hover{text-decoration:underline}
.rl-embed-top{display:flex;justify-content:space-between;align-items:flex-start;gap:10px;margin-bottom:8px}
.rl-embed-name{font-size:14px;font-weight:700;flex:1}
.rl-embed-tier{display:inline-block;padding:2px 8px;font-size:11px;font-weight:700;color:#fff;letter-spacing:1px;white-space:nowrap}
.rl-embed-tier-1{background:#555555}
.rl-embed-tier-2{background:#4a4a4a}
.rl-embed-tier-3{background:#666666}
.rl-embed-tier-4{background:#777777}
.rl-embed-score-row{display:flex;align-items:center;gap:8px;margin-bottom:6px}
.rl-embed-score-num{font-size:20px;font-weight:700;min-width:36px}
.rl-embed-score-bar{flex:1;height:8px;background:#d0d0c8;position:relative}
.rl-embed-score-fill{position:absolute;top:0;left:0;height:100%;background:#555555}
.rl-embed-meta{font-size:11px;color:#4a4a4a;display:flex;flex-wrap:wrap;gap:4px 12px;margin-bottom:8px}
.rl-embed-link{display:block;font-size:11px;font-weight:700;color:#333333;letter-spacing:0.5px}
.rl-embed-link:hover{text-decoration:underline}
.rl-embed-powered{font-size:9px;color:#4a4a4a;margin-top:6px;text-align:right}
`;

  var styleInjected=false;
  function injectCSS(){
    if(styleInjected)return;
    var s=document.createElement("style");
    s.textContent=CSS;
    document.head.appendChild(s);
    styleInjected=true;
  }

  var dataCache=null;
  var dataCallbacks=[];
  var dataLoading=false;

  function fetchData(cb){
    if(dataCache){cb(dataCache);return}
    dataCallbacks.push(cb);
    if(dataLoading)return;
    dataLoading=true;
    var x=new XMLHttpRequest();
    x.open("GET",DATA_URL,true);
    x.onload=function(){
      if(x.status===200){
        try{dataCache=JSON.parse(x.responseText)}catch(e){dataCache=[]}
      }else{dataCache=[]}
      for(var i=0;i<dataCallbacks.length;i++)dataCallbacks[i](dataCache);
      dataCallbacks=[];
    };
    x.onerror=function(){
      dataCache=[];
      for(var i=0;i<dataCallbacks.length;i++)dataCallbacks[i](dataCache);
      dataCallbacks=[];
    };
    x.send();
  }

  function renderCard(el,race){
    var tier=race.t;
    var tierLabel="T"+tier;
    var score=race.sc;
    var html='<div class="rl-embed-card">';
    html+='<div class="rl-embed-top">';
    html+='<a href="'+race.u+'" target="_blank" rel="noopener" class="rl-embed-name">'+esc(race.n)+'</a>';
    html+='<span class="rl-embed-tier rl-embed-tier-'+tier+'">'+tierLabel+'</span>';
    html+='</div>';
    html+='<div class="rl-embed-score-row">';
    html+='<span class="rl-embed-score-num">'+score+'</span>';
    html+='<div class="rl-embed-score-bar"><div class="rl-embed-score-fill" style="width:'+score+'%"></div></div>';
    html+='</div>';
    html+='<div class="rl-embed-meta">';
    if(race.l)html+='<span>'+esc(race.l)+'</span>';
    if(race.d)html+='<span>'+esc(race.d)+'</span>';
    html+='</div>';
    html+='<a href="'+race.u+'" target="_blank" rel="noopener" class="rl-embed-link">View on Roadie Labs &rarr;</a>';
    html+='<div class="rl-embed-powered"><a href="'+SITE+'" target="_blank" rel="noopener">Powered by Roadie Labs</a></div>';
    html+='</div>';
    el.innerHTML=html;

    // GA4 event
    if(typeof gtag==="function"){
      try{gtag("event","embed_load",{race_slug:race.s,race_tier:tier})}catch(e){}
    }
  }

  function esc(s){
    var d=document.createElement("div");
    d.textContent=s;
    return d.innerHTML;
  }

  function init(){
    injectCSS();
    var els=document.querySelectorAll(".rl-embed[data-slug]");
    if(!els.length)return;
    fetchData(function(data){
      var map={};
      for(var i=0;i<data.length;i++)map[data[i].s]=data[i];
      for(var j=0;j<els.length;j++){
        var slug=els[j].getAttribute("data-slug");
        var race=map[slug];
        if(race){
          renderCard(els[j],race);
        }else{
          els[j].innerHTML='<div class="rl-embed-card" style="text-align:center;padding:20px"><span style="color:#4a4a4a">Race not found: '+esc(slug)+'</span></div>';
        }
      }
    });
  }

  if(document.readyState==="loading"){
    document.addEventListener("DOMContentLoaded",init);
  }else{
    init();
  }
})();
