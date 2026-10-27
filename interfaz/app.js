/* Interfaz del Planificador de Horarios.
 * Datos: window.DATOS (generado por `python -m src.construir_interfaz`). */
(function () {
  "use strict";

  const D = window.DATOS;

  // ------------------------------------------------------------------ catálogo
  const TEC = {
    fuerza_bruta: {
      nombre: "Fuerza bruta", var: "--fb",
      desc: "Prueba todas las combinaciones (bloque, salón) y se queda con la mejor.",
      tiempo: "O((B·A)^S · S²)", espacio: "O(S)",
      optimo: ["si", "Sí, calidad completa"], limite: "S ≤ 4",
      trabajo: "combinaciones_probadas", trabajoNombre: "Combinaciones probadas",
      ops: (S) => Math.pow(60, S) * S * S,
    },
    greedy: {
      nombre: "Voraz (greedy)", var: "--gr",
      desc: "Ubica primero la sesión más restringida en la mejor opción local, sin retroceder.",
      tiempo: "O(S³ · B · A)", espacio: "O(S + B·A)",
      optimo: ["no", "No garantizado"], limite: "S en cientos",
      trabajo: "candidatos_evaluados", trabajoNombre: "Candidatos evaluados",
      ops: (S) => Math.pow(S, 3) * 60 + S * 60,
    },
    backtracking: {
      nombre: "Backtracking", var: "--bt",
      desc: "Recorre el árbol de decisiones con poda: restricciones, forward checking y MRV.",
      tiempo: "O((B·A)^S · S) peor caso", espacio: "O(S)",
      optimo: ["si", "Sí, calidad completa"], limite: "S ≤ 4 (óptimo)",
      trabajo: "nodos_explorados", trabajoNombre: "Nodos explorados",
      ops: (S) => Math.pow(60, S) * S,
    },
    dinamica: {
      nombre: "Programación dinámica", var: "--dp",
      desc: "Resuelve bloque a bloque recordando qué sesiones ya ubicó (máscara de bits).",
      tiempo: "O(B · 3^S)", espacio: "O(B · 2^S)",
      optimo: ["parcial", "Sí, en preferencia"], limite: "S ≈ 14",
      trabajo: "estados_explorados", trabajoNombre: "Estados (bloque, máscara)",
      ops: (S) => 30 * Math.pow(3, S),
    },
  };
  const ORDEN_TEC = ["fuerza_bruta", "greedy", "backtracking", "dinamica"];

  const DIAS = [
    { id: "lunes", corto: "Lun", nombre: "Lunes" },
    { id: "martes", corto: "Mar", nombre: "Martes" },
    { id: "miercoles", corto: "Mié", nombre: "Miércoles" },
    { id: "jueves", corto: "Jue", nombre: "Jueves" },
    { id: "viernes", corto: "Vie", nombre: "Viernes" },
  ];
  const FRANJAS = ["06:00-08:00", "08:00-10:00", "10:00-12:00", "12:00-14:00", "14:00-16:00", "16:00-18:00"];
  const PREF = {
    0: { t: "Evitar", v: 0 },
    1: { t: "Indiferente", v: 0.5 },
    2: { t: "Preferida", v: 1 },
  };
  const NOMBRES_CASO = {
    caso_pequeno: ["Original", "Pequeño"],
    caso_mediano: ["Original", "Mediano"],
    caso_grande: ["Original", "Grande"],
    caso_multi_pequeno: ["Multisesión", "Pequeño"],
    caso_multi_mediano: ["Multisesión", "Mediano"],
    caso_multi_grande: ["Multisesión", "Grande"],
  };
  const TONOS = [212, 152, 28, 280, 345, 190, 48, 105, 250, 0, 320, 170];

  // ------------------------------------------------------------------ utilidades
  const $ = (sel, raiz = document) => raiz.querySelector(sel);
  const $$ = (sel, raiz = document) => [...raiz.querySelectorAll(sel)];
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const cssVar = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  const colorTec = (t) => cssVar(TEC[t].var);

  const guardar = (k, v) => { try { localStorage.setItem("planificador." + k, JSON.stringify(v)); } catch (_) {} };
  const leer = (k, def) => { try { const v = localStorage.getItem("planificador." + k); return v == null ? def : JSON.parse(v); } catch (_) { return def; } };

  function fmtTiempo(s) {
    if (s == null || !isFinite(s)) return "—";
    if (s < 1e-3) return (s * 1e6).toFixed(0) + " µs";
    if (s < 1) return (s * 1e3).toFixed(s < 0.01 ? 2 : 1) + " ms";
    if (s < 60) return s.toFixed(s < 10 ? 2 : 1) + " s";
    if (s < 3600) return (s / 60).toFixed(1) + " min";
    if (s < 86400) return (s / 3600).toFixed(1) + " h";
    const dias = s / 86400;
    if (dias < 365) return dias.toFixed(0) + " días";
    const anios = dias / 365.25;
    if (anios < 1e4) return anios.toFixed(0) + " años";
    return fmtGrande(anios) + " años";
  }
  function fmtGrande(n) {
    if (n == null || !isFinite(n)) return "—";
    if (Math.abs(n) < 1e6) return Math.round(n).toLocaleString("es-CO");
    const e = Math.floor(Math.log10(n));
    return (n / Math.pow(10, e)).toFixed(1) + "×10" + superindice(e);
  }
  function superindice(n) {
    const m = { "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹", "-": "⁻" };
    return String(n).split("").map((c) => m[c] || c).join("");
  }
  const nombreDia = (id) => (DIAS.find((d) => d.id === id) || { nombre: id }).nombre;
  const iniciales = (g) => g.replace(/[^0-9A-Za-z]/g, "").slice(-3);

  // ------------------------------------------------------------------ estado
  const estado = {
    tab: leer("tab", "horarios"),
    caso: leer("caso", null),
    tecnica: leer("tecnica", "dinamica"),
    vista: leer("vista", "semana"),
    ref: "fuerza_bruta",
    ocultar: false,
    orden: { col: "dia", dir: 1 },
    filtros: nuevosFiltros(),
  };
  function nuevosFiltros() {
    return { dias: new Set(), materia: "", profesor: "", grupo: "", salon: "", texto: "" };
  }

  if (!D || !D.casos || !D.casos.length) {
    document.querySelector("main").innerHTML =
      '<div class="panel"><h2>Faltan los datos</h2><p style="margin-top:8px">Genera <code>interfaz/datos.js</code> desde la raíz del proyecto con:</p>' +
      "<pre class='mono' style='margin-top:10px'>python3 -m src.exportar_salidas\npython3 -m analisis.benchmark_tecnicas\npython3 -m src.construir_interfaz</pre></div>";
    return;
  }
  if (!D.casos.some((c) => c.id === estado.caso)) estado.caso = D.casos[D.casos.length - 1].id;

  const casoActual = () => D.casos.find((c) => c.id === estado.caso);
  const salidaActual = () => casoActual().salidas[estado.tecnica];

  function tonoMateria(caso) {
    const m = {};
    caso.materias.forEach((x, i) => { m[x.nombre] = TONOS[i % TONOS.length]; });
    return m;
  }

  // ------------------------------------------------------------------ pestañas y tema
  function aplicarTab() {
    $$(".pestana").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.tab === estado.tab)));
    $("#tab-horarios").hidden = estado.tab !== "horarios";
    $("#tab-analisis").hidden = estado.tab !== "analisis";
    if (estado.tab === "analisis") renderAnalisis();
  }
  $$(".pestana").forEach((b) => b.addEventListener("click", () => {
    estado.tab = b.dataset.tab; guardar("tab", estado.tab); aplicarTab();
  }));

  const temaGuardado = leer("tema", null);
  if (temaGuardado) document.documentElement.dataset.theme = temaGuardado;
  // Si el sistema cambia de tema, las gráficas se redibujan con los colores nuevos.
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
    analisisListo = false;
    if (estado.tab === "analisis") renderAnalisis();
  });
  $("#tema").addEventListener("click", () => {
    const oscuro = document.documentElement.dataset.theme
      ? document.documentElement.dataset.theme === "dark"
      : matchMedia("(prefers-color-scheme: dark)").matches;
    const nuevo = oscuro ? "light" : "dark";
    document.documentElement.dataset.theme = nuevo;
    guardar("tema", nuevo);
    analisisListo = false;
    if (estado.tab === "analisis") renderAnalisis();
  });

  // ================================================================== HORARIOS
  function renderCasos() {
    $("#casos").innerHTML = D.casos.map((c) => {
      const [etq, nom] = NOMBRES_CASO[c.id] || ["Caso", c.id];
      return `<button class="tarjeta-caso ${c.id === estado.caso ? "activo" : ""}" data-caso="${c.id}">
        <div class="tc-etiqueta">${etq}</div>
        <div class="tc-nombre">${nom}<span class="insignia">S = ${c.sesiones}</span></div>
        <div class="tc-detalle">${c.materias.length} materias · ${c.grupos.length} grupos · ${c.salones.length} salones</div>
      </button>`;
    }).join("");
    $$("#casos .tarjeta-caso").forEach((b) => b.addEventListener("click", () => {
      estado.caso = b.dataset.caso; guardar("caso", estado.caso);
      estado.filtros = nuevosFiltros();
      if (!casoActual().salidas[estado.tecnica]) estado.tecnica = ORDEN_TEC.find((t) => casoActual().salidas[t]);
      if (!casoActual().salidas[estado.ref] || estado.ref === undefined) estado.ref = ORDEN_TEC.find((t) => casoActual().salidas[t]);
      renderHorarios();
    }));
  }

  function renderTecnicas() {
    const caso = casoActual();
    $("#tecnicas").innerHTML = ORDEN_TEC.map((t) => {
      const s = caso.salidas[t];
      const info = TEC[t];
      if (!s) {
        return `<button class="tarjeta-tecnica" style="--c:var(${info.var})" disabled>
          <div class="tt-cabeza"><span class="tt-punto"></span><span class="tt-nombre">${info.nombre}</span></div>
          <div class="tt-desc">${info.desc}</div>
          <div class="tt-omitida">⏳ No se ejecutó: con S = ${caso.sesiones} tardaría horas (límite práctico ${info.limite}).</div>
        </button>`;
      }
      return `<button class="tarjeta-tecnica ${t === estado.tecnica ? "activo" : ""}" style="--c:var(${info.var})" data-tec="${t}">
        <div class="tt-cabeza"><span class="tt-punto"></span><span class="tt-nombre">${info.nombre}</span></div>
        <div class="tt-desc">${info.desc}</div>
        <div class="tt-metricas">
          <div><span>Calidad</span><b>${s.metricas.calidad.toFixed(3)}</b></div>
          <div><span>Preferencia</span><b>${preferencia(s).toFixed(1)}</b></div>
          <div><span>Tiempo</span><b>${fmtTiempo(s.tiempo_s)}</b></div>
        </div>
      </button>`;
    }).join("");
    $$("#tecnicas .tarjeta-tecnica[data-tec]").forEach((b) => b.addEventListener("click", () => {
      estado.tecnica = b.dataset.tec; guardar("tecnica", estado.tecnica); renderHorarios();
    }));
  }

  const preferencia = (s) => s.asignaciones.reduce((a, x) => a + PREF[x.preferencia_profesor].v, 0);

  function renderKPIs() {
    const caso = casoActual();
    const s = salidaActual();
    const info = TEC[estado.tecnica];
    const n = s.asignaciones.length;
    const salones = new Set(s.asignaciones.map((a) => a.salon)).size;
    const pref = preferencia(s);
    const trabajo = s.metricas[info.trabajo];
    $("#kpis").innerHTML = `
      <div class="kpi" style="--c:var(${info.var})">
        <div class="kpi-etiqueta">Calidad del horario</div>
        <div class="kpi-valor">${s.metricas.calidad.toFixed(3)} <small>/ 1</small></div>
        <div class="barra-prog"><i style="width:${s.metricas.calidad * 100}%"></i></div>
      </div>
      <div class="kpi" style="--c:var(--pref-2)">
        <div class="kpi-etiqueta">Preferencia profesores</div>
        <div class="kpi-valor">${pref.toFixed(1)} <small>/ ${n}</small></div>
        <div class="barra-prog"><i style="width:${n ? (pref / n) * 100 : 0}%"></i></div>
      </div>
      <div class="kpi">
        <div class="kpi-etiqueta">Tiempo de ejecución</div>
        <div class="kpi-valor">${fmtTiempo(s.tiempo_s)}</div>
        <div class="kpi-nota">${info.nombre}</div>
      </div>
      <div class="kpi">
        <div class="kpi-etiqueta">Clases programadas</div>
        <div class="kpi-valor">${n} <small>/ ${caso.sesiones}</small></div>
        <div class="kpi-nota">${n === caso.sesiones ? "✅ Todas las sesiones (R6)" : "⚠️ Faltan sesiones"}</div>
      </div>
      <div class="kpi">
        <div class="kpi-etiqueta">Salones usados</div>
        <div class="kpi-valor">${salones} <small>/ ${caso.salones.length}</small></div>
        <div class="kpi-nota">Menos salones es mejor</div>
      </div>
      <div class="kpi">
        <div class="kpi-etiqueta">${info.trabajoNombre}</div>
        <div class="kpi-valor">${trabajo != null ? fmtGrande(trabajo) : "—"}</div>
        <div class="kpi-nota">Trabajo del algoritmo</div>
      </div>`;
  }

  function opciones(lista, actual, todos) {
    return `<option value="">${todos}</option>` +
      lista.map((x) => `<option value="${esc(x)}" ${x === actual ? "selected" : ""}>${esc(x)}</option>`).join("");
  }

  function renderFiltros() {
    const caso = casoActual();
    const f = estado.filtros;
    const comparar = estado.vista === "comparar";
    $("#filtros").innerHTML = `
      <div class="campo campo-dias">
        <label>Días</label>
        <div class="chips">
          ${DIAS.map((d) => `<button class="chip ${f.dias.has(d.id) ? "activo" : ""}" data-dia="${d.id}">${d.nombre}</button>`).join("")}
        </div>
      </div>
      <div class="campo ${f.materia ? "activo" : ""}"><label>Materia</label>
        <select data-f="materia">${opciones(caso.materias.map((m) => m.nombre), f.materia, "Todas")}</select></div>
      <div class="campo ${f.profesor ? "activo" : ""}"><label>Profesor</label>
        <select data-f="profesor">${opciones(caso.profesores, f.profesor, "Todos")}</select></div>
      <div class="campo ${f.grupo ? "activo" : ""}"><label>Grupo</label>
        <select data-f="grupo">${opciones(caso.grupos.map((g) => g.nombre), f.grupo, "Todos")}</select></div>
      <div class="campo ${f.salon ? "activo" : ""}"><label>Salón</label>
        <select data-f="salon">${opciones(caso.salones.map((s) => s.id), f.salon, "Todos")}</select></div>
      <div class="campo"><label>Buscar</label>
        <input type="search" data-f="texto" placeholder="Materia, profesor, grupo…" value="${esc(f.texto)}"></div>
      <div class="acciones-filtro">
        <span class="contador" id="contador"></span>
        <span style="display:flex;gap:14px;align-items:center;flex-wrap:wrap">
          ${!comparar ? `<label class="interruptor"><input type="checkbox" id="ocultar" ${estado.ocultar ? "checked" : ""}> Ocultar las que no coinciden</label>` : ""}
          <button class="boton" id="limpiar">↺ Limpiar filtros</button>
        </span>
      </div>`;
    $$("#filtros .chip").forEach((b) => b.addEventListener("click", () => {
      const d = b.dataset.dia;
      f.dias.has(d) ? f.dias.delete(d) : f.dias.add(d);
      renderFiltros(); renderVista();
    }));
    $$("#filtros select").forEach((s) => s.addEventListener("change", () => {
      f[s.dataset.f] = s.value; renderFiltros(); renderLeyenda(); renderVista();
    }));
    const busc = $("#filtros input[type=search]");
    busc.addEventListener("input", () => { f.texto = busc.value; renderVista(); });
    const oc = $("#ocultar");
    if (oc) oc.addEventListener("change", () => { estado.ocultar = oc.checked; renderVista(); });
    $("#limpiar").addEventListener("click", () => { estado.filtros = nuevosFiltros(); renderFiltros(); renderLeyenda(); renderVista(); });
  }

  function hayFiltros() {
    const f = estado.filtros;
    return f.dias.size || f.materia || f.profesor || f.grupo || f.salon || f.texto;
  }
  function coincide(a) {
    const f = estado.filtros;
    if (f.dias.size && !f.dias.has(a.dia)) return false;
    if (f.materia && a.materia !== f.materia) return false;
    if (f.profesor && a.profesor !== f.profesor) return false;
    if (f.grupo && a.grupo !== f.grupo) return false;
    if (f.salon && a.salon !== f.salon) return false;
    if (f.texto) {
      const q = f.texto.toLowerCase();
      if (![a.materia, a.profesor, a.grupo, a.salon].some((x) => x.toLowerCase().includes(q))) return false;
    }
    return true;
  }

  function renderLeyenda() {
    const caso = casoActual();
    const tonos = tonoMateria(caso);
    $("#leyenda").innerHTML =
      caso.materias.map((m) => `<span class="li ${estado.filtros.materia === m.nombre ? "activo" : ""}" data-materia="${esc(m.nombre)}" title="Filtrar por esta materia">
        <span class="cuadro" style="--h:${tonos[m.nombre]}"></span>${esc(m.nombre)}</span>`).join("") +
      `<span class="sep"></span>
       <span class="li" style="cursor:default"><span class="pref-punto pref-2"></span>Preferida</span>
       <span class="li" style="cursor:default"><span class="pref-punto pref-1"></span>Indiferente</span>
       <span class="li" style="cursor:default"><span class="pref-punto pref-0"></span>Evitar</span>`;
    $$("#leyenda .li[data-materia]").forEach((el) => el.addEventListener("click", () => {
      const m = el.dataset.materia;
      estado.filtros.materia = estado.filtros.materia === m ? "" : m;
      renderFiltros(); renderLeyenda(); renderVista();
    }));
  }

  function actualizarContador(visibles, total) {
    const c = $("#contador");
    if (c) c.innerHTML = hayFiltros()
      ? `Mostrando <b>${visibles}</b> de <b>${total}</b> clases`
      : `<b>${total}</b> clases programadas · pasa el cursor sobre una clase para ver su grupo, haz clic para ver el detalle`;
  }

  function renderVista() {
    $$("#vistas button").forEach((b) => b.classList.toggle("activo", b.dataset.vista === estado.vista));
    if (estado.vista === "tabla") renderTabla();
    else if (estado.vista === "comparar") renderComparar();
    else renderSemana();
  }
  $$("#vistas button").forEach((b) => b.addEventListener("click", () => {
    estado.vista = b.dataset.vista; guardar("vista", estado.vista); renderFiltros(); renderVista();
  }));

  // ---------------------------------------------------------------- vista semana
  function tarjetaClase(a, tonos, idx) {
    const ok = coincide(a);
    const cls = ok ? "" : (estado.ocultar ? "oculta" : (hayFiltros() ? "tenue" : ""));
    return `<button class="clase ${cls}" style="--h:${tonos[a.materia]}" data-i="${idx}" data-grupo="${esc(a.grupo)}">
      <div class="cl-materia">${esc(a.materia)}</div>
      <div class="cl-meta"><span>${esc(a.profesor)} · ${esc(a.grupo)}</span>
        <span style="display:inline-flex;gap:5px;align-items:center"><span class="pref-punto pref-${a.preferencia_profesor}" title="Preferencia: ${PREF[a.preferencia_profesor].t}"></span><span class="cl-salon">${esc(a.salon)}</span></span></div>
    </button>`;
  }

  function renderSemana() {
    const caso = casoActual();
    const s = salidaActual();
    const tonos = tonoMateria(caso);
    const dias = estado.filtros.dias.size ? DIAS.filter((d) => estado.filtros.dias.has(d.id)) : DIAS;
    const asigs = s.asignaciones;
    let html = `<div class="semana-envoltura"><div class="semana" style="grid-template-columns: 92px repeat(${dias.length}, minmax(140px, 1fr))">`;
    html += `<div class="cab"></div>` + dias.map((d) => `<div class="cab">${d.nombre}</div>`).join("");
    FRANJAS.forEach((fr) => {
      const [hi, hf] = fr.split("-");
      html += `<div class="hora"><span>${hi}</span><span style="opacity:.6">${hf}</span></div>`;
      dias.forEach((d) => {
        const aqui = asigs.map((a, i) => [a, i]).filter(([a]) => a.dia === d.id && a.franja === fr);
        const visibles = aqui.filter(([a]) => !(estado.ocultar && !coincide(a)));
        html += `<div class="celda ${visibles.length ? "" : "vacia"}">${aqui.map(([a, i]) => tarjetaClase(a, tonos, i)).join("")}</div>`;
      });
    });
    html += `</div></div>`;
    $("#vista").innerHTML = html;
    actualizarContador(asigs.filter(coincide).length, asigs.length);

    $$("#vista .clase").forEach((el) => {
      el.addEventListener("mouseenter", () => {
        const g = el.dataset.grupo;
        $$("#vista .clase").forEach((o) => o.classList.toggle("resaltado", o.dataset.grupo === g));
      });
      el.addEventListener("mouseleave", () => $$("#vista .clase").forEach((o) => o.classList.remove("resaltado")));
      el.addEventListener("click", () => abrirDetalle(asigs[+el.dataset.i]));
    });
  }

  // ---------------------------------------------------------------- vista tabla
  const COLS = [
    { id: "dia", t: "Día", v: (a) => DIAS.findIndex((d) => d.id === a.dia) * 10 + FRANJAS.indexOf(a.franja) },
    { id: "franja", t: "Franja", v: (a) => FRANJAS.indexOf(a.franja) },
    { id: "materia", t: "Materia", v: (a) => a.materia },
    { id: "profesor", t: "Profesor", v: (a) => a.profesor },
    { id: "grupo", t: "Grupo", v: (a) => a.grupo },
    { id: "salon", t: "Salón", v: (a) => a.salon },
    { id: "pref", t: "Preferencia", v: (a) => a.preferencia_profesor },
  ];

  function renderTabla() {
    const caso = casoActual();
    const s = salidaActual();
    const tonos = tonoMateria(caso);
    const col = COLS.find((c) => c.id === estado.orden.col);
    const filas = s.asignaciones.filter(coincide).slice().sort((x, y) => {
      const a = col.v(x), b = col.v(y);
      return (a < b ? -1 : a > b ? 1 : 0) * estado.orden.dir;
    });
    const gruposInfo = Object.fromEntries(caso.grupos.map((g) => [g.nombre, g]));
    $("#vista").innerHTML = `
      <div style="display:flex;justify-content:flex-end;margin-bottom:10px">
        <button class="boton" id="csv">⬇ Descargar CSV</button>
      </div>
      <div class="tabla-envoltura"><table class="tabla">
        <thead><tr>${COLS.map((c) => `<th class="ordenable ${c.id === estado.orden.col ? "orden" : ""}" data-col="${c.id}">${c.t}<span class="flecha">${c.id === estado.orden.col ? (estado.orden.dir > 0 ? "▲" : "▼") : "↕"}</span></th>`).join("")}</tr></thead>
        <tbody>${filas.length ? filas.map((a) => `<tr>
          <td><b>${nombreDia(a.dia)}</b></td>
          <td class="mono">${a.franja}</td>
          <td><span class="etq-materia"><span class="cuadro" style="--h:${tonos[a.materia]}"></span>${esc(a.materia)}</span></td>
          <td>${esc(a.profesor)}</td>
          <td>${esc(a.grupo)} <span style="color:var(--texto-3);font-size:12px">(${gruposInfo[a.grupo]?.estudiantes ?? "?"} est.)</span></td>
          <td class="mono">${esc(a.salon)}</td>
          <td><span class="pref-etq"><span class="pref-punto pref-${a.preferencia_profesor}"></span>${PREF[a.preferencia_profesor].t}</span></td>
        </tr>`).join("") : `<tr><td colspan="7" class="vacio">Ninguna clase coincide con los filtros.</td></tr>`}</tbody>
      </table></div>`;
    actualizarContador(filas.length, s.asignaciones.length);
    $$("#vista th.ordenable").forEach((th) => th.addEventListener("click", () => {
      if (estado.orden.col === th.dataset.col) estado.orden.dir *= -1;
      else estado.orden = { col: th.dataset.col, dir: 1 };
      renderTabla();
    }));
    $("#csv").addEventListener("click", () => {
      const lineas = [["dia", "franja", "materia", "profesor", "grupo", "salon", "preferencia"].join(",")]
        .concat(filas.map((a) => [a.dia, a.franja, a.materia, a.profesor, a.grupo, a.salon, PREF[a.preferencia_profesor].t]
          .map((x) => `"${String(x).replace(/"/g, '""')}"`).join(",")));
      const blob = new Blob(["﻿" + lineas.join("\n")], { type: "text/csv;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url; link.download = `${estado.caso}_${estado.tecnica}.csv`;
      document.body.appendChild(link); link.click(); link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    });
  }

  // ---------------------------------------------------------------- vista comparar
  function claveTiempo(a) { return `${a.materia}|${a.grupo}|${a.dia}|${a.franja}`; }
  function coincidencias(ref, otra) {
    const cuenta = {};
    ref.forEach((a) => { const k = claveTiempo(a); cuenta[k] = (cuenta[k] || 0) + 1; });
    let n = 0;
    otra.forEach((a) => { const k = claveTiempo(a); if (cuenta[k] > 0) { cuenta[k]--; n++; } });
    return n;
  }

  function renderComparar() {
    const caso = casoActual();
    const tonos = tonoMateria(caso);
    const disp = ORDEN_TEC.filter((t) => caso.salidas[t]);
    if (!caso.salidas[estado.ref]) estado.ref = disp[0];
    const ref = caso.salidas[estado.ref].asignaciones;
    const claveRef = new Set(ref.map(claveTiempo));

    const maxT = Math.max(...disp.map((t) => caso.salidas[t].tiempo_s));
    const fila = (t, valor, max, texto, log) => {
      const pct = log ? (Math.log10(valor * 1e6 + 1) / Math.log10(max * 1e6 + 1)) * 100 : (valor / max) * 100;
      return `<div class="bc-fila"><span>${TEC[t].nombre}</span><span class="pista"><i style="width:${Math.max(pct, 2)}%;background:${colorTec(t)}"></i></span><span class="val">${texto}</span></div>`;
    };
    let html = `
      <div class="comparar-barra">
        <span>Técnica de referencia:</span>
        <select id="ref">${disp.map((t) => `<option value="${t}" ${t === estado.ref ? "selected" : ""}>${TEC[t].nombre}</option>`).join("")}</select>
        <span>· Las clases con borde punteado están en un día/franja distinto al de la referencia.</span>
      </div>
      <div class="barras-comparar">
        <div class="bc"><h4>Calidad (más es mejor)</h4>${disp.map((t) => fila(t, caso.salidas[t].metricas.calidad, 1, caso.salidas[t].metricas.calidad.toFixed(3))).join("")}</div>
        <div class="bc"><h4>Preferencia (más es mejor)</h4>${disp.map((t) => fila(t, preferencia(caso.salidas[t]), caso.sesiones, preferencia(caso.salidas[t]).toFixed(1))).join("")}</div>
        <div class="bc"><h4>Tiempo (escala log, menos es mejor)</h4>${disp.map((t) => fila(t, caso.salidas[t].tiempo_s, maxT, fmtTiempo(caso.salidas[t].tiempo_s), true)).join("")}</div>
      </div>
      <div class="mini-grid">`;
    ORDEN_TEC.forEach((t) => {
      const s = caso.salidas[t];
      if (!s) {
        html += `<div class="mini" style="--c:var(${TEC[t].var})"><div class="mini-cab"><span class="tt-nombre"><span class="tt-punto"></span>${TEC[t].nombre}</span></div>
          <div class="nota-omitida">No se ejecutó para S = ${caso.sesiones}: tardaría horas.</div></div>`;
        return;
      }
      const coinc = coincidencias(ref, s.asignaciones);
      html += `<div class="mini ${t === estado.ref ? "ref" : ""}" style="--c:var(${TEC[t].var})">
        <div class="mini-cab"><span class="tt-nombre"><span class="tt-punto"></span>${TEC[t].nombre}</span>
          <span class="coincide">${t === estado.ref ? "Referencia" : `${coinc}/${s.asignaciones.length} iguales`}</span></div>
        <div class="mini-stats"><span>Calidad <b>${s.metricas.calidad.toFixed(3)}</b></span><span>Pref. <b>${preferencia(s).toFixed(1)}</b></span><span>Tiempo <b>${fmtTiempo(s.tiempo_s)}</b></span></div>
        <div class="mini-tabla"><div></div>${DIAS.map((d) => `<div class="mh">${d.corto}</div>`).join("")}
        ${FRANJAS.map((fr) => `<div class="mf">${fr.slice(0, 5)}</div>` + DIAS.map((d) => {
          const aqui = s.asignaciones.filter((a) => a.dia === d.id && a.franja === fr);
          return `<div class="mc">${aqui.map((a) => {
            const ok = coincide(a);
            const distinta = t !== estado.ref && !claveRef.has(claveTiempo(a));
            return `<span class="mb ${distinta ? "distinta" : ""}" style="--h:${tonos[a.materia]};${ok || !hayFiltros() ? "" : "opacity:.15"}" title="${esc(a.materia)} · ${esc(a.grupo)} · ${esc(a.salon)}">${esc(iniciales(a.grupo))}</span>`;
          }).join("")}</div>`;
        }).join("")).join("")}
        </div></div>`;
    });
    html += `</div>`;
    $("#vista").innerHTML = html;
    actualizarContador(salidaActual().asignaciones.filter(coincide).length, salidaActual().asignaciones.length);
    $("#ref").addEventListener("change", (e) => { estado.ref = e.target.value; renderComparar(); });
  }

  // ---------------------------------------------------------------- detalle
  function abrirDetalle(a) {
    const caso = casoActual();
    const tonos = tonoMateria(caso);
    const g = caso.grupos.find((x) => x.nombre === a.grupo);
    const sal = caso.salones.find((x) => x.id === a.salon);
    $("#modal-contenido").innerHTML = `
      <div class="det-cabecera" style="--h:${tonos[a.materia]}">
        <div style="font-size:12px;font-weight:600;opacity:.8">${nombreDia(a.dia)} · ${a.franja}</div>
        <h3>${esc(a.materia)}</h3>
      </div>
      <dl class="det-lista">
        <dt>Profesor</dt><dd>${esc(a.profesor)}</dd>
        <dt>Grupo</dt><dd>${esc(a.grupo)}${g ? ` · ${g.estudiantes} estudiantes` : ""}</dd>
        <dt>Salón</dt><dd class="mono">${esc(a.salon)}${sal ? ` · capacidad ${sal.capacidad}` : ""}</dd>
        <dt>Ocupación</dt><dd>${g && sal ? Math.round((g.estudiantes / sal.capacidad) * 100) + " %" : "—"}</dd>
        <dt>Preferencia</dt><dd><span class="pref-etq"><span class="pref-punto pref-${a.preferencia_profesor}"></span>${PREF[a.preferencia_profesor].t} para el profesor</span></dd>
        <dt>Técnica</dt><dd>${TEC[estado.tecnica].nombre}</dd>
      </dl>
      <div class="det-acciones">
        <button class="boton" data-filtrar="profesor" data-valor="${esc(a.profesor)}">Ver solo ${esc(a.profesor)}</button>
        <button class="boton" data-filtrar="grupo" data-valor="${esc(a.grupo)}">Ver solo ${esc(a.grupo)}</button>
        <button class="boton" data-filtrar="salon" data-valor="${esc(a.salon)}">Ver salón ${esc(a.salon)}</button>
      </div>`;
    $("#modal").hidden = false;
    $$("#modal [data-filtrar]").forEach((b) => b.addEventListener("click", () => {
      estado.filtros = nuevosFiltros();
      estado.filtros[b.dataset.filtrar] = b.dataset.valor;
      cerrarModal(); renderFiltros(); renderLeyenda(); renderVista();
    }));
  }
  function cerrarModal() { $("#modal").hidden = true; }
  $("#modal").addEventListener("click", (e) => { if (e.target.id === "modal") cerrarModal(); });
  $(".modal-cerrar").addEventListener("click", cerrarModal);
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") cerrarModal(); });

  function renderHorarios() {
    renderCasos(); renderTecnicas(); renderKPIs(); renderFiltros(); renderLeyenda(); renderVista();
  }

  // ================================================================== ANÁLISIS
  let analisisListo = false;
  const graficas = {};

  function bench() { return (D.benchmark && D.benchmark.resultados) || []; }
  function serieBench(t, campo) {
    return bench().filter((r) => r.tecnica === t).map((r) => ({ x: r.S, y: r[campo] }));
  }

  function renderResumen() {
    $("#resumen-tecnicas").innerHTML = ORDEN_TEC.map((t) => {
      const i = TEC[t];
      const filas = bench().filter((r) => r.tecnica === t);
      const ultima = filas[filas.length - 1];
      return `<div class="resumen" style="--c:var(${i.var})">
        <div class="r-cab"><span class="tt-punto" style="--c:var(${i.var})"></span><span class="r-nombre">${i.nombre}</span></div>
        <p style="font-size:13px;color:var(--texto-2)">${i.desc}</p>
        <div class="r-big">${i.tiempo}</div>
        <dl>
          <dt>Espacio</dt><dd class="mono">${i.espacio}</dd>
          <dt>¿Óptimo?</dt><dd class="${i.optimo[0]}">${i.optimo[1]}</dd>
          <dt>Límite práctico</dt><dd>${i.limite}</dd>
          ${ultima ? `<dt>Mayor S medido</dt><dd>S = ${ultima.S} en ${fmtTiempo(ultima.tiempo_s)}</dd>` : ""}
        </dl>
      </div>`;
    }).join("");
  }

  function baseOpciones(ejeY, extra = {}) {
    const texto = cssVar("--texto-2");
    const rejilla = cssVar("--borde");
    return {
      responsive: true, maintainAspectRatio: false,
      interaction: { mode: "nearest", intersect: false },
      plugins: {
        legend: { labels: { color: texto, usePointStyle: true, pointStyle: "circle", boxWidth: 8, padding: 16, font: { family: "Inter", size: 12.5, weight: 600 } } },
        tooltip: {
          backgroundColor: cssVar("--superficie"), titleColor: cssVar("--texto"), bodyColor: cssVar("--texto-2"),
          borderColor: cssVar("--borde-fuerte"), borderWidth: 1, padding: 12, cornerRadius: 10, boxPadding: 4,
          titleFont: { family: "Inter", weight: 700 }, bodyFont: { family: "Inter" },
        },
      },
      scales: {
        x: { ticks: { color: texto, font: { family: "Inter" } }, grid: { color: rejilla, drawTicks: false }, border: { display: false } },
        y: Object.assign({ ticks: { color: texto, font: { family: "Inter" } }, grid: { color: rejilla, drawTicks: false }, border: { display: false } }, ejeY),
      },
      ...extra,
    };
  }

  function linea(t, datos, extra = {}) {
    const c = colorTec(t);
    return Object.assign({
      label: TEC[t].nombre, data: datos, borderColor: c, backgroundColor: c,
      borderWidth: 2.5, pointRadius: 4, pointHoverRadius: 7, tension: 0.25,
    }, extra);
  }

  function crear(id, config) {
    if (graficas[id]) graficas[id].destroy();
    const lienzo = document.getElementById(id);
    if (typeof Chart === "undefined") {
      lienzo.parentElement.innerHTML = `<div class="sin-grafica">No se pudo cargar Chart.js (se necesita conexión a internet para las gráficas).</div>`;
      return;
    }
    graficas[id] = new Chart(lienzo, config);
  }

  function graficaTiempo(escala = "logarithmic") {
    crear("g-tiempo", {
      type: "line",
      data: { datasets: ORDEN_TEC.map((t) => linea(t, serieBench(t, "tiempo_s"))) },
      options: baseOpciones({
        type: escala, title: { display: true, text: "segundos", color: cssVar("--texto-3") },
        ticks: { color: cssVar("--texto-2"), callback: (v) => (escala === "logarithmic" && !/^1(\.0+)?e/.test(Number(v).toExponential())) ? "" : fmtTiempo(v) },
      }),
    });
    const g = graficas["g-tiempo"];
    if (!g) return;
    g.options.scales.x = ejeS(14);
    g.options.plugins.tooltip.callbacks = { title: (it) => `S = ${it[0].parsed.x}`, label: (it) => ` ${it.dataset.label}: ${fmtTiempo(it.parsed.y)}` };
    g.update();
  }

  function ejeS(max) {
    return { type: "linear", min: 1, max, title: { display: true, text: "S (sesiones)", color: cssVar("--texto-3") }, ticks: { stepSize: 1, color: cssVar("--texto-2") }, grid: { color: cssVar("--borde") }, border: { display: false } };
  }
  // Etiqueta solo potencias de 10 (cada `paso` órdenes de magnitud) como "10ⁿ".
  const ticksPotencia = (paso = 1) => (v) => {
    const e = Math.log10(v);
    if (Math.abs(e - Math.round(e)) > 1e-9 || Math.round(e) % paso) return "";
    return Math.round(e) < 4 ? Number(v).toLocaleString("es-CO") : "10" + superindice(Math.round(e));
  };

  function graficaTrabajo() {
    crear("g-trabajo", {
      type: "line",
      data: { datasets: ORDEN_TEC.map((t) => linea(t, serieBench(t, "trabajo"))) },
      options: baseOpciones({ type: "logarithmic", ticks: { color: cssVar("--texto-2"), callback: ticksPotencia(1) } }),
    });
    const g = graficas["g-trabajo"];
    if (!g) return;
    g.options.scales.x = ejeS(14);
    g.options.plugins.tooltip.callbacks = {
      title: (it) => `S = ${it[0].parsed.x}`,
      label: (it) => {
        const t = ORDEN_TEC[it.datasetIndex];
        return ` ${TEC[t].trabajoNombre}: ${fmtGrande(it.parsed.y)}`;
      },
    };
    g.update();
  }

  function graficaComplejidad() {
    const S = Array.from({ length: 20 }, (_, i) => i + 1);
    crear("g-complejidad", {
      type: "line",
      data: {
        datasets: ORDEN_TEC.map((t) => linea(t, S.map((s) => ({ x: s, y: TEC[t].ops(s) })), {
          label: `${TEC[t].nombre}  ${TEC[t].tiempo.replace(" peor caso", "")}`, pointRadius: 0, pointHoverRadius: 5,
          borderDash: t === "backtracking" ? [6, 4] : [],
        })),
      },
      options: baseOpciones({ type: "logarithmic", min: 1, ticks: { color: cssVar("--texto-2"), autoSkip: false, callback: ticksPotencia(6) } }),
    });
    const g = graficas["g-complejidad"];
    if (!g) return;
    g.options.scales.x = ejeS(20);
    g.options.plugins.tooltip.callbacks = { title: (it) => `S = ${it[0].parsed.x}`, label: (it) => ` ${TEC[ORDEN_TEC[it.datasetIndex]].nombre}: ${fmtGrande(it.parsed.y)} operaciones` };
    g.update();
  }

  function graficaBarrasCaso(id, valor, ejeY) {
    const casos = D.casos;
    crear(id, {
      type: "bar",
      data: {
        labels: casos.map((c) => { const [e, n] = NOMBRES_CASO[c.id] || ["", c.id]; return [`${e} ${n.toLowerCase()}`, `S = ${c.sesiones}`]; }),
        datasets: ORDEN_TEC.map((t) => ({
          label: TEC[t].nombre,
          data: casos.map((c) => (c.salidas[t] ? valor(c.salidas[t]) : null)),
          backgroundColor: colorTec(t), borderRadius: 6, maxBarThickness: 26,
        })),
      },
      options: baseOpciones(ejeY),
    });
    const g = graficas[id];
    if (!g) return;
    g.options.interaction = { mode: "index", intersect: false };
    g.options.plugins.tooltip.callbacks = { label: (it) => ` ${it.dataset.label}: ${it.raw == null ? "no ejecutada" : it.raw.toFixed(3)}` };
    g.update();
  }

  function graficaCalidadS() {
    crear("g-calidad-s", {
      type: "line",
      data: { datasets: ORDEN_TEC.map((t) => linea(t, serieBench(t, "calidad"), { tension: 0, clip: false })) },
      options: baseOpciones({ min: 0, max: 1, ticks: { color: cssVar("--texto-2"), stepSize: 0.2, callback: (v) => v.toFixed(1) } },
        { layout: { padding: { top: 8 } } }),
    });
    const g = graficas["g-calidad-s"];
    if (!g) return;
    g.options.scales.x = ejeS(14);
    g.options.plugins.tooltip.callbacks = { title: (it) => `S = ${it[0].parsed.x}`, label: (it) => ` ${it.dataset.label}: ${it.parsed.y.toFixed(3)}` };
    g.update();
  }

  function renderAceleracion() {
    const en4 = bench().filter((r) => r.S === 4);
    const fb = en4.find((r) => r.tecnica === "fuerza_bruta");
    if (!fb) { $("#aceleracion").innerHTML = `<div class="sin-grafica">Sin datos de benchmark.</div>`; return; }
    const filas = ORDEN_TEC.map((t) => en4.find((r) => r.tecnica === t)).filter(Boolean)
      .map((r) => ({ t: r.tecnica, x: fb.tiempo_s / r.tiempo_s, tiempo: r.tiempo_s }));
    const max = Math.log10(Math.max(...filas.map((f) => f.x)) + 1);
    $("#aceleracion").innerHTML = filas.map((f) => `
      <div class="ac-fila" style="--c:${colorTec(f.t)}">
        <div class="ac-top"><span>${TEC[f.t].nombre}</span><span>${f.x < 1.05 ? "1×" : fmtGrande(f.x) + "×"}</span></div>
        <div class="pista"><i style="width:${Math.max((Math.log10(f.x + 1) / max) * 100, 3)}%"></i></div>
        <div style="font-size:12px;color:var(--texto-3)">${fmtTiempo(f.tiempo)}</div>
      </div>`).join("") +
      `<p style="font-size:12px;color:var(--texto-3)">Barra en escala logarítmica.</p>`;
  }

  function renderCalculadora() {
    const S = +$("#s-calc").value;
    $("#s-calc-valor").textContent = S;
    $("#calc-resultados").innerHTML = ORDEN_TEC.map((t) => {
      const filas = bench().filter((r) => r.tecnica === t);
      const ref = filas[filas.length - 1];
      if (!ref) return "";
      const c = ref.tiempo_s / TEC[t].ops(ref.S);
      const est = c * TEC[t].ops(S);
      const medido = filas.find((r) => r.S === S);
      const valor = medido ? medido.tiempo_s : est;
      const lento = valor > 3600;
      return `<div class="calc-fila ${lento ? "lento" : ""}" style="--c:${colorTec(t)}">
        <span class="cn">${TEC[t].nombre}</span>
        <span class="cv">${fmtTiempo(valor)}<small>${medido ? "medido" : "estimado"}</small></span>
      </div>`;
    }).join("") + `<p style="font-size:12px;margin-top:6px">Estimación: tiempo medido en el mayor S × crecimiento de la fórmula teórica.</p>`;
  }
  $("#s-calc").addEventListener("input", renderCalculadora);

  function renderTablaComparativa() {
    const filas = [
      ["Idea", (t) => TEC[t].desc],
      ["Complejidad temporal", (t) => `<span class="mono">${TEC[t].tiempo}</span>`],
      ["Complejidad espacial", (t) => `<span class="mono">${TEC[t].espacio}</span>`],
      ["¿Qué optimiza?", (t) => ({ fuerza_bruta: "Calidad completa", greedy: "Calidad completa (decisión local)", backtracking: "Calidad completa", dinamica: "Preferencia (R1–R6)" })[t]],
      ["¿Garantiza el óptimo?", (t) => `<span class="${TEC[t].optimo[0]}">${TEC[t].optimo[1]}</span>`],
      ["¿Retrocede?", (t) => ({ fuerza_bruta: "No (lo prueba todo)", greedy: "No", backtracking: "Sí", dinamica: "No (reutiliza subproblemas)" })[t]],
      ["Límite práctico", (t) => TEC[t].limite],
      ["Cuándo usarla", (t) => ({
        fuerza_bruta: "Instancias diminutas, para validar a las demás.",
        greedy: "Respuesta inmediata con buena calidad en instancias grandes.",
        backtracking: "Óptimo exacto en instancias pequeñas, con poda.",
        dinamica: "Óptimo de preferencia en instancias medianas (S ≲ 14).",
      })[t]],
    ];
    $("#tabla-comparativa").innerHTML =
      `<thead><tr><th></th>${ORDEN_TEC.map((t) => `<th><span style="display:inline-flex;gap:8px;align-items:center"><span class="tt-punto" style="--c:var(${TEC[t].var});width:10px;height:10px"></span>${TEC[t].nombre}</span></th>`).join("")}</tr></thead>
       <tbody>${filas.map(([n, f]) => `<tr><td style="font-weight:700;white-space:nowrap">${n}</td>${ORDEN_TEC.map((t) => `<td>${f(t)}</td>`).join("")}</tr>`).join("")}</tbody>`;
  }

  function renderConclusiones() {
    const b4 = Object.fromEntries(bench().filter((r) => r.S === 4).map((r) => [r.tecnica, r]));
    const acel = b4.fuerza_bruta && b4.dinamica ? fmtGrande(b4.fuerza_bruta.tiempo_s / b4.dinamica.tiempo_s) : "miles de";
    $("#conclusiones").innerHTML = `
      <div class="conclusion"><h4>⚡ La explosión combinatoria es real</h4><p>Cada sesión adicional multiplica por 60 el trabajo de la fuerza bruta. Con S = 4 ya tarda minutos; con S = 6 tardaría meses.</p></div>
      <div class="conclusion"><h4>🧠 La DP cambia la base del exponente</h4><p>Pasar de 60<sup>S</sup> a 3<sup>S</sup> la hace ${acel}× más rápida en S = 4 y le permite llegar a S ≈ 14 con el óptimo de preferencia.</p></div>
      <div class="conclusion"><h4>⚖️ Rapidez y calidad no siempre van juntas</h4><p>Greedy es la más rápida y en los casos multisesión obtiene mejor calidad completa que la DP, pero no garantiza el óptimo. La DP gana en preferencia porque es lo único que optimiza.</p></div>`;
  }

  function renderAnalisis() {
    if (analisisListo) return;
    analisisListo = true;
    renderResumen();
    graficaTiempo($("[data-escala='g-tiempo'] .activo").dataset.valor);
    graficaTrabajo();
    graficaComplejidad();
    graficaBarrasCaso("g-calidad", (s) => s.metricas.calidad, { min: 0, max: 1, ticks: { color: cssVar("--texto-2") } });
    graficaBarrasCaso("g-preferencia", preferencia, { min: 0, ticks: { color: cssVar("--texto-2") } });
    graficaCalidadS();
    renderAceleracion();
    renderCalculadora();
    renderTablaComparativa();
    renderConclusiones();
  }
  $$("[data-escala='g-tiempo'] button").forEach((b) => b.addEventListener("click", () => {
    $$("[data-escala='g-tiempo'] button").forEach((x) => x.classList.toggle("activo", x === b));
    graficaTiempo(b.dataset.valor);
  }));

  // ------------------------------------------------------------------ inicio
  if (!casoActual().salidas[estado.tecnica]) estado.tecnica = ORDEN_TEC.find((t) => casoActual().salidas[t]);
  renderHorarios();
  aplicarTab();
})();
