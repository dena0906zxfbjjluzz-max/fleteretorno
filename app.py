"""
InDrive para camiones de carga mayorista — MVP de arranque (Streamlit).
Empresa propia, de abajo hacia arriba: publicar → ofertar → aceptar.
Supabase opcional; sin secrets = demo local.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

# Comisión de la plataforma (demo) — modelo negocio InDrive de fletes
COMISION_PCT = 0.05

st.set_page_config(
    page_title="FleteRetorno",
    page_icon="🚛",
    layout="centered",
    initial_sidebar_state="expanded",
)

# --- Cuentas demo (producción: Supabase Auth / secrets) ---
USUARIOS = {
    "comerciante": {"clave": "santaanita2026", "rol": "comerciante", "nombre": "Comerciante Demo"},
    "chofer": {"clave": "flete2026", "rol": "chofer", "nombre": "Chofer Demo"},
}

DNI_BANEADOS = {"45892174", "10234567"}
PLACAS_BANEADAS = {"F3V-894", "A1B-123"}
SANTA_ANITA = (-12.045, -76.953)


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
    """Estado local de la empresa (sesión). Fase 1: sin nube."""
    if "fletes" not in st.session_state:
        st.session_state.fletes = [
            {
                "id": 1,
                "origen": "Santa Anita (Lima)",
                "destino": "Huancayo",
                "descripcion": "20 Tn fertilizante",
                "precio": 1500.0,
                "estado": "DISPONIBLE",
                "comerciante": "Comerciante Demo",
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
                "comerciante": "Comerciante Demo",
                "chofer": None,
                "precio_acordado": None,
            },
        ]
    if "siguiente_id_flete" not in st.session_state:
        st.session_state.siguiente_id_flete = 3
    if "ofertas" not in st.session_state:
        # Ofertas tipo InDrive: chofer puja, comerciante acepta
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
    st.title("🚛 FleteRetorno")
    st.subheader("InDrive de camiones · flete de retorno")
    st.caption(
        "Tu empresa · de abajo hacia arriba · "
        "comerciante publica · chofer contraoferta · se cierra el trato"
    )
    st.info(
        "**Problema:** el camión regresa vacío y quema plata.  \n"
        "**Solución:** conectar chofer en Santa Anita con carga de regreso a provincia."
    )
    st.divider()
    with st.form("login"):
        u = st.text_input("Usuario")
        c = st.text_input("Contraseña", type="password")
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
    with st.expander("Cuentas de demostración (arranque local)"):
        st.code("comerciante / santaanita2026\nchofer / flete2026", language=None)
        st.caption("1) Entra como comerciante y publica. 2) Entra como chofer, verifica perfil y oferte.")
    st.stop()

init_demo_store()

# ---------- SHELL ----------
st.sidebar.title("FleteRetorno")
st.sidebar.caption(f"**{st.session_state.nombre_sesion}** · `{st.session_state.rol}`")
st.sidebar.caption(f"Comisión plataforma (demo): **{int(COMISION_PCT * 100)}%**")
if en_nube():
    st.sidebar.success("🟢 Nube (Supabase)")
else:
    st.sidebar.warning("🟡 Demo local · Fase 1")

if st.session_state.rol == "comerciante":
    seccion = st.sidebar.radio(
        "Menú",
        [
            "📝 Publicar carga",
            "💬 Ofertas (InDrive)",
            "🗺️ Mapa de camiones",
            "🚨 Monitoreo desvío",
            "📄 Acta / denuncia demo",
        ],
    )
else:
    seccion = st.sidebar.radio(
        "Menú",
        [
            "🆔 Mi perfil (seguridad)",
            "🚚 Cargas y contraoferta",
            "🗺️ Mapa en ruta",
            "🔒 Validar DNI/placa",
        ],
    )

if st.sidebar.button("Cerrar sesión", use_container_width=True):
    for k in ("autenticado", "usuario", "rol", "nombre_sesion"):
        st.session_state[k] = False if k == "autenticado" else ""
    st.rerun()

st.title("🚛 FleteRetorno")
st.caption("Empieza chico: 1 corredor · publicar · ofertar · aceptar")

# =====================================================================
# COMERCIANTE
# =====================================================================
if st.session_state.rol == "comerciante" and seccion == "📝 Publicar carga":
    st.header("Publicar carga")
    st.caption("Como InDrive: usted pone precio. Los choferes ven y contraofertan.")
    with st.form("pub_carga", clear_on_submit=True):
        origen = st.text_input("Origen", value="Santa Anita (Lima)")
        destino = st.text_input("Destino", placeholder="Ej: Huancayo")
        desc = st.text_input("Carga", placeholder="Ej: 20 Tn fertilizante")
        precio = st.number_input("Flete que ofrece (S/)", min_value=0.0, value=1500.0, step=50.0)
        com = comision_de(precio)
        st.caption(f"Comisión demo plataforma ({int(COMISION_PCT*100)}%): S/ {com:.2f}")
        publicar = st.form_submit_button("Publicar flete", type="primary")
        if publicar:
            if not destino.strip() or not desc.strip():
                st.error("Complete destino y descripción.")
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
                st.success(f"Carga #{fid} en el mercado. Choferes verificados ya pueden contraofertar.")
                st.rerun()

    st.subheader("Todos los fletes (demo)")
    st.dataframe(pd.DataFrame(st.session_state.fletes), use_container_width=True, hide_index=True)

elif st.session_state.rol == "comerciante" and seccion == "💬 Ofertas (InDrive)":
    st.header("Ofertas de choferes")
    st.caption("Usted elige la mejor contrapropuesta. Así se cierra el trato.")
    abiertas = [f for f in st.session_state.fletes if f["estado"] == "DISPONIBLE"]
    if not abiertas:
        st.info("No hay fletes abiertos. Publique una carga primero.")
    else:
        for f in abiertas:
            ofs = [o for o in st.session_state.ofertas if o["flete_id"] == f["id"] and o["estado"] == "PENDIENTE"]
            with st.expander(
                f"#{f['id']} {f['origen']} → {f['destino']} · pide S/ {f['precio']:.0f} · "
                f"{len(ofs)} oferta(s)",
                expanded=bool(ofs),
            ):
                st.write(f"**Carga:** {f['descripcion']}")
                if not ofs:
                    st.caption("Aún no hay contraofertas. Entre como chofer y oferte.")
                for o in ofs:
                    c1, c2, c3 = st.columns([2, 1, 1])
                    with c1:
                        st.write(
                            f"**{o['chofer_nombre']}** · DNI {o['dni']} · "
                            f"placa `{o['placa']}` · **S/ {o['monto']:.0f}**"
                        )
                        st.caption(o.get("nota") or "Sin nota")
                    with c2:
                        if st.button("Aceptar", key=f"ok_{o['id']}", type="primary"):
                            f["estado"] = "EN RUTA"
                            f["chofer"] = o["chofer_nombre"]
                            f["precio_acordado"] = float(o["monto"])
                            o["estado"] = "ACEPTADA"
                            for otras in st.session_state.ofertas:
                                if otras["flete_id"] == f["id"] and otras["id"] != o["id"] and otras["estado"] == "PENDIENTE":
                                    otras["estado"] = "RECHAZADA"
                            st.success(
                                f"Trato cerrado #{f['id']}: {o['chofer_nombre']} · "
                                f"S/ {o['monto']:.0f} · comisión demo S/ {comision_de(o['monto']):.2f}"
                            )
                            st.rerun()
                    with c3:
                        if st.button("Rechazar", key=f"no_{o['id']}"):
                            o["estado"] = "RECHAZADA"
                            st.rerun()

    cerrados = [f for f in st.session_state.fletes if f["estado"] == "EN RUTA"]
    if cerrados:
        st.subheader("En ruta (aceptados)")
        st.dataframe(pd.DataFrame(cerrados), use_container_width=True, hide_index=True)

elif st.session_state.rol == "comerciante" and seccion == "🗺️ Mapa de camiones":
    st.header("Rastreo ligero (demo GPS)")
    camiones = st.session_state.camiones_gps
    sel = st.selectbox("Camión", list(camiones.keys()))
    d = camiones[sel]
    st.write(f"**Chofer:** {d['chofer']} · **Ruta:** {d['ruta']}")
    st.info(f"📦 {d['carga']}")
    m = folium.Map(location=[d["lat"], d["lon"]], zoom_start=8)
    folium.Marker(
        [d["lat"], d["lon"]],
        popup=f"{sel} · en camino",
        icon=folium.Icon(color="red", icon="truck", prefix="fa"),
    ).add_to(m)
    folium.Marker(
        list(SANTA_ANITA),
        popup="Mercado Mayorista Santa Anita",
        icon=folium.Icon(color="green", icon="home", prefix="fa"),
    ).add_to(m)
    st_folium(m, width=700, height=400)

elif st.session_state.rol == "comerciante" and seccion == "🚨 Monitoreo desvío":
    st.header("Centro de desvío (demo)")
    st.caption("Simulación: si se aleja de Santa Anita → alerta.")
    lat = st.number_input("Latitud GPS", value=-12.050, format="%.4f")
    lon = st.number_input("Longitud GPS", value=-76.900, format="%.4f")
    dist = abs(lat - SANTA_ANITA[0]) + abs(lon - SANTA_ANITA[1])
    st.write(f"Distancia estimada al destino: **{dist:.4f}**")
    if dist > 0.5:
        st.error("🚨 ALERTA: posible desvío (flujo demo).")
    else:
        st.success("🟢 Proximidad razonable al corredor.")

elif st.session_state.rol == "comerciante" and seccion == "📄 Acta / denuncia demo":
    st.header("Paquete de evidencia (demo)")
    datos = {
        "Chofer": "Juan Carlos Pérez Machuca",
        "DNI": "45892174",
        "Licencia": "Q45892174-A3C",
        "Placa": "F3V-894",
        "Carga": "20 Tn Papa Única (valor simulado S/ 40,000)",
        "GPS": "Lat -11.954, Lon -76.321 (San Mateo)",
    }
    st.warning("Solo demostración — no envía a la PNP.")
    if st.button("Generar acta de denuncia (demo)", type="primary"):
        st.subheader("ACTA DE EVIDENCIA DIGITAL")
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
        st.success("Acta demo + DNI/placa a lista negra local.")

# =====================================================================
# CHOFER
# =====================================================================
elif st.session_state.rol == "chofer" and seccion == "🆔 Mi perfil (seguridad)":
    st.header("Verificación de transportista (Fase 1)")
    st.caption("Sin esto no se ve como empresa seria. Mínimo: DNI + licencia + placa.")
    p: dict[str, Any] = st.session_state.perfil_chofer
    st.info(f"Estado: **{p.get('estado_verificacion', 'PENDIENTE')}**")
    with st.form("perfil_chofer"):
        dni = st.text_input("DNI (8 dígitos)", value=p.get("dni", ""), max_chars=8)
        nombre = st.text_input("Nombre completo", value=p.get("nombre", "") or st.session_state.nombre_sesion)
        licencia = st.text_input("Licencia (A3C / especial carga)", value=p.get("licencia", ""))
        placa = st.text_input("Placa camión", value=p.get("placa", ""))
        celular = st.text_input("Celular / WhatsApp", value=p.get("celular", ""))
        enviar = st.form_submit_button("Enviar para validación", type="primary")
        if enviar:
            check = verificar_lista_negra(dni, placa)
            if check == "DNI_BLOQUEADO":
                st.error("🚨 DNI en lista negra.")
            elif check == "PLACA_BLOQUEADA":
                st.error("🚨 Placa en lista negra.")
            elif len(dni) != 8 or not nombre.strip() or not licencia.strip() or not placa.strip():
                st.error("Complete DNI (8), nombre, licencia y placa.")
            else:
                st.session_state.perfil_chofer = {
                    "dni": dni,
                    "nombre": nombre.strip(),
                    "licencia": licencia.strip(),
                    "placa": placa.strip().upper(),
                    "celular": celular.strip(),
                    "estado_verificacion": "APROBADO",
                }
                st.success("Perfil APROBADO (demo). En prod: revisión admin.")
                st.rerun()

elif st.session_state.rol == "chofer" and seccion == "🚚 Cargas y contraoferta":
    st.header("Cargas · contraoferta tipo InDrive")
    perfil = st.session_state.perfil_chofer
    if perfil.get("estado_verificacion") != "APROBADO":
        st.warning("Primero complete **Mi perfil** y quede APROBADO.")
    disponibles = [f for f in st.session_state.fletes if f["estado"] == "DISPONIBLE"]
    if not disponibles:
        st.info("No hay cargas abiertas. Como comerciante publique una.")
    else:
        for f in disponibles:
            with st.container(border=True):
                st.markdown(
                    f"**#{f['id']}** {f['origen']} → **{f['destino']}**  \n"
                    f"{f['descripcion']}  \n"
                    f"Ofrece el comerciante: **S/ {f['precio']:.0f}**"
                )
                mis = [
                    o
                    for o in st.session_state.ofertas
                    if o["flete_id"] == f["id"]
                    and o.get("chofer_nombre") == (perfil.get("nombre") or st.session_state.nombre_sesion)
                    and o["estado"] == "PENDIENTE"
                ]
                if mis:
                    st.caption(f"Su oferta pendiente: S/ {mis[0]['monto']:.0f}")
                c1, c2 = st.columns([2, 1])
                with c1:
                    monto = st.number_input(
                        "Su precio (S/)",
                        min_value=0.0,
                        value=float(f["precio"]),
                        step=50.0,
                        key=f"monto_{f['id']}",
                    )
                    nota = st.text_input(
                        "Nota (ej. salgo en 1 hora)",
                        key=f"nota_{f['id']}",
                        placeholder="Opcional",
                    )
                with c2:
                    st.write("")
                    st.write("")
                    if st.button("Enviar oferta", key=f"btn_{f['id']}", type="primary"):
                        if perfil.get("estado_verificacion") != "APROBADO":
                            st.error("Debe estar verificado.")
                        elif monto <= 0:
                            st.error("Indique un monto.")
                        else:
                            # Una oferta pendiente por chofer/flete: actualiza
                            actualizada = False
                            for o in st.session_state.ofertas:
                                if (
                                    o["flete_id"] == f["id"]
                                    and o.get("chofer_nombre") == (perfil.get("nombre") or st.session_state.nombre_sesion)
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
                            st.success(f"Oferta enviada: S/ {monto:.0f}. Espere que el comerciante acepte.")
                            st.rerun()

    historial = [
        o
        for o in st.session_state.ofertas
        if o.get("chofer_nombre") == (perfil.get("nombre") or st.session_state.nombre_sesion)
    ]
    if historial:
        st.subheader("Mis ofertas")
        st.dataframe(pd.DataFrame(historial), use_container_width=True, hide_index=True)

elif st.session_state.rol == "chofer" and seccion == "🗺️ Mapa en ruta":
    st.header("Mi ubicación (demo)")
    lat = st.number_input("Mi lat", value=-12.045, format="%.4f", key="ch_lat")
    lon = st.number_input("Mi lon", value=-75.500, format="%.4f", key="ch_lon")
    m = folium.Map(location=[lat, lon], zoom_start=8)
    folium.Marker([lat, lon], popup="Mi camión", icon=folium.Icon(color="blue", icon="truck", prefix="fa")).add_to(m)
    folium.Marker(list(SANTA_ANITA), popup="Santa Anita", icon=folium.Icon(color="green")).add_to(m)
    st_folium(m, width=700, height=400)

elif st.session_state.rol == "chofer" and seccion == "🔒 Validar DNI/placa":
    st.header("Lista negra (demo)")
    with st.form("val_lb"):
        d = st.text_input("DNI", max_chars=8)
        p = st.text_input("Placa")
        if st.form_submit_button("Validar"):
            r = verificar_lista_negra(d, p)
            if r == "DNI_BLOQUEADO":
                st.error("🚨 DNI bloqueado.")
            elif r == "PLACA_BLOQUEADA":
                st.error("🚨 Placa reportada.")
            else:
                st.success("🟢 Limpio en lista demo.")
