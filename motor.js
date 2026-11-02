const CDN = "https://cdn.jsdelivr.net/pyodide/v0.28.3/full/";
let runtime;
function status(text) { postMessage({type:"status", text}); }
async function incarcare() {
  status("Se încarcă Python în browser. Prima pornire poate dura un minut.");
  importScripts(CDN + "pyodide.js");
  const py = await loadPyodide({indexURL:CDN});
  status("Se încarcă bibliotecile pentru calcule și clasificare…");
  await py.loadPackage(["scikit-learn", "pandas", "scipy"]);
  const res = await fetch("motor.zip?v=3");
  if (!res.ok) throw new Error("Motorul de calcul nu a putut fi descărcat.");
  py.unpackArchive(await res.arrayBuffer(),"zip",{extractDir:"/motor"});
  const bridge = await fetch("atelier.py?v=3");
  if (!bridge.ok) throw new Error("Adaptorul Python nu a putut fi încărcat.");
  await py.runPythonAsync("import sys\nsys.path.insert(0, '/motor')\nsys.dont_write_bytecode = True\n" + await bridge.text());
  return py;
}
self.onmessage = async ({data}) => {
  try {
    runtime ??= incarcare().catch(err => { runtime = null; throw err; });
    const py = await runtime;
    if (data.action === "solve") {
      status("Se citesc datele și se interpretează cerințele…");
      py.runPython("incepe()");
      for (const file of data.files) {
        if (/[\\/:]/.test(file.name) || file.name === "." || file.name === "..") throw new Error("Nume de fișier invalid.");
        py.FS.writeFile("/lucru/intrari/"+file.name, new Uint8Array(await file.arrayBuffer()));
      }
      py.globals.set("config_web", JSON.stringify(data.config));
      postMessage({type:"plan", ...JSON.parse(await py.runPythonAsync("interpreteaza_web(config_web)"))});
      status("Se calculează tabelele și se creează arhiva ZIP…");
      const outputs = JSON.parse(await py.runPythonAsync("calculeaza_web()"));
      for (const out of outputs) out.bytes = py.FS.readFile("/lucru/proiect/data_out/"+out.nume);
      const bytes = py.FS.readFile("/lucru/rezolvare.zip");
      postMessage({type:"done",outputs, bytes},[bytes.buffer, ...outputs.map(out => out.bytes.buffer)]);
    }
  } catch (err) {
    const message = String(err.message || err).trim().split("\n");
    postMessage({type:"error",text:message.filter(s=>!/^\s*(File |Traceback|\^|at )/.test(s)).slice(-3).join("\n")});
  }
};
