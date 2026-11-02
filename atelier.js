const el = id => document.getElementById(id);
let files = [], statement = null, worker;
const urls = [];
function fisierNou(bytes, type) {
  const url = URL.createObjectURL(new Blob([bytes],{type}));
  urls.push(url);
  return url;
}
function reset() {
  el("review").hidden = true;
  el("result").hidden = true;
  el("status").textContent = "";
  urls.splice(0).forEach(url => URL.revokeObjectURL(url));
  el("copy").textContent = "Copiază codul";
}
function busy(on) {
  el("fields").disabled = on;
  el("demo").disabled = on;
}
function selectFiles(list) {
  reset();
  files = list;
  el("selection").textContent = files.length ? files.map(f=>f.name).join(" · ") : "Niciun fișier selectat.";
}
function setStatement(file) {
  statement = file;
  el("sheet").textContent = file ? file.name : "";
}
el("choose").onclick = () => el("files").click();
el("folder").onclick = () => el("dir").click();
el("load").onclick = () => el("statement").click();
el("files").onchange = e => { selectFiles([...e.target.files]); e.target.value = ""; };
el("dir").onchange = e => {
  const list = [...e.target.files];
  const csv = list.filter(f=>/\.csv$/i.test(f.name) && !/(^|\/)data_out\//i.test(f.webkitRelativePath));
  const inputs = csv.filter(f=>/(^|\/)data_in\//i.test(f.webkitRelativePath));
  selectFiles(inputs.length ? inputs : csv);
  const pdf = list.filter(f=>/^tema.*\.pdf$/i.test(f.name));
  if (!el("text").value.trim()) setStatement(pdf.length === 1 ? pdf[0] : null);
  e.target.value = "";
};
el("statement").onchange = e => {
  const f = e.target.files[0];
  if (f) { reset(); setStatement(f); el("text").value = ""; }
  e.target.value = "";
};
for (const id of ["text","primary","category"]) el(id).oninput = () => {
  reset();
  if (id === "text") setStatement(null);
};
el("demo").onclick = async () => {
  busy(true); reset();
  try {
    const [data, text] = await Promise.all(["exemplu.zip","cerinte.txt"].map(f=>fetch(f)));
    if (!data.ok || !text.ok) throw Error("Exemplul nu a putut fi încărcat.");
    selectFiles([new File([await data.blob()], "exemplu.zip")]);
    setStatement(null);
    el("text").value = await text.text(); el("primary").value = ""; el("category").value = "";
    busy(false); el("form").requestSubmit();
  } catch(err) { el("status").textContent = err.message; busy(false); }
};
el("copy").onclick = async () => {
  try {
    await navigator.clipboard.writeText(el("code").textContent);
    el("copy").textContent = "Cod copiat";
  } catch {
    const range = document.createRange();
    range.selectNodeContents(el("code"));
    const selection = window.getSelection();
    selection.removeAllRanges(); selection.addRange(range);
    el("copy").textContent = "Cod selectat • copiază cu Ctrl+C";
  }
};
function rezultatCsv(out) {
  const box = document.createElement("details");
  box.open = true;
  const title = document.createElement("summary");
  title.textContent = out.nume + " · " + out.total + " rânduri";
  const scroll = document.createElement("div"); scroll.className = "csv";
  const table = document.createElement("table");
  for (const [i,row] of [out.antet, ...out.mostra].entries()) {
    const tr = table.insertRow();
    for (const value of row) {
      const cell = document.createElement(i === 0 ? "th" : "td");
      cell.textContent = value; tr.append(cell);
    }
  }
  scroll.append(table);
  const link = document.createElement("a");
  link.href = fisierNou(out.bytes, "text/csv;charset=utf-8");
  link.download = out.nume; link.textContent = "Descarcă " + out.nume;
  box.append(title, scroll, link); return box;
}
function motor() {
  if (worker) return worker;
  worker = new Worker("motor.js?v=3");
  worker.onerror = e => {
    el("status").textContent = e.message || "Motorul nu a pornit. Verifică accesul la internet și reîncearcă.";
    busy(false); worker.terminate(); worker = null;
  };
  worker.onmessage = ({data}) => {
    if (data.type === "status" || data.type === "error") el("status").textContent = data.text;
    if (data.type === "status") return;
    if (data.type === "done" || data.type === "error") busy(false);
    if (data.type === "plan") {
      el("text").value = data.text;
      el("code").textContent = data.cod;
      el("python").href = fisierNou(data.cod, "text/x-python;charset=utf-8");
      el("table").textContent = "Tabel principal · " + data.principal;
      el("plan").replaceChildren(...data.pasi.map(p=>{
        const li = document.createElement("li"), title = document.createElement("strong"), details = document.createElement("code");
        title.textContent = p.functie + " → " + p.fisier;
        details.textContent = Object.entries(p.parametri).map(([k,v])=>k+" = "+JSON.stringify(v)).join(" · ")
           + (p.sortare ? " · sortare = "+p.sortare : "");
        li.append(title, details); return li;
      }));
      el("review").hidden = false;
      el("review").scrollIntoView({block:"start"});
    } else if (data.type === "done") {
      el("download").href = fisierNou(data.bytes, "application/zip");
      el("outputs").replaceChildren(...data.outputs.map(rezultatCsv));
      el("result").hidden = false;
      el("status").textContent = "Calcul încheiat.";
    }
  };
  return worker;
}
el("form").onsubmit = e => {
  e.preventDefault(); reset();
  try {
    if (!files.length) throw Error("Alege fișierele CSV, un dosar sau o arhivă ZIP.");
    if (files.some(f=>/\.zip$/i.test(f.name)) && files.length > 1) throw Error("Alege o singură arhivă ZIP sau un grup de CSV-uri.");
    const all = statement ? [...files, statement] : files;
    if (new Set(all.map(f=>f.name.toLowerCase())).size !== all.length) throw Error("Există fișiere cu același nume. Selectează un singur set de date.");
    busy(true); el("status").textContent = "Se pornește motorul…";
    motor().postMessage({action:"solve",files:all,config:{text:el("text").value,principal:el("primary").value.trim(),categorie:el("category").value.trim()}});
  } catch(err) { busy(false); el("status").textContent = err.message; }
};
