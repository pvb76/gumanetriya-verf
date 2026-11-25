(function(){var b=document.querySelector('.burger'),n=document.getElementById('nav');if(b&&n){
b.addEventListener('click',function(){var o=n.classList.toggle('open');b.setAttribute('aria-expanded',o)});
n.addEventListener('click',function(e){if(e.target.tagName==='A'){n.classList.remove('open');b.setAttribute('aria-expanded','false')}});}
var rm=window.matchMedia('(prefers-reduced-motion: reduce)').matches,fine=window.matchMedia('(hover: hover) and (pointer: fine)').matches;
if(rm)return;
var sc=document.querySelector('[data-par]');
if(sc&&fine){var hero=sc.closest('.hero')||document.body,raf=0;
hero.addEventListener('pointermove',function(e){var r=hero.getBoundingClientRect(),x=(e.clientX-r.left)/r.width-.5,y=(e.clientY-r.top)/r.height-.5;
cancelAnimationFrame(raf);raf=requestAnimationFrame(function(){sc.style.transform='rotateX('+(8-y*8).toFixed(2)+'deg) rotateY('+(-14+x*14).toFixed(2)+'deg)'})});
hero.addEventListener('pointerleave',function(){sc.style.transform=''});}
if(!fine)return;
document.querySelectorAll('.tilt,.ex,.chan a').forEach(function(el){
el.addEventListener('pointermove',function(e){var r=el.getBoundingClientRect(),x=(e.clientX-r.left)/r.width-.5,y=(e.clientY-r.top)/r.height-.5;
el.style.transform='rotateX('+(-y*6).toFixed(2)+'deg) rotateY('+(x*8).toFixed(2)+'deg) translateZ(6px)';el.classList.add('is-tilt')});
el.addEventListener('pointerleave',function(){el.style.transform='';el.classList.remove('is-tilt')});});
})();

(function(){try{var u='/hit?p='+encodeURIComponent(location.pathname)+'&r='+encodeURIComponent(document.referrer||'');if(navigator.sendBeacon){navigator.sendBeacon(u)}else{fetch(u,{method:'POST',keepalive:true})}}catch(e){}})();
