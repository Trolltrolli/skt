(function(){
"use strict";
function install(){
 if(document.getElementById("sktWakeButton"))return;
 var b=document.createElement("button");
 b.id="sktWakeButton";b.type="button";b.textContent="Aktivovat";b.title="Obnovit aktivitu ovládání tabulky";
 b.style.cssText="position:fixed;right:8px;bottom:8px;z-index:2147483647;padding:5px 9px;border:1px solid #666;border-radius:4px;background:#292929;color:#ddd;font:12px Arial;cursor:pointer;box-shadow:0 1px 4px #000;opacity:.82";
 b.addEventListener("click",function(){
  var ok=false;
  try{if(typeof window.sktWakeEditor==="function")ok=window.sktWakeEditor()===true;}catch(e){}
  window.dispatchEvent(new Event("resize"));
  window.dispatchEvent(new Event("scroll"));
  requestAnimationFrame(function(){window.dispatchEvent(new Event("resize"));});
  b.textContent=ok?"Aktivováno":"Zkus znovu";
  b.style.borderColor=ok?"#4a8":"#a66";
  setTimeout(function(){b.textContent="Aktivovat";b.style.borderColor="#666";},1800);
 });
 document.body.appendChild(b);
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",install,{once:true});else install();
})();
