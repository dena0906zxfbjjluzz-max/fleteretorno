"""
FleteRetorno — marketplace de fletes tipo InDrive.
Publicar → contraoferta → aceptar. Supabase opcional; sin secrets = local.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

COMISION_PCT = 0.05

st.set_page_config(
    page_title="FleteRetorno",
    page_icon="🚛",
    layout="centered",
    initial_sidebar_state="expanded",
)

USUARIOS = {
    "comerciante": {"clave": "santaanita2026", "rol": "comerciante", "nombre": "Ana Torres"},
    "chofer": {"clave": "flete2026", "rol": "chofer", "nombre": "Luis Quispe"},
}

DNI_BANEADOS = {"45892174", "10234567"}
PLACAS_BANEADAS = {"F3V-894", "A1B-123"}
SANTA_ANITA = (-12.045, -76.953)


def inject_styles() -> None:
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

html, body, [class*="css"] {
  font-family: 'DM Sans', sans-serif;
}

.stApp {
  background:
    radial-gradient(1200px 500px at 10% -10%, rgba(193,241,29,0.12), transparent 55%),
    radial-gradient(900px 400px at 100% 0%, rgba(46,120,80,0.18), transparent 50%),
    #0B0F0C;
}

/* Hide Streamlit chrome noise */
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }

.block-container {
  padding-top: 1.4rem !important;
  padding-bottom: 3rem !important;
  max-width: 760px;
}

h1, h2, h3, .fr-brand {
  font-family: 'Space Grotesk', sans-serif !important;
  letter-spacing: -0.02em;
}

/* Brand / login */
.fr-hero {
  text-align: center;
  padding: 2.2rem 0 0.2rem;
}
.fr-mark {
  width: 56px;
  height: 56px;
  margin: 0 auto 1rem;
  border-radius: 16px;
  background: linear-gradient(145deg, #C1F11D 0%, #8BC34A 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.55rem;
  box-shadow: 0 10px 30px rgba(193,241,29,0.22);
}
.fr-brand {
  font-size: 2.55rem;
  font-weight: 700;
  color: #F2F5F0;
  margin: 0;
  line-height: 1.05;
}
.fr-brand span { color: #C1F11D; }
.fr-tag {
  margin: 0.7rem auto 0;
  color: #A8B3A6;
  font-size: 1.05rem;
  font-weight: 500;
  max-width: 28rem;
  line-height: 1.45;
}
.fr-steps {
  display: flex;
  justify-content: center;
  gap: 0.55rem;
  flex-wrap: wrap;
  margin-top: 1.15rem;
}
.fr-step {
  padding: 0.35rem 0.7rem;
  border-radius: 999px;
  background: rgba(242,245,240,0.05);
  border: 1px solid rgba(242,245,240,0.1);
  color: #C8D0C6;
  font-size: 0.78rem;
  font-weight: 600;
}
.fr-login-title {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 1.05rem;
  font-weight: 600;
  color: #F2F5F0;
  margin: 1.35rem 0 0.35rem;
  text-align: center;
}

/* Login form as a product card */
div[data-testid="stForm"] {
  background: rgba(21,27,22,0.94);
  border: 1px solid rgba(242,245,240,0.1);
  border-radius: 22px;
  padding: 1.25rem 1.1rem 1rem;
  box-shadow: 0 18px 50px rgba(0,0,0,0.35);
}

.fr-card {
  background: #151B16;
  border: 1px solid rgba(242,245,240,0.08);
  border-radius: 18px;
  padding: 1.15rem 1.2rem;
  margin: 0.85rem 0;
}
.fr-card-title {
  font-family: 'Space Grotesk', sans-serif;
  font-weight: 600;
  font-size: 1.05rem;
  margin: 0 0 0.25rem;
  color: #F2F5F0;
}
.fr-muted { color: #9AA69A; font-size: 0.9rem; margin: 0; }
.fr-price {
  font-family: 'Space Grotesk', sans-serif;
  font-weight: 700;
  font-size: 1.45rem;
  color: #C1F11D;
  margin: 0.55rem 0 0.15rem;
}
.fr-badge {
  display: inline-block;
  padding: 0.15rem 0.55rem;
  border-radius: 8px;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}
.fr-badge-ok { background: rgba(193,241,29,0.15); color: #C1F11D; }
.fr-badge-wait { background: rgba(255,193,7,0.15); color: #FFC107; }
.fr-badge-go { background: rgba(33,150,243,0.18); color: #64B5F6; }

div[data-testid="stSidebar"] {
  background: #101510;
  border-right: 1px solid rgba(242,245,240,0.06);
}
div[data-testid="stSidebar"] .fr-side-brand {
  font-family: 'Space Grotesk', sans-serif;
  font-weight: 700;
  font-size: 1.2rem;
  color: #F2F5F0;
  margin: 0.2rem 0 0.9rem;
}
div[data-testid="stSidebar"] .fr-side-brand span { color: #C1F11D; }

.fr-profile {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  margin-bottom: 0.85rem;
  border-radius: 16px;
  background: rgba(193,241,29,0.06);
  border: 1px solid rgba(193,241,29,0.18);
}
.fr-avatar {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  background: #C1F11D;
  color: #0B0F0C;
  font-family: 'Space Grotesk', sans-serif;
  font-weight: 700;
  font-size: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.fr-profile-name {
  margin: 0;
  font-weight: 700;
  color: #F2F5F0;
  font-size: 0.95rem;
  line-height: 1.2;
}
.fr-profile-role {
  margin: 0.15rem 0 0;
  color: #A8B3A6;
  font-size: 0.78rem;
  font-weight: 500;
}
.fr-nav-label {
  margin: 0.35rem 0 0.45rem;
  color: #7E8A7C;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.fr-page-head {
  margin: 0 0 1rem;
}
.fr-page-head h1 {
  margin: 0 !important;
  font-size: 1.65rem !important;
}
.fr-page-head p {
  margin: 0.35rem 0 0;
  color: #9AA69A;
  font-size: 0.95rem;
}
.fr-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.55rem;
  margin: 0 0 1.1rem;
}
.fr-stat {
  background: #151B16;
  border: 1px solid rgba(242,245,240,0.08);
  border-radius: 14px;
  padding: 0.75rem 0.65rem;
  text-align: center;
}
.fr-stat b {
  display: block;
  font-family: 'Space Grotesk', sans-serif;
  font-size: 1.2rem;
  color: #C1F11D;
  line-height: 1.1;
}
.fr-stat span {
  display: block;
  margin-top: 0.25rem;
  color: #9AA69A;
  font-size: 0.72rem;
  font-weight: 600;
}

div[data-testid="stSidebar"] div[role="radiogroup"] label {
  background: transparent !important;
  border-radius: 12px !important;
  padding: 0.45rem 0.55rem !important;
  margin-bottom: 0.2rem !important;
}
div[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
  background: rgba(242,245,240,0.04) !important;
}

/* Primary buttons → InDrive lime */
.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"] {
  background: #C1F11D !important;
  color: #0B0F0C !important;
  border: none !important;
  font-weight: 700 !important;
  border-radius: 14px !important;
}
.stButton > button[kind="primary"]:hover,
.stFormSubmitButton > button[kind="primary"]:hover {
  background: #D4F85A !important;
  color: #0B0F0C !important;
}
.stButton > button, .stFormSubmitButton > button {
  border-radius: 14px !important;
  font-weight: 600 !important;
}

/* Inputs */
div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] > div,
div[data-baseweb="base-input"] {
  border-radius: 12px !important;
}

.fr-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.35rem;
}
.fr-topbar h1 {
  margin: 0 !important;
  font-size: 1.55rem !important;
}
</style>
        """,
        unsafe_allow_html=True,
    )


