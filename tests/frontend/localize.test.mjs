import assert from "node:assert/strict";
import {readFileSync,readdirSync} from "node:fs";
import test from "node:test";

const {setLanguage,t,translationKeys}=await import("../../custom_components/home_tasker/frontend/localize.js");

test("English is the complete built-in fallback",async()=>{
  await setLanguage("en-US");
  assert.equal(t("common.add_task"),"Add task");
  assert.equal(t("task.complete_confirm",{name:"Laundry"}),"Do you want to mark “Laundry” as completed?");
  assert.ok(translationKeys.length>50);
});

test("German translations cover every frontend key",()=>{
  const messages=JSON.parse(readFileSync(new URL("../../custom_components/home_tasker/frontend/translations/de.json",import.meta.url),"utf8"));
  assert.deepEqual(Object.keys(messages).sort(),[...translationKeys].sort());
});

test("frontend source contains no embedded German UI copy",()=>{
  const root=new URL("../../custom_components/home_tasker/frontend/",import.meta.url);
  const files=readdirSync(root,{recursive:true}).filter(name=>name.endsWith(".js"));
  const german=/[\u00e4\u00f6\u00fc\u00c4\u00d6\u00dc\u00df]/;
  for(const name of files)assert.doesNotMatch(readFileSync(new URL(name.replaceAll("\\","/"),root),"utf8"),german,name);
});
