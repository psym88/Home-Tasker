export const L = { addTask:"Task hinzufügen", fixed:"Nach Kalender", sliding:"Nach Erledigung", daily:"Täglich", weekly:"Wöchentlich", monthly:"Monatlich", yearly:"Jährlich", save:"Speichern", files:"Dateien", history:"Verlauf", noFiles:"Keine Dateien", noHistory:"Noch kein Verlauf" };
export const esc = (v) => String(v ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const markdownInline = (value) => {
  const protectedHtml=[],protect=html=>{protectedHtml.push(html);return `\u0000${protectedHtml.length-1}\u0000`;};
  let html=esc(value).replace(/`([^`\n]+)`/g,(_,text)=>protect(`<code>${text}</code>`));
  html=html.replace(/\[([^\]]+)]\(((?:https?:\/\/|mailto:|\/)[^\s)]+)\)/g,(_,label,url)=>protect(`<a href="${url}" target="_blank" rel="noopener noreferrer">${label}</a>`));
  html=html.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>").replace(/__([^_]+)__/g,"<strong>$1</strong>");
  html=html.replace(/(^|[^*])\*([^*\n]+)\*/g,"$1<em>$2</em>").replace(/(^|[^_])_([^_\n]+)_/g,"$1<em>$2</em>");
  return html.replace(/\u0000(\d+)\u0000/g,(_,index)=>protectedHtml[Number(index)]);
};
export const markdown = (value) => {
  const lines=String(value??"").replace(/\r\n?/g,"\n").split("\n"),parts=[];
  let list=null,paragraph=[],fence=null;
  const flushParagraph=()=>{if(paragraph.length){parts.push(`<p>${paragraph.map(markdownInline).join("<br>")}</p>`);paragraph=[];}};
  const closeList=()=>{if(list){parts.push(`</${list}>`);list=null;}};
  for(const line of lines){
    if(fence!==null){if(/^\s*```/.test(line)){parts.push(`<pre><code>${esc(fence.join("\n"))}</code></pre>`);fence=null;}else fence.push(line);continue;}
    if(/^\s*```/.test(line)){flushParagraph();closeList();fence=[];continue;}
    const heading=/^(#{1,6})\s+(.+)$/.exec(line),unordered=/^\s*[-*+]\s+(.+)$/.exec(line),ordered=/^\s*\d+[.)]\s+(.+)$/.exec(line),quote=/^\s*>\s?(.*)$/.exec(line);
    if(!line.trim()){flushParagraph();closeList();continue;}
    if(heading){flushParagraph();closeList();const level=heading[1].length;parts.push(`<h${level}>${markdownInline(heading[2])}</h${level}>`);continue;}
    if(unordered||ordered){flushParagraph();const kind=unordered?"ul":"ol";if(list!==kind){closeList();parts.push(`<${kind}>`);list=kind;}parts.push(`<li>${markdownInline((unordered||ordered)[1])}</li>`);continue;}
    if(quote){flushParagraph();closeList();parts.push(`<blockquote>${markdownInline(quote[1])}</blockquote>`);continue;}
    if(/^\s*(?:---+|___+|\*\*\*+)\s*$/.test(line)){flushParagraph();closeList();parts.push("<hr>");continue;}
    closeList();paragraph.push(line);
  }
  if(fence!==null)parts.push(`<pre><code>${esc(fence.join("\n"))}</code></pre>`);
  flushParagraph();closeList();return parts.join("");
};