def secrets_supabase() -> tuple[str | None, str | None]:
    try:
        url = st.secrets.get("SUPABASE_URL") or st.secrets.get("supabase_url")
        key = st.secrets.get("SUPABASE_KEY") or st.secrets.get("supabase_key")
        if (not url or not key) and "credenciales" in st.secrets:
            c = st.secrets["credenciales"]
            url = url or c.get("SUPABASE_URL")
            key = key or c.get("SUPABASE_KEY")
        if url and key:
            return str(url).strip().rstrip("/"), str(key).strip()
    except Exception:
        pass
    return None, None


@st.cache_resource
def get_supabase_client():
    url, key = secrets_supabase()
    if not url or not key:
        return None
    try:
        from supabase import create_client

        return create_client(url, key)
    except Exception:
        return None


def en_nube() -> bool:
    return get_supabase_client() is not None


def init_demo_store() -> None:
    if "fletes" not in st.session_state:
        st.session_state.fletes = [
            {
                "id": 1,
                "origen": "Santa Anita (Lima)",
                "destino": "Huancayo",
                "descripcion": "20 Tn fertilizante",
                "precio": 1500.0,
                "estado": "DISPONIBLE",
                "comerciante": "Ana Torres",
                "chofer": None,
                "precio_acordado": None,
            },
            {
                "id": 2,
                "origen": "Santa Anita (Lima)",
                "destino": "Chiclayo",
                "descripcion": "15 Tn envases vacíos (retorno)",
                "precio": 2200.0,
                "estado": "DISPONIBLE",
                "comerciante": "Ana Torres",
                "chofer": None,
                "precio_acordado": None,
            },
        ]
    if "siguiente_id_flete" not in st.session_state:
        st.session_state.siguiente_id_flete = 3
    if "ofertas" not in st.session_state:
        st.session_state.ofertas = []
    if "siguiente_id_oferta" not in st.session_state:
        st.session_state.siguiente_id_oferta = 1
    if "perfil_chofer" not in st.session_state:
        st.session_state.perfil_chofer = {
            "dni": "",
            "nombre": "",
            "licencia": "",
            "placa": "",
            "celular": "",
            "estado_verificacion": "PENDIENTE",
        }
    if "camiones_gps" not in st.session_state:
        st.session_state.camiones_gps = {
            "Camión 1 (Papas)": {
                "chofer": "Juan Pérez",
                "lat": -12.045,
                "lon": -75.210,
                "ruta": "Huancayo → Lima",
                "carga": "20 Tn Papa Única",
            },
            "Camión 2 (Arroz)": {
                "chofer": "Carlos Soto",
                "lat": -11.100,
                "lon": -77.600,
                "ruta": "Chiclayo → Lima",
                "carga": "30 Tn Arroz Extra",
            },
        }
    if "lista_negra" not in st.session_state:
        st.session_state.lista_negra = {
            "dnis": set(DNI_BANEADOS),
            "placas": set(PLACAS_BANEADAS),
        }


