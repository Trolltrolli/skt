(function(){
'use strict';

const TABLE_ID='tg-uIa8n',
SAVE_ENDPOINT='https://torrexplorer-save.kari1989liska.workers.dev/',
STORAGE_DATA='torrexplorer.table.v3',
STORAGE_BACKUPS='torrexplorer.backups.v3',
INTERNAL_PASSWORD='789456',
MAX_BACKUPS=5,
IMG_BASE='https://trolltrolli.github.io/skt/torrexplorer/covery_seznam/';

let table=null,tbody=null,unlocked=false,dirty=false,modalResolve=null,originalSearchDisplay='',dragRow=null,dragPlaceholder=null,dragPointerId=null,editingRow=null,lockHoldTimer=null,lockHoldFired=false;

const $=(s,r=document)=>r.querySelector(s),
$$=(s,r=document)=>Array.from(r.querySelectorAll(s));

function escapeHtml(v){
return String(v??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#039;')
}

function cleanText(v){
return String(v??'').replace(/\u00a0/g,' ').trim()
}

function isExternalUrl(v){
return /^(?:https?:|magnet:|ftp:|data:)/i.test(String(v||'').trim())
}

function normaliseImagePath(v){
const r=String(v||'').trim();
if(!r)return '';
if(isExternalUrl(r))return r;
const n=r.replace(/^.*[\/]/,'');
return IMG_BASE+encodeURIComponent(n).replace(/%2F/g,'/')
}

function normaliseSavedImagePath(v){
const r=String(v||'').trim();
if(!r)return '';
if(isExternalUrl(r))return r;
const c=r.replace(/^\.\//,'').replace(/^\/?/,'');
if(/^covery_seznam\//i.test(c))
return IMG_BASE+c.substring('covery_seznam/'.length).split('/').map(x=>encodeURIComponent(x)).join('/');
return IMG_BASE+c.split('/').map(x=>encodeURIComponent(x)).join('/')
}

function cellText(td){
if(!td)return '';
const c=td.cloneNode(true);
c.querySelectorAll('.tx-row-actions').forEach(x=>x.remove());
return cleanText(c.textContent||'')
}

function rowToData(row){
const c=row.querySelectorAll(':scope > td'),
img=c[0]?.querySelector('img'),
il=c[0]?.querySelector('a'),
tl=c[1]?.querySelector('a'),
name=c[1]?.querySelector('[itemprop="name"]')||c[1]?.querySelector('span');

return{
image:normaliseSavedImagePath(img?.getAttribute('src')||il?.getAttribute('href')||''),
name:cleanText(name?.textContent||c[1]?.textContent||''),
torrent:tl?.getAttribute('href')||'',
title:tl?.getAttribute('title')||'',
genre:cellText(c[2]),
type:cellText(c[3]),
size:cellText(c[4]),
idt:cellText(c[5])
}
}

function getRowsData(){
return $$(':scope > tr',tbody).map(rowToData)
}

function snapshot(){
return{
version:3,
savedAt:new Date().toISOString(),
rows:getRowsData()
}
}

function loadJson(k,f){
try{
const r=localStorage.getItem(k);
return r?JSON.parse(r):f
}catch(_){
return f
}
}

function saveJson(k,v){
try{
localStorage.setItem(k,JSON.stringify(v));
return true
}catch(_){
return false
}
}

function saveCurrentData(){
saveJson(STORAGE_DATA,snapshot())
}


/* ============================================================
   AUTOMATICKÉ ULOŽENÍ NA GITHUB
   ============================================================ */

async function saveToGitHub(){

const cleanTbody=document.createElement('tbody');

$$(':scope > tr',tbody).forEach(row=>{

const clone=row.cloneNode(true);

clone.querySelectorAll('.tx-row-actions').forEach(x=>x.remove());

clone.removeAttribute('data-editing');
clone.removeAttribute('data-new-row');
clone.removeAttribute('draggable');

clone.classList.remove('tx-dragging','tx-drag-over');

clone.querySelectorAll('[data-field]').forEach(x=>{
x.removeAttribute('data-field')
});

clone.querySelectorAll('.tx-id-value').forEach(x=>{
x.replaceWith(document.createTextNode(x.textContent||''))
});

cleanTbody.appendChild(clone);

});

const response=await fetch(SAVE_ENDPOINT,{
method:'POST',
headers:{
'Content-Type':'application/json'
},
body:JSON.stringify({
tbody:cleanTbody.innerHTML
})
});

let result=null;

try{
result=await response.json()
}catch(_){}

if(!response.ok||!result?.ok){
throw new Error(
result?.error||
'Nepodařilo se uložit změny na GitHub.'
)
}

return result
}


/* ============================================================
   BACKUPS / DATA
   ============================================================ */

function addBackup(state=null){

const s=state||loadJson(STORAGE_DATA,null)||snapshot();

if(!s||!Array.isArray(s.rows))return;

const b=loadJson(STORAGE_BACKUPS,[]);

b.unshift(s);

saveJson(
STORAGE_BACKUPS,
b.slice(0,MAX_BACKUPS)
)
}

function restoreSavedData(){

const s=loadJson(STORAGE_DATA,null);

if(!s||!Array.isArray(s.rows)||!s.rows.length)
return false;

tbody.innerHTML='';

s.rows.forEach(d=>{
tbody.appendChild(createRow(d))
});

renumberRows();

return true
}


/* ============================================================
   ROW CREATION
   ============================================================ */

function createRow(data={}){

const row=document.createElement('tr'),
image=normaliseSavedImagePath(data.image||''),
name=data.name||'',
torrent=data.torrent||'#',
title=data.title||'';

row.innerHTML=
`<td><a href="${escapeHtml(image||'#')}" target="_blank" rel="noopener noreferrer"><img class="center" src="${escapeHtml(image||'core/noimage.png')}" alt=""></a></td><td data-sortvalue="${escapeHtml((name[0]||'').toUpperCase())}"><a style="text-decoration:none" href="${escapeHtml(torrent)}" target="_blank" title="${escapeHtml(title)}" rel="noopener noreferrer"><span style="color:#fff;font-size:15px;float:left"><font itemprop="name">&nbsp;${escapeHtml(name)}</font></span></a></td><td>${escapeHtml(data.genre||'')}</td><td>${escapeHtml(data.type||'')}</td><td>${escapeHtml(data.size||'')}</td><td><span class="tx-id-value">${escapeHtml(data.idt||'')}</span></td>`;

return row
}

function updateRowFromData(row,data){

const c=row.querySelectorAll(':scope > td'),
image=normaliseSavedImagePath(data.image||''),
name=data.name||'';

c[0].innerHTML=
`<a href="${escapeHtml(image||'#')}" target="_blank" rel="noopener noreferrer"><img class="center" src="${escapeHtml(image||'core/noimage.png')}" alt=""></a>`;

c[1].innerHTML=
`<a style="text-decoration:none" href="${escapeHtml(data.torrent||'#')}" target="_blank" title="${escapeHtml(data.title||'')}" rel="noopener noreferrer"><span style="color:#fff;font-size:15px;float:left"><font itemprop="name">&nbsp;${escapeHtml(name)}</font></span></a>`;

c[1].dataset.sortvalue=(name[0]||'').toUpperCase();

c[2].textContent=data.genre||'';
c[3].textContent=data.type||'';
c[4].textContent=data.size||'';

c[5].innerHTML=
`<span class="tx-id-value">${escapeHtml(data.idt||'')}</span>`
}


/* ============================================================
   ID / EDITING
   ============================================================ */

function renumberRows(){

const rows=$$(':scope > tr',tbody),
mw=Math.max(
3,
...rows.map(r=>cleanText(r.cells[5]?.textContent).length)
),
w=Math.max(
3,
String(rows.length).length,
mw>3?mw:3
);

rows.forEach((row,i)=>{

if(row.dataset.editing==='true'){

const input=row.querySelector('[data-field="idt"]');

if(input)
input.value=String(rows.length-i).padStart(w,'0')

}else if(row.cells[5]){

let h=row.cells[5].querySelector('.tx-id-value');

if(!h){

h=document.createElement('span');
h.className='tx-id-value';

row.cells[5].innerHTML='';
row.cells[5].appendChild(h)
}

h.textContent=
String(rows.length-i).padStart(w,'0')

}

})
}

function fieldInput(field,value='',type='text',placeholder=''){

const i=document.createElement('input');

i.type=type;
i.value=value||'';
i.dataset.field=field;
i.className='tx-edit-input';
i.autocomplete='off';

if(placeholder)
i.placeholder=placeholder;

return i
}

function beginRowEdit(row){

if(!unlocked||row.dataset.editing==='true')
return;

if(editingRow&&editingRow!==row){

setStatus(
'Nejdřív potvrď nebo zruš aktuální úpravu.',
'error'
);

return
}

editingRow=row;

const data=rowToData(row);

row.dataset.editing='true';
row._txOriginal=data;

const c=row.querySelectorAll(':scope > td');

c[0].innerHTML='';

const wrap=document.createElement('div');

wrap.className='tx-img-edit';

const imgInput=fieldInput(
'image',
data.image
);

imgInput.addEventListener(
'input',
()=>updateEditImagePreview(
wrap,
imgInput.value
)
);

wrap.appendChild(imgInput);

const preview=document.createElement('img');

preview.className='tx-edit-preview';
preview.src=data.image||'core/noimage.png';

preview.onerror=()=>{
preview.src='core/noimage.png'
};

wrap.appendChild(preview);

c[0].appendChild(wrap);

const isNew=row.dataset.newRow==='true';

const nameInput=
fieldInput(
'name',
data.name,
'text',
isNew?'Název hry':''
);

const torrentInput=
fieldInput(
'torrent',
data.torrent==='#'?'':data.torrent,
'url',
isNew?'Odkaz na stránku torrentu':''
);

const titleInput=
fieldInput(
'title',
data.title,
'text',
isNew?'Tooltip text':''
);

c[1].innerHTML='';

[
nameInput,
torrentInput,
titleInput
].forEach(i=>c[1].appendChild(i));

c[2].innerHTML='';
c[2].appendChild(
fieldInput('genre',data.genre)
);

c[3].innerHTML='';
c[3].appendChild(
fieldInput('type',data.type)
);

c[4].innerHTML='';
c[4].appendChild(
fieldInput('size',data.size)
);

c[5].innerHTML='';

const idInput=
fieldInput('idt',data.idt);

idInput.readOnly=true;
idInput.title='IDT se přečísluje automaticky';

c[5].appendChild(idInput);

[
imgInput,
nameInput,
torrentInput,
titleInput,
c[2].querySelector('input'),
c[3].querySelector('input'),
c[4].querySelector('input')
].forEach(i=>{

if(i)
i.addEventListener(
'input',
()=>{
dirty=true
}
)

});

refreshRowActions(row);
updateHeaderEditButtons();
renumberRows();

nameInput.focus();
nameInput.select()
}

function updateEditImagePreview(wrap,value){

const p=wrap.querySelector('.tx-edit-preview');

if(!p)return;

p.src=
normaliseSavedImagePath(value)||
'core/noimage.png'
}

function collectEditedRow(row){

const get=f=>
row.querySelector(
`[data-field="${f}"]`
)?.value||'';

return{
image:get('image'),
name:get('name'),
torrent:get('torrent'),
title:get('title'),
genre:get('genre'),
type:get('type'),
size:get('size'),
idt:get('idt')
}
}

function finishRowEdit(row,commit){

if(!row||row.dataset.editing!=='true')
return;

const data=
commit?
collectEditedRow(row):
row._txOriginal;

updateRowFromData(row,data);

delete row._txOriginal;

row.dataset.editing='false';

delete row.dataset.newRow;

if(editingRow===row)
editingRow=null;

refreshRowActions(row);
updateHeaderEditButtons();
renumberRows()
}

function cancelRowEdit(row){

if(!row||row.dataset.editing!=='true')
return;

if(row.dataset.newRow==='true'){

row.remove();

if(editingRow===row)
editingRow=null;

dirty=true;

updateHeaderEditButtons();
renumberRows();

return
}

finishRowEdit(row,false);

dirty=true
}


/* ============================================================
   ROW BUTTONS / DRAG
   ============================================================ */

function makeButton(cls,label,title,handler){

const b=document.createElement('button');

b.type='button';
b.className=`tx-row-btn ${cls}`;
b.textContent=label;
b.title=title;
b.setAttribute('aria-label',title);

b.addEventListener(
'click',
e=>{
e.preventDefault();
e.stopPropagation();
handler()
}
);

return b
}

function startRowDrag(e,row){

if(!unlocked||row.dataset.editing==='true'||dragRow)
return;

if(editingRow){

setStatus(
'Nejdřív dokonči úpravu řádku.',
'error'
);

return
}

e.preventDefault();
e.stopPropagation();

dragRow=row;
dragPointerId=e.pointerId;

row.classList.add('tx-dragging');

const h=row.getBoundingClientRect().height;

dragPlaceholder=document.createElement('tr');

dragPlaceholder.className=
'tx-drag-placeholder';

dragPlaceholder.innerHTML=
`<td colspan="${row.cells.length}"></td>`;

dragPlaceholder.style.height=
`${Math.max(28,h)}px`;

tbody.insertBefore(
dragPlaceholder,
row
);

row.style.display='none';

try{
e.currentTarget.setPointerCapture(e.pointerId)
}catch(_){}
}

function moveRowDrag(e){

if(!dragRow||e.pointerId!==dragPointerId)
return;

const el=
document.elementFromPoint(
e.clientX,
e.clientY
);

const target=el?.closest('tr');

if(
!target||
target===dragRow||
target===dragPlaceholder||
target.parentNode!==tbody
)
return;

const r=target.getBoundingClientRect(),
after=e.clientY>r.top+r.height/2;

if(after){

if(target.nextSibling!==dragPlaceholder)
tbody.insertBefore(
dragPlaceholder,
target.nextSibling
)

}else if(
target!==dragPlaceholder.nextSibling
){

tbody.insertBefore(
dragPlaceholder,
target
)

}

tbody
.querySelectorAll('.tx-drag-over')
.forEach(x=>
x.classList.remove('tx-drag-over')
);

target.classList.add('tx-drag-over')
}

function endRowDrag(e){

if(!dragRow)
return;

if(
dragPointerId!=null&&
e.pointerId!=null&&
e.pointerId!==dragPointerId
)
return;

tbody
.querySelectorAll('.tx-drag-over')
.forEach(x=>
x.classList.remove('tx-drag-over')
);

if(dragPlaceholder){

tbody.insertBefore(
dragRow,
dragPlaceholder
);

dragPlaceholder.remove()
}

dragRow.style.display='';
dragRow.classList.remove('tx-dragging');

dragRow=null;
dragPlaceholder=null;
dragPointerId=null;

dirty=true;

renumberRows();
refreshAllActions()
}

function refreshRowActions(row){

let box=row.querySelector('.tx-row-actions');

if(!box){

box=document.createElement('div');
box.className='tx-row-actions';

const cell=row.cells[1];

if(cell)
cell.appendChild(box)
}

box.innerHTML='';

box.appendChild(
makeButton(
'tx-add',
'+',
'Přidat řádek pod tento',
()=>insertRowAfter(row)
)
);

const move=
makeButton(
'tx-move',
'↕',
'Přesunout řádek',
()=>{}
);

move.addEventListener(
'pointerdown',
e=>startRowDrag(e,row)
);

box.appendChild(move);

box.appendChild(
makeButton(
'tx-edit',
'✎',
'Upravit řádek',
()=>beginRowEdit(row)
)
);

box.appendChild(
makeButton(
'tx-delete',
'×',
'Smazat řádek',
()=>deleteRow(row)
)
)
}

function refreshAllActions(){

getRowsData();

$$(':scope > tr',tbody)
.forEach(refreshRowActions);

setEditabilityState()
}

function insertRowAfter(row){

if(!unlocked)
return;

if(editingRow){

setStatus(
'Nejdřív dokonči úpravu řádku',
'error'
);

return
}

const n=createRow({
image:'',
name:'',
torrent:'',
title:'',
genre:'',
type:'',
size:'',
idt:''
});

n.dataset.newRow='true';

row.after(n);

dirty=true;

refreshRowActions(n);
renumberRows();
beginRowEdit(n)
}

function deleteRow(row){

if(!unlocked)
return;

if(editingRow){

setStatus(
'Nejdřív dokonči úpravu řádku',
'error'
);

return
}

if(!confirm(
'Opravdu chceš tento řádek smazat?'
))
return;

row.remove();

dirty=true;

renumberRows();
refreshAllActions()
}


/* ============================================================
   EDITABILITY
   ============================================================ */

function setEditabilityState(){

table.classList.toggle(
'tx-unlocked',
unlocked
);

updateLockButton();
updateBackupButton();
updateHeaderEditButtons();

if(unlocked){

originalSearchDisplay=
originalSearchDisplay||
getComputedStyle(
$('.fancy-search')||document.body
).display;

const s=$('.fancy-search');

if(s)
s.style.display='none'

}else{

const s=$('.fancy-search');

if(s&&originalSearchDisplay)
s.style.display=
originalSearchDisplay
}
}


/* ============================================================
   PASSWORD
   ============================================================ */

function showPasswordDialog(){

return new Promise(resolve=>{

modalResolve=resolve;

const o=$('#txPasswordOverlay'),
t=$('#txPasswordTitle'),
h=$('#txPasswordHint'),
c=$('#txPasswordConfirm'),
s=$('#txPasswordSecondWrap'),
i=$('#txPasswordInput'),
i2=$('#txPasswordInput2');

t.textContent='Odemknout úpravy';
h.textContent='Zadej interní heslo pro úpravy';
c.textContent='Potvrdit';

s.hidden=true;

i.value='';
i2.value='';

o.classList.add('visible');

setTimeout(
()=>i.focus(),
30
)

})
}

function closePasswordDialog(result){

const o=$('#txPasswordOverlay');

o.classList.remove('visible');

if(modalResolve){

const r=modalResolve;

modalResolve=null;

r(result)
}
}

async function requestUnlock(){

const password=
await showPasswordDialog();

return!!password&&
password.password===INTERNAL_PASSWORD
}


/* ============================================================
   LOCK / AUTOMATICKÉ ULOŽENÍ
   ============================================================ */

async function toggleLock(){

if(unlocked){

if(editingRow)
finishRowEdit(editingRow,true);

renumberRows();

addBackup(
loadJson(STORAGE_DATA,null)||
snapshot()
);

saveCurrentData();

setStatus(
'Ukládám změny na GitHub...'
);

try{

await saveToGitHub();

dirty=false;
unlocked=false;

setEditabilityState();

setStatus(
'Uloženo. GitHub aktualizován.',
'ok'
);

}catch(error){

setStatus(
`Chyba ukládání: ${error.message}`,
'error'
);

return
}

return
}

if(!(await requestUnlock())){

setStatus(
'Nesprávné heslo',
'error'
);

return
}

unlocked=true;

setEditabilityState();

setStatus(
'Režim úprav odemčen',
'ok'
)
}

function updateLockButton(){

const b=$('#txLockButton');

if(!b)
return;

b.classList.toggle(
'unlocked',
unlocked
);

b.title=
unlocked?
'Uložit změny a uzamknout':
'Odemknout úpravy';

b.setAttribute(
'aria-label',
b.title
)
}

function updateBackupButton(){

const b=$('#txBackupButton');

if(!b)
return;

b.style.display=
unlocked?
'inline-block':
'none'
}

function updateHeaderEditButtons(){

const ok=$('#txHeaderEditOk'),
cancel=$('#txHeaderEditCancel'),
active=!!(
unlocked&&
editingRow&&
editingRow.dataset.editing==='true'
);

if(ok)
ok.style.display=
active?
'inline-block':
'none';

if(cancel)
cancel.style.display=
active?
'inline-block':
'none'
}

function setStatus(text,kind=''){

const s=$('#txEditStatus');

if(!s)
return;

s.textContent=text;

s.className=
`tx-edit-status ${kind}`;

clearTimeout(setStatus.timer);

setStatus.timer=
setTimeout(()=>{

s.textContent='';
s.className='tx-edit-status'

},2500)
}


/* ============================================================
   UI
   ============================================================ */

function buildUi(){

const host=document.createElement('div');

host.id='txEditorUi';

host.innerHTML=
`<div id="txEditStatus" class="tx-edit-status"></div><div id="txPasswordOverlay" class="tx-password-overlay" role="dialog" aria-modal="true" aria-labelledby="txPasswordTitle"><div class="tx-password-box"><div id="txPasswordTitle" class="tx-password-title"></div><div id="txPasswordHint" class="tx-password-hint"></div><input id="txPasswordInput" class="tx-password-input" type="password" autocomplete="current-password"><div id="txPasswordSecondWrap" class="tx-password-second"><input id="txPasswordInput2" class="tx-password-input" type="password" autocomplete="new-password" placeholder="Zopakovat heslo"></div><div class="tx-password-actions"><button id="txPasswordCancel" type="button">Zrušit</button><button id="txPasswordConfirm" type="button">Odemknout</button></div></div></div>`;

document.body.appendChild(host);

const titleCell=
table.querySelector(
'thead th:nth-child(2)'
),
wrap=
table.closest('.tg-wrap');

if(titleCell&&wrap){

titleCell.classList.add(
'tx-editor-header-cell'
);

const headerActions=
document.createElement('div');

headerActions.id=
'txHeaderActions';

headerActions.innerHTML=
`<button id="txHeaderEditOk" class="tx-header-btn tx-header-edit-ok" type="button" aria-label="Potvrdit editaci řádku" title="Potvrdit editaci řádku">✓</button><button id="txHeaderEditCancel" class="tx-header-btn tx-header-edit-cancel" type="button" aria-label="Zrušit editaci řádku" title="Zrušit editaci řádku">↶</button><button id="txLockButton" class="tx-header-btn tx-header-lock" type="button" aria-label="Odemknout úpravy" title="Odemknout úpravy"><span class="tx-lock-shape"><i></i></span></button><button id="txBackupButton" class="tx-header-btn tx-header-backup" type="button" aria-label="Obnovit poslední backup" title="Obnovit poslední backup">↶</button>`;

wrap.appendChild(headerActions);

const stop=e=>{
e.stopPropagation()
};

[
'pointerdown',
'mousedown',
'click',
'dblclick'
].forEach(t=>
headerActions.addEventListener(
t,
stop
)
);

const seed=
document.createElement('div');

seed.id='txSeed';

seed.innerHTML=
'<div class="tx-seed-track"><div class="tx-seed-text">SEED VĚTŠINOU VEČER</div></div>';

wrap.appendChild(seed);

const positionHeader=()=>{

const wr=wrap.getBoundingClientRect(),
hr=titleCell.getBoundingClientRect();

headerActions.style.left=
`${Math.max(
0,
hr.right-wr.left-108
)}px`;

headerActions.style.top=
`${Math.max(
0,
hr.top-wr.top+3
)}px`
};

const positionSeed=()=>{

const wr=wrap.getBoundingClientRect(),
ir=
table.querySelector(
'thead th:nth-child(1)'
)?.getBoundingClientRect(),
tr=
titleCell?.getBoundingClientRect();

if(!ir||!tr)
return;

seed.style.left=
`${Math.max(
0,
ir.right-wr.left+4
)}px`;

seed.style.top=
`${Math.max(
0,
tr.top-wr.top
)}px`;

seed.style.width='118px';

seed.style.height=
`${Math.max(
20,
tr.height
)}px`
};

requestAnimationFrame(()=>{
positionHeader();
positionSeed()
});

window.addEventListener(
'resize',
()=>{
positionHeader();
positionSeed()
}
);

window.addEventListener(
'scroll',
()=>{
positionHeader();
positionSeed()
},
{passive:true}
)
}

const lockButton=
$('#txLockButton');

lockButton.addEventListener(
'pointerdown',
e=>{

if(unlocked)
return;

lockHoldFired=false;

clearTimeout(lockHoldTimer);

lockHoldTimer=
setTimeout(()=>{

lockHoldTimer=null;
lockHoldFired=true;

toggleLock()

},2000)
});

[
'pointerup',
'pointercancel',
'pointerleave'
].forEach(t=>
lockButton.addEventListener(
t,
()=>{
clearTimeout(lockHoldTimer);
lockHoldTimer=null
}
)
);

lockButton.addEventListener(
'click',
e=>{

if(unlocked){

toggleLock();

return
}

if(!lockHoldFired)
e.preventDefault();

lockHoldFired=false
}
);

$('#txHeaderEditOk').addEventListener(
'click',
()=>{
if(editingRow)
finishRowEdit(
editingRow,
true
)
}
);

$('#txHeaderEditCancel').addEventListener(
'click',
()=>{
if(editingRow)
cancelRowEdit(
editingRow
)
}
);

$('#txBackupButton').addEventListener(
'click',
restoreLastBackup
);

$('#txPasswordCancel').addEventListener(
'click',
()=>{
closePasswordDialog(null)
}
);

$('#txPasswordConfirm').addEventListener(
'click',
()=>{
const p=
$('#txPasswordInput').value;

closePasswordDialog({
password:p
})
}
);

[
'#txPasswordInput',
'#txPasswordInput2'
].forEach(sel=>
$(sel).addEventListener(
'keydown',
e=>{

if(e.key==='Enter')
$('#txPasswordConfirm').click();

if(e.key==='Escape')
$('#txPasswordCancel').click()

}
)
);

$('#txHeaderEditOk').style.display='none';
$('#txHeaderEditCancel').style.display='none';
$('#txBackupButton').style.display='none'
}


/* ============================================================
   BACKUP RESTORE
   ============================================================ */

function restoreLastBackup(){

if(!unlocked)
return;

if(editingRow){

setStatus(
'Nejdřív dokonči úpravu řádku.',
'error'
);

return
}

const b=
loadJson(
STORAGE_BACKUPS,
[]
);

if(!Array.isArray(b)||!b.length){

setStatus(
'Žádný backup není k dispozici',
'error'
);

return
}

if(!confirm(
'Obnovit poslední backup? Aktuální neuložené změny budou nahrazeny'
))
return;

const s=b[0];

if(!s||!Array.isArray(s.rows))
return;

tbody.innerHTML='';

s.rows.forEach(d=>
tbody.appendChild(
createRow(d)
)
);

renumberRows();
refreshAllActions();

dirty=true;

setStatus(
'Poslední backup obnoven.',
'ok'
)
}


/* ============================================================
   IMAGE PREVIEW
   ============================================================ */

function installImagePreview(){

const preview=
document.createElement('img');

preview.className=
'tx-image-preview';

preview.alt='';

document.body.appendChild(preview);

let active=null;

function move(e){

if(
!active||
preview.style.display!=='block'
)
return;

const gap=14,
margin=10,
r=preview.getBoundingClientRect();

let x=e.clientX+gap,
y=e.clientY+gap;

if(x+r.width>innerWidth-margin)
x=e.clientX-r.width-gap;

if(y+r.height>innerHeight-margin)
y=e.clientY-r.height-gap;

if(x<margin)
x=margin;

if(y<margin)
y=margin;

preview.style.left=`${x}px`;
preview.style.top=`${y}px`
}

function show(img,e){

if(!img?.src)
return;

active=img;

preview.src=
img.currentSrc||
img.src;

preview.style.display='block';

requestAnimationFrame(
()=>move(e)
)
}

function hide(){

active=null;

preview.style.display='none';

preview.removeAttribute('src')
}

document.addEventListener(
'mouseover',
e=>{

const img=
e.target.closest(
`#${TABLE_ID} img.center`
);

if(img)
show(img,e)
}
);

document.addEventListener(
'mousemove',
e=>{
if(active)
move(e)
}
);

document.addEventListener(
'mouseout',
e=>{

const img=
e.target.closest(
`#${TABLE_ID} img.center`
);

if(
img&&
(!e.relatedTarget||
!img.contains(e.relatedTarget))
)
hide()

}
);

window.addEventListener(
'resize',
hide
);

window.addEventListener(
'scroll',
hide,
{passive:true}
)
}


/* ============================================================
   STYLES
   ============================================================ */

function addStyles(){

const style=
document.createElement('style');

style.textContent=`

.tg-wrap{position:relative!important}

#${TABLE_ID}{
border-collapse:separate!important;
border-spacing:0!important
}

#${TABLE_ID}>tbody>tr:nth-child(odd)>td{
background:#1a1a1a;
background-image:-webkit-linear-gradient(
top,
rgba(40,40,40,.88) 3%,
rgba(65,65,65,.73) 17%,
rgba(68,68,68,.33) 89%,
rgba(68,68,68,.88) 42%,
rgba(63,63,63,.79) 45%,
rgba(61,61,61,.75) 77%,
rgba(56,56,56,.17) 86%,
rgba(27,27,27,1) 100%
)
}

#${TABLE_ID}>tbody>tr:nth-child(even)>td{
background-color:#565657;
background-image:-webkit-linear-gradient(
top,
rgba(40,40,40,.88) 3%,
rgba(65,65,65,.73) 17%,
rgba(68,68,68,.33) 89%,
rgba(68,68,68,.88) 42%,
rgba(63,63,63,.79) 45%,
rgba(61,61,61,.75) 77%,
rgba(56,56,56,.17) 86%,
rgba(27,27,27,1) 100%
)
}

#${TABLE_ID}>thead{
position:sticky!important;
top:0!important;
z-index:9000!important
}

#${TABLE_ID}>thead>tr>th{
position:sticky!important;
top:0!important;
z-index:9001!important
}

#${TABLE_ID}>thead>tr>th:first-child{
z-index:9002!important
}

#${TABLE_ID}>thead>tr>th:nth-child(2){
z-index:9003!important
}

#${TABLE_ID}>thead>tr>th:nth-child(3),
#${TABLE_ID}>thead>tr>th:nth-child(4),
#${TABLE_ID}>thead>tr>th:nth-child(5),
#${TABLE_ID}>thead>tr>th:nth-child(6){
z-index:9002!important
}

.tx-editor-header-cell{
position:sticky!important;
top:0!important;
padding-right:112px!important;
overflow:visible!important
}

#txHeaderActions{
position:absolute;
pointer-events:auto;
display:flex;
align-items:center;
justify-content:flex-end;
gap:2px;
width:108px;
height:29px;
box-sizing:border-box;
z-index:1000000;
padding:1px;
border:1px solid transparent;
border-radius:5px;
background:transparent;
box-shadow:none
}

.tx-header-btn{
width:25px;
pointer-events:auto;
height:23px;
padding:0;
margin:0;
border:1px solid #111;
border-radius:4px;
background:linear-gradient(#555,#222);
color:#ddd;
box-shadow:0 1px 3px #000;
cursor:pointer
}

.tx-header-lock{
background:transparent;
border:none;
box-shadow:none
}

.tx-header-lock:hover{
background:transparent!important;
border:none!important;
box-shadow:none!important;
filter:none!important
}

.tx-header-btn:hover{
filter:brightness(1.25)
}

.tx-header-edit-ok{
color:#55ff55!important;
font:bold 18px/21px Arial
}

.tx-header-edit-cancel{
color:#ff5555!important;
font:bold 18px/21px Arial
}

.tx-header-backup{
display:none
}

.tx-header-lock.unlocked{
border-color:#9b7a1b;
background:linear-gradient(#6b5a24,#29230e)
}

.tx-lock-shape{
display:block;
position:relative;
width:13px;
height:13px;
margin:auto;
border:2px solid #222;
border-radius:3px;
box-sizing:border-box;
box-shadow:inset 0 0 3px #000
}

.tx-lock-shape i{
position:absolute;
width:4px;
height:4px;
left:50%;
top:50%;
transform:translate(-50%,-50%);
border-radius:50%;
background:#333
}

.tx-header-lock.unlocked .tx-lock-shape{
border-color:#ffd45a
}

.tx-header-lock.unlocked .tx-lock-shape i{
background:#ffd45a;
box-shadow:0 0 5px #ffd45a
}

#txSeed{
position:absolute;
left:0;
top:0;
width:118px;
height:24px;
overflow:hidden;
pointer-events:none;
z-index:10000;
border:0;
box-sizing:border-box
}

.tx-seed-track{
position:absolute;
inset:0;
overflow:hidden;
white-space:nowrap
}

.tx-seed-text{
position:absolute;
top:3px;
left:100%;
will-change:transform;
color:red;
font-size:11px;
line-height:15px;
white-space:nowrap;
text-shadow:
0 0 1px #000,
1px 1px 2px #010a17,
1px 0 0 darkred,
0 0 .5px silver;
animation:txSeedScroll 5s linear infinite
}

@keyframes txSeedScroll{
0%{
transform:translateX(0)
}
100%{
transform:translateX(
calc(-100% - 118px)
)
}
}

.tx-row-actions{
display:none;
position:absolute;
right:4px;
top:50%;
transform:translateY(-50%);
width:106px;
height:24px;
overflow:visible;
gap:2px;
z-index:200;
align-items:center;
justify-content:flex-end
}

#${TABLE_ID}.tx-unlocked td:nth-child(2){
position:relative
}

#${TABLE_ID}.tx-unlocked .tx-row-actions{
display:flex
}

.tx-row-btn{
width:24px;
height:22px;
padding:0;
margin:0;
border:1px solid #111;
border-radius:4px;
color:#eee;
font:bold 16px/20px Arial;
background:linear-gradient(#555,#222);
box-shadow:0 1px 3px #000;
cursor:pointer
}

.tx-row-btn:hover{
filter:brightness(1.3)
}

.tx-add{
color:#fff
}

.tx-move{
color:#ddd;
font-size:18px;
cursor:grab
}

.tx-move:active{
cursor:grabbing
}

.tx-edit{
color:#ddd;
background:transparent
}

.tx-delete{
color:#ff5555;
font-size:20px
}

.tx-dragging{
opacity:.35
}

.tx-drag-over>td{
box-shadow:
inset 0 2px 0 #d1aa43,
inset 0 -2px 0 #d1aa43
}

.tx-drag-placeholder>td{
height:28px!important;
padding:0!important;
border:2px dashed #777!important;
background:rgba(80,80,80,.18)!important;
box-sizing:border-box
}

#${TABLE_ID}.tx-unlocked tr[data-editing="true"]{
position:relative;
height:28px!important
}

#${TABLE_ID}.tx-unlocked tr[data-editing="true"]>td{
position:relative!important;
height:28px!important;
min-height:28px!important;
max-height:28px!important;
overflow:visible!important;
vertical-align:top!important;
box-sizing:border-box
}

.tx-edit-input{
position:absolute;
left:4px;
top:2px;
width:calc(100% - 8px);
min-width:0;
height:24px;
box-sizing:border-box;
margin:0;
padding:3px 6px;
border:1px solid #777;
border-radius:3px;
background:#151515;
color:#fff;
font:13px Arial;
outline:none;
z-index:500
}

.tx-edit-input::placeholder{
color:#777;
opacity:1
}

.tx-edit-input:focus{
border-color:#d1aa43;
box-shadow:0 0 4px rgba(209,170,67,.5)
}

td:nth-child(2) .tx-edit-input[data-field="torrent"]{
top:31px
}

td:nth-child(2) .tx-edit-input[data-field="title"]{
top:60px
}

.tx-img-edit{
position:static;
min-width:0;
width:100%
}

.tx-img-edit .tx-edit-input{
left:3px;
width:calc(100% - 6px)
}

.tx-edit-preview{
position:absolute;
left:calc(50% + 5px);
top:31px;
transform:translateX(-50%);
width:45px;
height:45px;
object-fit:contain;
margin:0;
border:1px solid #555;
background:#111;
z-index:501
}

#${TABLE_ID} img.center:hover{
position:static!important;
transform:none!important;
width:22px!important;
height:24px!important;
padding-left:0!important;
top:auto!important;
border:2px solid #000!important;
box-shadow:2px 2px 3px #000!important
}

.tx-image-preview{
position:fixed;
display:none;
left:0;
top:0;
width:auto;
height:auto;
max-width:520px;
max-height:75vh;
object-fit:contain;
margin:0;
padding:0;
border:2px solid #111;
border-radius:4px;
background:#111;
box-shadow:
0 8px 35px #000,
0 0 12px rgba(0,0,0,.8);
z-index:10000000;
pointer-events:none
}

.tx-password-overlay{
display:none;
position:fixed;
inset:0;
z-index:100000;
background:rgba(0,0,0,.72);
align-items:center;
justify-content:center
}

.tx-password-overlay.visible{
display:flex
}

.tx-password-box{
width:340px;
max-width:calc(100vw - 30px);
padding:18px;
border:1px solid #777;
border-radius:9px;
background:linear-gradient(#353535,#171717);
color:#eee;
box-shadow:0 8px 35px #000
}

.tx-password-title{
font:bold 17px Arial;
margin-bottom:7px
}

.tx-password-hint{
color:#aaa;
font:12px Arial;
margin-bottom:12px
}

.tx-password-input{
box-sizing:border-box;
width:100%;
height:34px;
margin-bottom:8px;
padding:6px 9px;
border:1px solid #666;
border-radius:4px;
background:#0d0d0d;
color:#fff
}

.tx-password-actions{
display:flex;
justify-content:flex-end;
gap:7px;
margin-top:5px
}

.tx-password-actions button{
padding:7px 12px;
border:1px solid #666;
border-radius:4px;
background:#292929;
color:#eee;
cursor:pointer
}

.tx-password-actions button:last-child{
background:#4c421d;
border-color:#a98b36
}

.tx-edit-status{
position:fixed;
right:55px;
top:38px;
z-index:99998;
color:#ddd;
font:12px Arial;
text-shadow:0 1px #000;
pointer-events:none
}

.tx-edit-status.ok{
color:#8fe88f
}

.tx-edit-status.error{
color:#ff7777
}

@media(max-width:900px){

#txHeaderActions{
width:108px
}

.tx-editor-header-cell{
padding-right:112px!important
}

}
`;

document.head.appendChild(style)
}


/* ============================================================
   INIT
   ============================================================ */

function init(){

table=document.getElementById(TABLE_ID);

if(!table)
return;

tbody=table.querySelector('tbody');

if(!tbody)
return;

addStyles();
installImagePreview();
buildUi();
restoreSavedData();
renumberRows();
refreshAllActions();
updateHeaderEditButtons()
}

if(document.readyState==='loading')
document.addEventListener(
'DOMContentLoaded',
init
);
else
init();

})();