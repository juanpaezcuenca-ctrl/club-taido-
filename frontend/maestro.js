// ── UTILIDADES ───────────────────────────────────────────────────────────────

async function apiFetch(path, options) {
  var res = await fetch(API + path, options || {});
  var data = {};
  try { data = await res.json(); } catch(e) {}
  if (!res.ok) throw new Error(data.error || "Error en la solicitud");
  return data;
}

function showMsg(el, text, error) {
  if (!el) return;
  el.textContent = text || "";
  el.className = "maestro-msg" + (text ? (error ? " error" : " ok") : "");
}

function renderTabla(el, datos, acciones) {
  if (!el) return;
  if (!datos || !datos.length) { el.innerHTML = '<p class="maestro-empty">No hay registros.</p>'; return; }
  var headers = Object.keys(datos[0]);
  var html = '<table class="tabla-listado"><thead><tr>';
  headers.forEach(function(h) { html += '<th>' + h.toUpperCase() + '</th>'; });
  if (acciones) html += '<th>ACCIONES</th>';
  html += '</tr></thead><tbody>';
  datos.forEach(function(fila) {
    html += '<tr>';
    headers.forEach(function(h) { html += '<td>' + (fila[h] == null ? "" : fila[h]) + '</td>'; });
    if (acciones) html += '<td>' + acciones(fila) + '</td>';
    html += '</tr>';
  });
  html += '</tbody></table>';
  el.innerHTML = html;
}


// ── PANEL ────────────────────────────────────────────────────────────────────