def verificar_lista_negra(dni: str, placa: str) -> str:
    init_demo_store()
    d = (dni or "").strip()
    p = (placa or "").strip().upper()
    if d in st.session_state.lista_negra["dnis"]:
        return "DNI_BLOQUEADO"
    if p in st.session_state.lista_negra["placas"]:
        return "PLACA_BLOQUEADA"
    return "PERMITIDO"


def flete_por_id(fid: int) -> dict[str, Any] | None:
    for f in st.session_state.fletes:
        if f["id"] == fid:
            return f
    return None


def comision_de(monto: float) -> float:
    return round(float(monto) * COMISION_PCT, 2)


def badge_estado(estado: str) -> str:
    e = (estado or "").upper()
    if e == "DISPONIBLE":
        return '<span class="fr-badge fr-badge-ok">Disponible</span>'
    if e == "EN RUTA":
        return '<span class="fr-badge fr-badge-go">En ruta</span>'
    if e in ("PENDIENTE", "APROBADO"):
        cls = "fr-badge-wait" if e == "PENDIENTE" else "fr-badge-ok"
        return f'<span class="fr-badge {cls}">{e.title()}</span>'
    return f'<span class="fr-badge fr-badge-wait">{estado}</span>'


inject_styles()

# ---------- LOGIN ----------
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "usuario" not in st.session_state:
    st.session_state.usuario = ""
if "rol" not in st.session_state:
    st.session_state.rol = ""
