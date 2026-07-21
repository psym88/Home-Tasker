// Shared constants and helpers for the Home Tasker panel modules.
export const VERSION = "0.2.48";
export const CSS_URL = new URL(`./panel.css?v=${VERSION}`, import.meta.url).href;
export const STYLE_LINK = `<link rel="stylesheet" href="${CSS_URL}">`;
export const L = { addTask:"Task hinzufügen", fixed:"Nach Kalender", sliding:"Nach Erledigung", daily:"Täglich", weekly:"Wöchentlich", monthly:"Monatlich", yearly:"Jährlich", save:"Speichern", files:"Dateien", history:"Verlauf", noFiles:"Keine Dateien", noHistory:"Noch kein Verlauf" };
export const esc = (v) => String(v ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