function initPanel() {
  if (!document.getElementById("nombre-maestro")) return;

  var sesion = requireSession("maestro");
  if (!sesion) return;
  var idMaestro = sesion.id;

  document.getElementById("nombre-maestro").textContent = sesion.nombre || "Maestro";
  document.getElementById("correo-maestro").textContent  = sesion.correo || "";
  bindLogout("btn-salir");

  // ── Navegación tabs ──────────────────────────────────────────────────────
  document.querySelectorAll(".maestro-nav button[data-tab]").forEach(function(btn) {
    btn.onclick = function() {
      var tab = btn.getAttribute("data-tab");
      document.querySelectorAll(".maestro-nav button[data-tab]").forEach(function(b) { b.classList.toggle("active", b === btn); });
      document.querySelectorAll(".maestro-tab").forEach(function(s) { s.classList.toggle("active", s.id === "tab-" + tab); });
      if (tab === "maestros")     cargarMaestros();
      if (tab === "practicantes") cargarPracticantes();
      if (tab === "eventos")      cargarEventos();
      if (tab === "pagos")        cargarPagos();
      if (tab === "informes")     { cargarInformes(); cargarEventosSelect(); }
      if (tab === "guias")        cargarGuias();
    };
  });


  // ══════════════════════════════════════════════════════════════════════════
  // MAESTROS
  // ══════════════════════════════════════════════════════════════════════════

  function cargarMaestros(q) {
    var url = "/maestros" + (q ? "?q=" + encodeURIComponent(q) : "");
    var el  = document.getElementById("lista-maestros");
    apiFetch(url).then(function(datos) {
      renderTabla(el, datos, function(fila) {
        return '<button class="btn-edit" onclick="editarMaestro(' + fila.id + ',\'' + fila.nombre + '\',\'' + fila.correo + '\')">✏️ Editar</button>' +
               '<button class="btn-del"  onclick="eliminarMaestro(' + fila.id + ')">🗑️ Eliminar</button>';
      });
    }).catch(function(e) { el.innerHTML = '<p class="maestro-msg error">' + e.message + '</p>'; });
  }

  document.getElementById("btn-buscar-maestro").onclick  = function() { cargarMaestros(document.getElementById("buscar-maestro").value.trim()); };
  document.getElementById("btn-todos-maestros").onclick  = function() { document.getElementById("buscar-maestro").value=""; cargarMaestros(); };
  document.getElementById("buscar-maestro").onkeydown    = function(e) { if(e.key==="Enter") cargarMaestros(this.value.trim()); };

  document.getElementById("form-maestro").onsubmit = async function(e) {
    e.preventDefault();
    var msg = document.getElementById("msg-maestro");
    var fd  = new FormData(e.target);
    try {
      await apiFetch("/maestros", { method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ nombre: fd.get("nombre"), correo: fd.get("correo"), contrasena: fd.get("contrasena") }) });
      showMsg(msg, "Maestro creado correctamente.", false);
      e.target.reset(); cargarMaestros();
    } catch(err) { showMsg(msg, err.message, true); }
  };

  window.editarMaestro = function(id, nombre, correo) {
    document.getElementById("edit-maestro-card").style.display = "block";
    document.getElementById("edit-maestro-id").value      = id;
    document.getElementById("edit-maestro-nombre").value  = nombre;
    document.getElementById("edit-maestro-correo").value  = correo;
    document.getElementById("edit-maestro-contrasena").value = "";
    document.getElementById("edit-maestro-card").scrollIntoView({behavior:"smooth"});
  };

  document.getElementById("cancel-edit-maestro").onclick = function() {
    document.getElementById("edit-maestro-card").style.display = "none";
  };

  document.getElementById("form-edit-maestro").onsubmit = async function(e) {
    e.preventDefault();
    var msg   = document.getElementById("msg-edit-maestro");
    var id    = document.getElementById("edit-maestro-id").value;
    var body  = {
      nombre:     document.getElementById("edit-maestro-nombre").value,
      correo:     document.getElementById("edit-maestro-correo").value,
      contrasena: document.getElementById("edit-maestro-contrasena").value || undefined
    };
    try {
      await apiFetch("/actualizar_maestro/" + id, { method:"PUT", headers:{"Content-Type":"application/json"}, body: JSON.stringify(body) });
      showMsg(msg, "Maestro actualizado.", false);
      document.getElementById("edit-maestro-card").style.display = "none";
      cargarMaestros();
    } catch(err) { showMsg(msg, err.message, true); }
  };

  window.eliminarMaestro = async function(id) {
    if (!confirm("¿Eliminar este maestro?")) return;
    try {
      await apiFetch("/eliminar_maestro/" + id, { method:"DELETE" });
      cargarMaestros();
    } catch(err) { alert(err.message); }
  };


  // ══════════════════════════════════════════════════════════════════════════
  // PRACTICANTES
  // ══════════════════════════════════════════════════════════════════════════

  function cargarPracticantes(q) {
    var url = "/practicantes" + (q ? "?q=" + encodeURIComponent(q) : "");
    var el  = document.getElementById("lista-practicantes");
    apiFetch(url).then(function(datos) {
      renderTabla(el, datos, function(fila) {
        return '<button class="btn-edit" onclick="editarPracticante(' + fila.id + ',\'' + fila.nombre + '\',\'' + fila.correo + '\',\'' + fila.actividad + '\')">✏️ Editar</button>' +
               '<button class="btn-del"  onclick="eliminarPracticante(' + fila.id + ')">🗑️ Eliminar</button>';
      });
    }).catch(function(e) { el.innerHTML = '<p class="maestro-msg error">' + e.message + '</p>'; });
  }

  document.getElementById("btn-buscar-practicante").onclick = function() { cargarPracticantes(document.getElementById("buscar-practicante").value.trim()); };
  document.getElementById("btn-todos-practicantes").onclick = function() { document.getElementById("buscar-practicante").value=""; cargarPracticantes(); };
  document.getElementById("buscar-practicante").onkeydown   = function(e) { if(e.key==="Enter") cargarPracticantes(this.value.trim()); };

  document.getElementById("form-practicante").onsubmit = async function(e) {
    e.preventDefault();
    var msg = document.getElementById("msg-practicante");
    var fd  = new FormData(e.target);
    try {
      var res = await apiFetch("/nuevo_practicante", { method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ NOMBRE: fd.get("NOMBRE"), CORREO: fd.get("CORREO"), ACTIVIDAD: fd.get("ACTIVIDAD"), ID_MAESTRO: idMaestro, CONTRASENA: fd.get("CONTRASENA") }) });
      showMsg(msg, res.mensaje, false);
      if (res.practicante && res.familia) {
        var div = document.getElementById("info-familia-creada");
        div.style.display = "block";
        document.getElementById("detalle-creacion").innerHTML =
          "<p><strong>👤 Practicante</strong></p>" +
          "<p>Correo: " + res.practicante.correo + " | Contraseña: " + res.practicante.contrasena + "</p>" +
          "<p style='margin-top:8px;'><strong>👨‍👩‍👦 " + res.familia.nombre + "</strong></p>" +
          "<p>Correo: " + res.familia.correo + " | Contraseña: " + res.familia.contrasena + "</p>" +
          "<p style='font-size:0.78rem;color:#888;margin-top:6px;'>Entrega estos datos a la familia y al practicante.</p>";
      }
      e.target.reset(); cargarPracticantes();
    } catch(err) { showMsg(msg, err.message, true); }
  };

  window.editarPracticante = function(id, nombre, correo, actividad) {
    document.getElementById("edit-practicante-card").style.display = "block";
    document.getElementById("edit-prac-id").value         = id;
    document.getElementById("edit-prac-nombre").value     = nombre;
    document.getElementById("edit-prac-correo").value     = correo;
    document.getElementById("edit-prac-actividad").value  = actividad;
    document.getElementById("edit-prac-contrasena").value = "";
    document.getElementById("edit-practicante-card").scrollIntoView({behavior:"smooth"});
  };

  document.getElementById("cancel-edit-practicante").onclick = function() {
    document.getElementById("edit-practicante-card").style.display = "none";
  };

  document.getElementById("form-edit-practicante").onsubmit = async function(e) {
    e.preventDefault();
    var msg = document.getElementById("msg-edit-practicante");
    var id  = document.getElementById("edit-prac-id").value;
    try {
      await apiFetch("/actualizar_practicante/" + id, { method:"PUT", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({
          NOMBRE:     document.getElementById("edit-prac-nombre").value,
          CORREO:     document.getElementById("edit-prac-correo").value,
          ACTIVIDAD:  document.getElementById("edit-prac-actividad").value,
          CONTRASENA: document.getElementById("edit-prac-contrasena").value || undefined
        }) });
      showMsg(msg, "Practicante actualizado.", false);
      document.getElementById("edit-practicante-card").style.display = "none";
      cargarPracticantes();
    } catch(err) { showMsg(msg, err.message, true); }
  };

  window.eliminarPracticante = async function(id) {
    if (!confirm("¿Eliminar este practicante y su familia vinculada?")) return;
    try {
      await apiFetch("/eliminar_practicante/" + id, { method:"DELETE" });
      cargarPracticantes();
    } catch(err) { alert(err.message); }
  };


  // ══════════════════════════════════════════════════════════════════════════
  // EVENTOS
  // ══════════════════════════════════════════════════════════════════════════

  function cargarEventos(q) {
    var url = "/eventos" + (q ? "?q=" + encodeURIComponent(q) : "");
    var el  = document.getElementById("lista-eventos");
    apiFetch(url).then(function(datos) {
      renderTabla(el, datos, function(fila) {
        return '<button class="btn-edit" onclick="editarEvento(' + fila.id + ',\'' + fila.titulo + '\',\'' + fila.fecha + '\',\'' + fila.tipo + '\')">✏️ Editar</button>' +
               '<button class="btn-del"  onclick="eliminarEvento(' + fila.id + ')">🗑️ Eliminar</button>';
      });
    }).catch(function(e) { el.innerHTML = '<p class="maestro-msg error">' + e.message + '</p>'; });
  }

  document.getElementById("btn-buscar-evento").onclick  = function() { cargarEventos(document.getElementById("buscar-evento").value.trim()); };
  document.getElementById("btn-todos-eventos").onclick  = function() { document.getElementById("buscar-evento").value=""; cargarEventos(); };
  document.getElementById("buscar-evento").onkeydown    = function(e) { if(e.key==="Enter") cargarEventos(this.value.trim()); };

  document.getElementById("form-evento").onsubmit = async function(e) {
    e.preventDefault();
    var msg = document.getElementById("msg-evento");
    var fd  = new FormData(e.target);
    try {
      var res = await apiFetch("/postear_evento", { method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ NOMBRE: fd.get("NOMBRE"), TIPO: fd.get("TIPO"), FECHA: fd.get("FECHA") }) });
      showMsg(msg, res.mensaje, false);
      e.target.reset(); cargarEventos();
    } catch(err) { showMsg(msg, err.message, true); }
  };

  window.editarEvento = function(id, titulo, fecha, tipo) {
    document.getElementById("edit-evento-card").style.display = "block";
    document.getElementById("edit-evento-id").value     = id;
    document.getElementById("edit-evento-nombre").value = titulo;
    document.getElementById("edit-evento-fecha").value  = fecha;
    document.getElementById("edit-evento-tipo").value   = tipo;
    document.getElementById("edit-evento-card").scrollIntoView({behavior:"smooth"});
  };

  document.getElementById("cancel-edit-evento").onclick = function() {
    document.getElementById("edit-evento-card").style.display = "none";
  };

  document.getElementById("form-edit-evento").onsubmit = async function(e) {
    e.preventDefault();
    var msg = document.getElementById("msg-edit-evento");
    var id  = document.getElementById("edit-evento-id").value;
    try {
      await apiFetch("/actualizar_evento/" + id, { method:"PUT", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({
          NOMBRE: document.getElementById("edit-evento-nombre").value,
          FECHA:  document.getElementById("edit-evento-fecha").value,
          TIPO:   document.getElementById("edit-evento-tipo").value
        }) });
      showMsg(msg, "Evento actualizado.", false);
      document.getElementById("edit-evento-card").style.display = "none";
      cargarEventos();
    } catch(err) { showMsg(msg, err.message, true); }
  };

  window.eliminarEvento = async function(id) {
    if (!confirm("¿Eliminar este evento?")) return;
    try {
      await apiFetch("/eliminar_evento/" + id, { method:"DELETE" });
      cargarEventos();
    } catch(err) { alert(err.message); }
  };


  // ══════════════════════════════════════════════════════════════════════════
  // PAGOS
  // ══════════════════════════════════════════════════════════════════════════

  function cargarPagos(q) {
    var url = "/pagos" + (q ? "?q=" + encodeURIComponent(q) : "");
    var el  = document.getElementById("lista-pagos");
    apiFetch(url).then(function(datos) {
      renderTabla(el, datos, null);
    }).catch(function(e) { el.innerHTML = '<p class="maestro-msg error">' + e.message + '</p>'; });
  }

  document.getElementById("btn-buscar-pago").onclick  = function() { cargarPagos(document.getElementById("buscar-pago-id").value.trim()); };
  document.getElementById("btn-todos-pagos").onclick  = function() { document.getElementById("buscar-pago-id").value=""; cargarPagos(); };
  document.getElementById("buscar-pago-id").onkeydown = function(e) { if(e.key==="Enter") cargarPagos(this.value.trim()); };


  // ══════════════════════════════════════════════════════════════════════════
  // INFORMES — búsqueda por nombre (FIX 6)
  // ══════════════════════════════════════════════════════════════════════════

  var timeoutBusqueda;
  document.getElementById("buscar-prac-informe").oninput = function() {
    var q = this.value.trim();
    clearTimeout(timeoutBusqueda);
    var sug = document.getElementById("sugerencias-informe");
    if (!q) { sug.innerHTML = ""; sug.style.display="none"; return; }
    timeoutBusqueda = setTimeout(async function() {
      try {
        var lista = await apiFetch("/buscar_practicantes?q=" + encodeURIComponent(q));
        if (!lista.length) { sug.innerHTML=""; sug.style.display="none"; return; }
        sug.style.display = "block";
        sug.innerHTML = lista.map(function(p) {
          return '<div onclick="seleccionarPracticante(' + p.id + ',\'' + p.nombre + '\')">' + p.nombre + '</div>';
        }).join("");
      } catch(e) {}
    }, 300);
  };

  window.seleccionarPracticante = function(id, nombre) {
    document.getElementById("buscar-prac-informe").value = nombre;
    document.getElementById("id-prac-informe").value     = id;
    document.getElementById("sugerencias-informe").style.display = "none";
  };

  function cargarEventosSelect() {
    var sel = document.getElementById("select-eventos-informe");
    sel.innerHTML = '<option value="">Seleccione un torneo…</option>';
    apiFetch("/eventos").then(function(eventos) {
      eventos.forEach(function(ev) {
        var opt = document.createElement("option");
        opt.value = ev.titulo; opt.textContent = ev.titulo;
        sel.appendChild(opt);
      });
    }).catch(function(){});
  }

  document.getElementById("form-informe").onsubmit = async function(e) {
    e.preventDefault();
    var msg = document.getElementById("msg-informe");
    var id  = document.getElementById("id-prac-informe").value;
    var torneo = document.getElementById("select-eventos-informe").value;
    if (!id) { showMsg(msg, "Selecciona un practicante de la lista.", true); return; }
    if (!torneo) { showMsg(msg, "Selecciona un torneo de la lista.", true); return; }
    try {
      await apiFetch("/publicar_rendimiento", { method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({
          id_practicante: parseInt(id),
          nombre_torneo:  torneo,
          comentarios:    document.getElementById("comentarios-informe").value
        }) });
      showMsg(msg, "Informe publicado con éxito.", false);
      document.getElementById("buscar-prac-informe").value = "";
      document.getElementById("id-prac-informe").value = "";
      document.getElementById("select-eventos-informe").value = "";
      document.getElementById("comentarios-informe").value = "";
      cargarInformes();
    } catch(err) { showMsg(msg, err.message, true); }
  };

  function cargarInformes() {
    var el = document.getElementById("lista-informes");
    apiFetch("/informes").then(function(datos) {
      if (!datos || !datos.length) { el.innerHTML = '<p class="maestro-empty">No hay informes publicados.</p>'; return; }
      var html = '<table class="tabla-listado"><thead><tr><th>PRACTICANTE</th><th>TORNEO</th><th>COMENTARIOS</th></tr></thead><tbody>';
      datos.forEach(function(r) {
        html += '<tr>';
        html += '<td>' + (r.practicante || "") + '</td>';
        html += '<td>' + (r.torneo && r.torneo !== "None" ? r.torneo : '<em style="color:#aaa;">Sin torneo registrado</em>') + '</td>';
        html += '<td>' + (r.comentarios || "") + '</td>';
        html += '</tr>';
      });
      html += '</tbody></table>';
      el.innerHTML = html;
    }).catch(function(e) { el.innerHTML = '<p class="maestro-msg error">' + e.message + '</p>'; });
  }


  // ══════════════════════════════════════════════════════════════════════════
  // GUÍAS
  // ══════════════════════════════════════════════════════════════════════════

  function cargarGuias() {
    var el = document.getElementById("lista-guias");
    apiFetch("/guias").then(function(datos) {
      if (!datos.length) { el.innerHTML='<p class="maestro-empty">No hay guías.</p>'; return; }
      var html = '<table class="tabla-listado"><thead><tr><th>ID</th><th>TÍTULO</th><th>NIVEL</th><th>ABRIR</th><th>ACCIONES</th></tr></thead><tbody>';
      datos.forEach(function(g) {
        html += '<tr><td>' + g.id + '</td><td>' + g.titulo + '</td><td>' + g.nivel + '</td>';
        html += '<td><a href="' + API + '/uploads/guias/' + encodeURIComponent(g.url_recurso) + '" target="_blank" class="btn-edit">📥 Abrir</a></td>';
        html += '<td><button class="btn-del" onclick="eliminarGuia(' + g.id + ')">🗑️ Eliminar</button></td></tr>';
      });
      html += '</tbody></table>';
      el.innerHTML = html;
    }).catch(function(e) { el.innerHTML='<p class="maestro-msg error">'+e.message+'</p>'; });
  }

  document.getElementById("form-guia").onsubmit = async function(e) {
    e.preventDefault();
    var msg = document.getElementById("msg-guia");
    var fd  = new FormData(e.target);
    fd.append("id_maestro", idMaestro);
    try {
      await apiFetch("/publicar_guias", { method:"POST", body: fd });
      showMsg(msg, "Guía publicada con éxito.", false);
      e.target.reset(); cargarGuias();
    } catch(err) { showMsg(msg, err.message, true); }
  };

  window.eliminarGuia = async function(id) {
    if (!confirm("¿Eliminar esta guía?")) return;
    try {
      await apiFetch("/eliminar_guia/" + id, { method:"DELETE" });
      cargarGuias();
    } catch(err) { alert(err.message); }
  };

  // Carga inicial
  cargarMaestros();
}

initPanel();