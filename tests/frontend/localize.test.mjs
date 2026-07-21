import assert from "node:assert/strict";
import {readFileSync,readdirSync} from "node:fs";
import test from "node:test";

const catalog=language=>JSON.parse(readFileSync(new URL(`../../custom_components/home_tasker/translations/${language}.json`,import.meta.url),"utf8"));
globalThis.fetch=async url=>{const language=String(url).match(/\/([a-z]{2,3})\.json$/)?.[1]||"en";return {ok:true,json:async()=>catalog(language)};};

const {ready,setLanguage,t}=await import("../../custom_components/home_tasker/frontend/localize.js");
await ready;

test("English is loaded as the complete fallback catalog",async()=>{
  await setLanguage("en-US");
  assert.equal(t("common.add_task"),"Add task");
  assert.equal(t("task.complete_confirm",{name:"Laundry"}),"Do you want to mark “Laundry” as completed?");
  assert.ok(Object.keys(catalog("en").frontend).length>50);
});

test("German translations share the consolidated Home Assistant catalog",async()=>{
  const english=catalog("en"),german=catalog("de");
  assert.ok(english.config&&german.config);
  assert.deepEqual(Object.keys(german.frontend).sort(),Object.keys(english.frontend).sort());
  await setLanguage("de-CH");
  assert.equal(t("common.add_task"),german.frontend["common.add_task"]);
  await setLanguage("en");
});

test("missing language catalogs retain the English fallback",async()=>{
  await setLanguage("fr");
  assert.equal(t("common.add_task"),catalog("en").frontend["common.add_task"]);
  await setLanguage("en");
});

test("frontend source contains no embedded German UI copy",()=>{
  const root=new URL("../../custom_components/home_tasker/frontend/",import.meta.url);
  const files=readdirSync(root,{recursive:true}).filter(name=>name.endsWith(".js"));
  const german=/[\u00e4\u00f6\u00fc\u00c4\u00d6\u00dc\u00df]/;
  for(const name of files)assert.doesNotMatch(readFileSync(new URL(name.replaceAll("\\","/"),root),"utf8"),german,name);
});
