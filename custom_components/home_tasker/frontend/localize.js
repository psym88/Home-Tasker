const CATALOG_URL="/home_tasker_translations";

let messages={};
let language="en";
let appliedLanguage=null;
const loaded=new Map();

function interpolate(value,variables){
  return String(value).replace(/\{(\w+)\}/g,(_,key)=>variables[key]??`{${key}}`);
}

async function loadCatalog(code){
  if(!loaded.has(code)){
    loaded.set(code,fetch(`${CATALOG_URL}/${code}.json`).then(response=>response.ok?response.json():{}).then(catalog=>catalog.frontend||{}).catch(()=>({})));
  }
  return loaded.get(code);
}

export function t(key,variables={}){return interpolate(messages[key]??key,variables);}
export function errorMessage(error){const key=String(error?.code||error?.message||error||"");return messages[`error.${key}`]??error?.message??key;}
export function historyNote(value){return value==="home_tasker.history.completed_via_nfc"?t("history.completed_via_nfc"):value;}
export function locale(){return language;}

export async function setLanguage(value){
  const requested=String(value||"en").toLowerCase().split(/[-_]/)[0];
  const next=/^[a-z]{2,3}$/.test(requested)?requested:"en";
  language=next;
  const fallback=await loadCatalog("en");
  const translated=next==="en"?fallback:await loadCatalog(next);
  const changed=appliedLanguage!==next;
  if(language===next){messages={...fallback,...translated};appliedLanguage=next;}
  return changed;
}

export const ready=setLanguage(globalThis.navigator?.language);