if "nombre_sesion" not in st.session_state:
    st.session_state.nombre_sesion = ""

if not st.session_state.autenticado:
    st.markdown(
        """
<div class="fr-hero">
  <div class="fr-mark">🚛</div>
  <p class="fr-brand">Flete<span>Retorno</span></p>
  <p class="fr-tag">Tú pones el precio. El chofer contraoferta.<br>Cierras el trato en minutos.</p>
  <div class="fr-steps">
    <span class="fr-step">1 · Publica</span>
    <span class="fr-step">2 · Contraoferta</span>
    <span class="fr-step">3 · Acepta</span>
  </div>
</div>
<p class="fr-login-title">Inicia sesión</p>
        """,
        unsafe_allow_html=True,
    )
    with st.form("login"):
        u = st.text_input("Usuario", placeholder="comerciante o chofer")
        c = st.text_input("Contraseña", type="password", placeholder="Tu contraseña")
        ok = st.form_submit_button("Ingresar", type="primary", use_container_width=True)
    if ok:
        u = (u or "").strip()
        reg = USUARIOS.get(u)
        if reg and c == reg["clave"]:
            st.session_state.autenticado = True
            st.session_state.usuario = u
            st.session_state.rol = reg["rol"]
            st.session_state.nombre_sesion = reg["nombre"]
            init_demo_store()
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")
    with st.expander("Acceso de prueba"):
        st.markdown(
            """
| Rol | Usuario | Contraseña |
|-----|---------|------------|
| Comerciante | `comerciante` | `santaanita2026` |
| Chofer | `chofer` | `flete2026` |
            """
        )
    st.stop()

init_demo_store()

# ---------- SHELL ----------
nombre_ui = st.session_state.nombre_sesion
iniciales = "".join(p[0] for p in nombre_ui.split()[:2]).upper() or "FR"
es_comerciante = st.session_state.rol == "comerciante"
rol_label = "Comerciante" if es_comerciante else "Chofer"

st.sidebar.markdown(
    '<p class="fr-side-brand">Flete<span>Retorno</span></p>',
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    f"""
<div class="fr-profile">
  <div class="fr-avatar">{iniciales}</div>
  <div>
    <p class="fr-profile-name">{nombre_ui}</p>
    <p class="fr-profile-role">{rol_label} · Santa Anita</p>
  </div>
</div>
    """,
    unsafe_allow_html=True,
)
st.sidebar.markdown('<p class="fr-nav-label">Menú</p>', unsafe_allow_html=True)

if es_comerciante:
    seccion = st.sidebar.radio(
        "Menú",
        ["📦 Publicar carga", "💬 Ofertas", "🗺️ Mapa", "📡 Monitoreo", "📄 Evidencia"],
        label_visibility="collapsed",
    )
else:
    seccion = st.sidebar.radio(
        "Menú",
        ["🆔 Mi perfil", "🚚 Cargas", "🗺️ En ruta", "🔒 Validar"],
        label_visibility="collapsed",
    )

# Quita emoji del inicio → clave estable
seccion_key = seccion.split(" ", 1)[-1].strip()

st.sidebar.write("")
if st.sidebar.button("Cerrar sesión", use_container_width=True):
    for k in ("autenticado", "usuario", "rol", "nombre_sesion"):
        st.session_state[k] = False if k == "autenticado" else ""
    st.rerun()

n_disp = sum(1 for f in st.session_state.fletes if f["estado"] == "DISPONIBLE")
n_ruta = sum(1 for f in st.session_state.fletes if f["estado"] == "EN RUTA")
n_ofertas = sum(1 for o in st.session_state.ofertas if o["estado"] == "PENDIENTE")

