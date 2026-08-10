# FleteRetorno — InDrive de camiones (empresa propia)

MVP de arranque **de abajo hacia arriba**: publicar carga → chofer contraoferta → comerciante acepta.

## Cómo empezamos este proyecto (orden real)

| Paso | Qué hacer | Estado |
|------|-----------|--------|
| **0** | Carpeta + venv + deps | ✅ Listo |
| **1** | Demo local con roles | ✅ Listo |
| **2** | Flujo InDrive (oferta / aceptar) | ✅ Listo |
| **3** | Probar tú mismo los 2 logins | 👈 **Hoy** |
| **4** | Hablar con 3 choferes / comerciantes (calle) | Pendiente |
| **5** | Supabase cuando valide uso | Opcional |
| **6** | Play Store / pagos / cripto | Después |

## Arranque en Ubuntu / WSL

```bash
cd /home/dena0/fleteretorno
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Proyecto **aparte** del de papas (`app-negocio`). Repo Git propio en esta carpeta.

Abre el link local (suele ser `http://localhost:8501`).

## Login demo

| Usuario | Clave | Qué hace |
|---------|-------|----------|
| `comerciante` | `santaanita2026` | Publica carga, **acepta ofertas**, mapa, alerta |
| `chofer` | `flete2026` | Verifica perfil, **contraoferta**, mapa |

## Flujo de prueba (5 minutos)

1. Login **comerciante** → Publicar carga (ej. fertilizante a Huancayo, S/ 1500).
2. Cerrar sesión → login **chofer**.
3. **Mi perfil** → DNI (8 dígitos), licencia, placa → guardar (queda APROBADO).
4. **Cargas y contraoferta** → envía precio (ej. S/ 1700).
5. Cerrar sesión → **comerciante** → menú **Ofertas (InDrive)** → **Aceptar**.
6. El flete pasa a **EN RUTA** con precio acordado + comisión 5% demo.

## Supabase (fase 2, no bloquea el arranque)

1. SQL Editor → `supabase/schema.sql`
2. Secrets → ver `.streamlit/secrets.toml.example`

## Qué NO es Fase 1

Escrow real, GPS heartbeat, Ed25519, panel admin país, Play Store.  
Eso viene **después** de que el flujo InDrive y la verificación básica se sientan bien.
