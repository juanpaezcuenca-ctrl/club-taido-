var API = window.API_URL || "http://127.0.0.1:5000";
var SESSION_KEY = "taido_sesion";

var PANELS = {
  maestro:     "indexmaestro.html",
  familia:     "indexfamilia.html",
  practicante: "indexpracticante.html"
};

function getSession() {
  try {
    var raw = localStorage.getItem(SESSION_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch (e) {
    return null;
  }
}

function setSession(data) {
  localStorage.setItem(SESSION_KEY, JSON.stringify(data));
}

function clearSession() {
  localStorage.removeItem(SESSION_KEY);
}

function loginPageUrl() {
  var path = window.location.pathname || "";
  var enSubcarpeta = path.indexOf("/maestro/") !== -1
    || path.indexOf("/familia/") !== -1
    || path.indexOf("/practicante/") !== -1;
  return enSubcarpeta ? "../login.html" : "login.html";
}

function requireSession(tipoEsperado) {
  var s = getSession();
  if (!s || !s.id || !s.tipo) {
    window.location.href = loginPageUrl();
    return null;
  }
  if (tipoEsperado && s.tipo !== tipoEsperado) {
    window.location.href = PANELS[s.tipo] || loginPageUrl();
    return null;
  }
  return s;
}

function showLoginMsg(el, text, isError) {
  if (!el) return;
  el.textContent = text || "";
  el.className = "maestro-msg" + (text ? (isError ? " error" : " ok") : "");
}

function redirectToPanel(tipo) {
  var destino = PANELS[tipo];
  if (destino) window.location.href = destino;
}

function bindLogout(btnId) {
  var btn = document.getElementById(btnId);
  if (!btn) return;
  btn.onclick = function () {
    clearSession();
    window.location.href = loginPageUrl();
  };
}

function initLoginPage() {
  var form = document.getElementById("form-login-unificado");
  if (!form) return;

  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    var msg        = document.getElementById("msg-login");
    var rol        = document.getElementById("rol").value;
    var correo     = document.getElementById("correo").value.trim();
    var contrasena = document.getElementById("contrasena").value;

    if (!rol) {
      showLoginMsg(msg, "Selecciona tu rol antes de continuar.", true);
      return;
    }

    showLoginMsg(msg, "Verificando…", false);

    try {
      var res = await fetch(API + "/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rol: rol, correo: correo, contrasena: contrasena })
      });
      var data = await res.json().catch(function () { return {}; });

      if (res.status === 403) {
        showLoginMsg(msg, data.error || "Cuenta desactivada.", true);
        return;
      }
      if (!res.ok) {
        showLoginMsg(msg, data.error || "Rol, correo o contraseña no válidos.", true);
        return;
      }

      var usuario = data.usuario;
      if (!usuario || !usuario.tipo) {
        showLoginMsg(msg, "Respuesta del servidor inválida.", true);
        return;
      }

      setSession(usuario);
      redirectToPanel(usuario.tipo);

    } catch (err) {
      showLoginMsg(msg, "Sin conexión al servidor. Asegúrate de ejecutar python app.py.", true);
    }
  });
}

initLoginPage();