# =====================================================================
# COMERCIANTE
# =====================================================================
if es_comerciante and seccion_key == "Publicar carga":
    st.markdown(
        """
<div class="fr-page-head">
  <h1>Publicar carga</h1>
  <p>Define ruta y precio. Los choferes te contraofertan.</p>
</div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
<div class="fr-stats">
  <div class="fr-stat"><b>{n_disp}</b><span>Abiertas</span></div>
  <div class="fr-stat"><b>{n_ofertas}</b><span>Ofertas</span></div>
  <div class="fr-stat"><b>{n_ruta}</b><span>En ruta</span></div>
</div>
        """,
        unsafe_allow_html=True,
    )
    with st.form("pub_carga", clear_on_submit=True):
        origen = st.text_input("Origen", value="Santa Anita (Lima)")
        destino = st.text_input("Destino", placeholder="Ej: Huancayo")
        desc = st.text_input("Descripción de la carga", placeholder="Ej: 20 Tn fertilizante")
        precio = st.number_input("Tu precio (S/)", min_value=0.0, value=1500.0, step=50.0)
        com = comision_de(precio)
        st.caption(f"Comisión plataforma ({int(COMISION_PCT * 100)}%): S/ {com:.2f}")
        publicar = st.form_submit_button("Publicar flete", type="primary", use_container_width=True)
        if publicar:
            if not destino.strip() or not desc.strip():
                st.error("Completa destino y descripción.")
            else:
                fid = st.session_state.siguiente_id_flete
                st.session_state.siguiente_id_flete += 1
                st.session_state.fletes.append(
                    {
                        "id": fid,
                        "origen": origen.strip(),
                        "destino": destino.strip(),
                        "descripcion": desc.strip(),
                        "precio": float(precio),
                        "estado": "DISPONIBLE",
                        "comerciante": st.session_state.nombre_sesion,
                        "chofer": None,
                        "precio_acordado": None,
                    }
                )
                st.success(f"Carga #{fid} publicada. Ya puede recibir ofertas.")
                st.rerun()

    st.subheader("Tus fletes")
    for f in reversed(st.session_state.fletes):
        st.markdown(
            f"""
<div class="fr-card">
  <p class="fr-card-title">#{f['id']} · {f['origen']} → {f['destino']}</p>
  <p class="fr-muted">{f['descripcion']}</p>
  <p class="fr-price">S/ {f['precio']:.0f}</p>
  {badge_estado(f['estado'])}
</div>
            """,
            unsafe_allow_html=True,
        )

elif es_comerciante and seccion_key == "Ofertas":
    st.markdown(
        """
<div class="fr-page-head">
  <h1>Ofertas</h1>
  <p>Elige la mejor contraoferta y cierra el trato.</p>
</div>
        """,
        unsafe_allow_html=True,
    )
    abiertas = [f for f in st.session_state.fletes if f["estado"] == "DISPONIBLE"]
    if not abiertas:
        st.info("No hay fletes abiertos. Publica una carga primero.")
    else:
        for f in abiertas:
            ofs = [o for o in st.session_state.ofertas if o["flete_id"] == f["id"] and o["estado"] == "PENDIENTE"]
            with st.expander(
                f"#{f['id']}  {f['origen']} → {f['destino']}  ·  S/ {f['precio']:.0f}  ·  {len(ofs)} oferta(s)",
                expanded=bool(ofs),
            ):
                st.write(f"**Carga:** {f['descripcion']}")
                if not ofs:
                    st.caption("Aún no hay contraofertas.")
                for o in ofs:
                    st.markdown(
                        f"""
<div class="fr-card">
  <p class="fr-card-title">{o['chofer_nombre']}</p>
  <p class="fr-muted">DNI {o['dni']} · Placa {o['placa']}</p>
  <p class="fr-price">S/ {o['monto']:.0f}</p>
  <p class="fr-muted">{o.get('nota') or 'Sin nota'}</p>
</div>
                        """,
                        unsafe_allow_html=True,
                    )
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Aceptar", key=f"ok_{o['id']}", type="primary", use_container_width=True):
                            f["estado"] = "EN RUTA"
                            f["chofer"] = o["chofer_nombre"]
                            f["precio_acordado"] = float(o["monto"])
                            o["estado"] = "ACEPTADA"
                            for otras in st.session_state.ofertas:
                                if (
                                    otras["flete_id"] == f["id"]
                                    and otras["id"] != o["id"]
                                    and otras["estado"] == "PENDIENTE"
                                ):
                                    otras["estado"] = "RECHAZADA"
                            st.success(
                                f"Trato cerrado · {o['chofer_nombre']} · "
                                f"S/ {o['monto']:.0f} · comisión S/ {comision_de(o['monto']):.2f}"
                            )
                            st.rerun()
                    with c2:
                        if st.button("Rechazar", key=f"no_{o['id']}", use_container_width=True):
                            o["estado"] = "RECHAZADA"
                            st.rerun()

    cerrados = [f for f in st.session_state.fletes if f["estado"] == "EN RUTA"]
    if cerrados:
        st.subheader("En ruta")
        for f in cerrados:
            precio = f.get("precio_acordado") or f["precio"]
            st.markdown(
                f"""
<div class="fr-card">
  <p class="fr-card-title">#{f['id']} · {f['origen']} → {f['destino']}</p>
  <p class="fr-muted">Chofer: {f.get('chofer') or '—'} · {f['descripcion']}</p>
  <p class="fr-price">S/ {precio:.0f}</p>
  {badge_estado(f['estado'])}
</div>
                """,
                unsafe_allow_html=True,
            )

elif es_comerciante and seccion_key == "Mapa":
    st.markdown('''
<div class="fr-page-head">
  <h1>Mapa</h1>
  <p>Seguimiento de camiones en el corredor.</p>
</div>
        ''', unsafe_allow_html=True)
    camiones = st.session_state.camiones_gps
    sel = st.selectbox("Camión", list(camiones.keys()))
    d = camiones[sel]
    st.markdown(
        f"""
<div class="fr-card">
  <p class="fr-card-title">{sel}</p>
  <p class="fr-muted">Chofer: {d['chofer']} · {d['ruta']}</p>
  <p class="fr-muted">{d['carga']}</p>
</div>
        """,
        unsafe_allow_html=True,
    )
    m = folium.Map(location=[d["lat"], d["lon"]], zoom_start=8)
    folium.Marker(
        [d["lat"], d["lon"]],
        popup=f"{sel} · en camino",
        icon=folium.Icon(color="green", icon="truck", prefix="fa"),
    ).add_to(m)
    folium.Marker(
        list(SANTA_ANITA),
        popup="Mercado Mayorista Santa Anita",
        icon=folium.Icon(color="red", icon="home", prefix="fa"),
    ).add_to(m)
    st_folium(m, width=700, height=400)

elif es_comerciante and seccion_key == "Monitoreo":
    st.markdown('''
<div class="fr-page-head">
  <h1>Monitoreo</h1>
  <p>Alerta si el camión se aleja del corredor.</p>
</div>
        ''', unsafe_allow_html=True)
    lat = st.number_input("Latitud GPS", value=-12.050, format="%.4f")
    lon = st.number_input("Longitud GPS", value=-76.900, format="%.4f")
    dist = abs(lat - SANTA_ANITA[0]) + abs(lon - SANTA_ANITA[1])
    st.write(f"Distancia estimada al destino: **{dist:.4f}**")
    if dist > 0.5:
        st.error("Posible desvío detectado.")
    else:
        st.success("Dentro del corredor esperado.")

elif es_comerciante and seccion_key == "Evidencia":
    st.markdown('''
<div class="fr-page-head">
  <h1>Evidencia</h1>
  <p>Paquete de respaldo ante un incidente.</p>
</div>
        ''', unsafe_allow_html=True)
    datos = {
        "Chofer": "Juan Carlos Pérez Machuca",
        "DNI": "45892174",
        "Licencia": "Q45892174-A3C",
        "Placa": "F3V-894",
        "Carga": "20 Tn Papa Única (valor simulado S/ 40,000)",
        "GPS": "Lat -11.954, Lon -76.321 (San Mateo)",
    }
    st.warning("Modo simulación — no envía a la PNP.")
    if st.button("Generar acta", type="primary", use_container_width=True):
        st.subheader("Acta de evidencia digital")
        st.write(f"**Fecha:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        st.markdown(
            f"""
* **Imputado:** {datos['Chofer']} (DNI {datos['DNI']})
* **Licencia:** {datos['Licencia']}
* **Placa:** **{datos['Placa']}**
* **Carga:** {datos['Carga']}
* **Último GPS:** {datos['GPS']}
"""
        )
        st.session_state.lista_negra["dnis"].add(datos["DNI"])
        st.session_state.lista_negra["placas"].add(datos["Placa"])
        st.success("Acta generada. DNI y placa agregados a lista negra local.")

# =====================================================================
# CHOFER
# =====================================================================
elif (not es_comerciante) and seccion_key == "Mi perfil":
    st.markdown('''
<div class="fr-page-head">
  <h1>Mi perfil</h1>
  <p>Verifica DNI, licencia y placa para ofertar.</p>
</div>
        ''', unsafe_allow_html=True)
    p: dict[str, Any] = st.session_state.perfil_chofer
    st.markdown(badge_estado(p.get("estado_verificacion", "PENDIENTE")), unsafe_allow_html=True)
    with st.form("perfil_chofer"):
        dni = st.text_input("DNI (8 dígitos)", value=p.get("dni", ""), max_chars=8)
        nombre = st.text_input("Nombre completo", value=p.get("nombre", "") or st.session_state.nombre_sesion)
        licencia = st.text_input("Licencia (A3C / carga)", value=p.get("licencia", ""))
        placa = st.text_input("Placa del camión", value=p.get("placa", ""))
        celular = st.text_input("Celular / WhatsApp", value=p.get("celular", ""))
        enviar = st.form_submit_button("Guardar y verificar", type="primary", use_container_width=True)
        if enviar:
            check = verificar_lista_negra(dni, placa)
            if check == "DNI_BLOQUEADO":
                st.error("DNI en lista negra.")
            elif check == "PLACA_BLOQUEADA":
                st.error("Placa en lista negra.")
            elif len(dni) != 8 or not nombre.strip() or not licencia.strip() or not placa.strip():
                st.error("Completa DNI (8), nombre, licencia y placa.")
            else:
                st.session_state.perfil_chofer = {
                    "dni": dni,
                    "nombre": nombre.strip(),
                    "licencia": licencia.strip(),
                    "placa": placa.strip().upper(),
                    "celular": celular.strip(),
                    "estado_verificacion": "APROBADO",
                }
                st.success("Perfil verificado. Ya puedes ofertar.")
                st.rerun()

elif (not es_comerciante) and seccion_key == "Cargas":
    st.markdown('''
<div class="fr-page-head">
  <h1>Cargas</h1>
  <p>Propón tu precio. El comerciante acepta o rechaza.</p>
</div>
        ''', unsafe_allow_html=True)
    st.markdown(f'''
<div class="fr-stats">
  <div class="fr-stat"><b>{n_disp}</b><span>Disponibles</span></div>
  <div class="fr-stat"><b>{n_ofertas}</b><span>Pendientes</span></div>
  <div class="fr-stat"><b>{n_ruta}</b><span>En ruta</span></div>
</div>
        ''', unsafe_allow_html=True)
    perfil = st.session_state.perfil_chofer
    if perfil.get("estado_verificacion") != "APROBADO":
        st.warning("Completa **Mi perfil** antes de ofertar.")
    disponibles = [f for f in st.session_state.fletes if f["estado"] == "DISPONIBLE"]
    if not disponibles:
        st.info("No hay cargas abiertas por ahora.")
    else:
        for f in disponibles:
            st.markdown(
                f"""
<div class="fr-card">
  <p class="fr-card-title">#{f['id']} · {f['origen']} → {f['destino']}</p>
  <p class="fr-muted">{f['descripcion']}</p>
  <p class="fr-price">S/ {f['precio']:.0f}</p>
  <p class="fr-muted">Precio ofrecido por el comerciante</p>
</div>
                """,
                unsafe_allow_html=True,
            )
            mis = [
                o
                for o in st.session_state.ofertas
                if o["flete_id"] == f["id"]
                and o.get("chofer_nombre") == (perfil.get("nombre") or st.session_state.nombre_sesion)
                and o["estado"] == "PENDIENTE"
            ]
            if mis:
                st.caption(f"Tu oferta pendiente: S/ {mis[0]['monto']:.0f}")
            c1, c2 = st.columns([2, 1])
            with c1:
                monto = st.number_input(
                    "Tu contraoferta (S/)",
                    min_value=0.0,
                    value=float(f["precio"]),
                    step=50.0,
                    key=f"monto_{f['id']}",
                )
                nota = st.text_input(
                    "Nota",
                    key=f"nota_{f['id']}",
                    placeholder="Ej: salgo en 1 hora",
                )
            with c2:
                st.write("")
                st.write("")
                if st.button("Enviar oferta", key=f"btn_{f['id']}", type="primary", use_container_width=True):
                    if perfil.get("estado_verificacion") != "APROBADO":
                        st.error("Debes estar verificado.")
                    elif monto <= 0:
                        st.error("Indica un monto.")
                    else:
                        actualizada = False
                        for o in st.session_state.ofertas:
                            if (
                                o["flete_id"] == f["id"]
                                and o.get("chofer_nombre")
                                == (perfil.get("nombre") or st.session_state.nombre_sesion)
                                and o["estado"] == "PENDIENTE"
                            ):
                                o["monto"] = float(monto)
                                o["nota"] = nota.strip()
                                actualizada = True
                                break
                        if not actualizada:
                            oid = st.session_state.siguiente_id_oferta
                            st.session_state.siguiente_id_oferta += 1
                            st.session_state.ofertas.append(
                                {
                                    "id": oid,
                                    "flete_id": f["id"],
                                    "chofer_nombre": perfil.get("nombre") or st.session_state.nombre_sesion,
                                    "dni": perfil.get("dni", ""),
                                    "placa": perfil.get("placa", ""),
                                    "monto": float(monto),
                                    "nota": nota.strip(),
                                    "estado": "PENDIENTE",
                                    "creada": datetime.now().isoformat(timespec="seconds"),
                                }
                            )
                        st.success(f"Oferta enviada: S/ {monto:.0f}")
                        st.rerun()

    historial = [
        o
        for o in st.session_state.ofertas
        if o.get("chofer_nombre") == (perfil.get("nombre") or st.session_state.nombre_sesion)
    ]
    if historial:
        st.subheader("Mis ofertas")
        st.dataframe(pd.DataFrame(historial), use_container_width=True, hide_index=True)

elif (not es_comerciante) and seccion_key == "En ruta":
    st.markdown('''
<div class="fr-page-head">
  <h1>En ruta</h1>
  <p>Tu ubicación hacia Santa Anita.</p>
</div>
        ''', unsafe_allow_html=True)
    lat = st.number_input("Latitud", value=-12.045, format="%.4f", key="ch_lat")
    lon = st.number_input("Longitud", value=-75.500, format="%.4f", key="ch_lon")
    m = folium.Map(location=[lat, lon], zoom_start=8)
    folium.Marker(
        [lat, lon],
        popup="Mi camión",
        icon=folium.Icon(color="blue", icon="truck", prefix="fa"),
    ).add_to(m)
    folium.Marker(list(SANTA_ANITA), popup="Santa Anita", icon=folium.Icon(color="green")).add_to(m)
    st_folium(m, width=700, height=400)

elif (not es_comerciante) and seccion_key == "Validar":
    st.markdown('''
<div class="fr-page-head">
  <h1>Validar</h1>
  <p>Consulta DNI o placa en lista negra.</p>
</div>
        ''', unsafe_allow_html=True)
    with st.form("val_lb"):
        d = st.text_input("DNI", max_chars=8)
        p = st.text_input("Placa")
        if st.form_submit_button("Validar", type="primary", use_container_width=True):
            r = verificar_lista_negra(d, p)
            if r == "DNI_BLOQUEADO":
                st.error("DNI bloqueado.")
            elif r == "PLACA_BLOQUEADA":
                st.error("Placa reportada.")
            else:
                st.success("Sin alertas en lista.")
