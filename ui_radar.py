# ui_radar.py
import streamlit as st
import pandas as pd
import time  # <--- Corregido: Evita el NameError detectado
from logic_data import fetch_rsi_batch, fetch_fundamental_data
from sp500_data import get_sp500_tickers 

def render_tab_radar():
    st.header("🎯 Radar de Oportunidades (S&P 500)")
    st.markdown("Busca empresas de **alta calidad** en el **S&P 500** que estén en zona de compra técnica.")

    # Obtenemos la lista completa de tickers del S&P 500
    SP500_TICKERS = get_sp500_tickers()

    # --- CONTROLES DE FILTRADO ---
    st.subheader("⚙️ Ajustar Filtros")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        rsi_m = st.slider("📉 RSI Máximo", 20, 80, 35)
        st.caption("**Filtro Técnico:** Busca activos en corrección o sobreventa.")
    with col2:
        roe_m = st.slider("📈 ROE Mínimo %", 0, 50, 15)
        st.caption("**Calidad:** Eficiencia en generación de ganancias.")
    with col3:
        pe_m = st.slider("⚖️ P/E Máximo", 5, 80, 25)
        st.caption("**Valuación:** Relación precio/ganancia actual.")
    with col4:
        fpe_m = st.slider("🔮 Fwd P/E Máx", 5, 80, 20)
        st.caption("**Futuro:** Valuación basada en proyecciones.")

    st.divider()

    if st.button("🚀 Iniciar Escaneo del S&P 500", use_container_width=True):
        st.info(f"🔍 PASO 1: Escaneando precios y RSI de {len(SP500_TICKERS)} empresas...")
        
        # 1. Filtro Técnico (RSI) - Ejecución en lote
        rsi_data = fetch_rsi_batch(SP500_TICKERS)
        
        if not rsi_data:
            st.error("Error al conectar con el servidor de datos. Reintentá.")
            return

        # Filtramos primero por RSI para reducir la carga de balance posterior
        sobrevendidas = [t for t, rsi in rsi_data.items() if rsi <= rsi_m]
        
        if not sobrevendidas:
            st.warning(f"Ninguna empresa con RSI menor a {rsi_m}. El mercado está extendido.")
            return
            
        st.success(f"✅ {len(sobrevendidas)} candidatas técnicas encontradas.")

        # 2. Filtro Fundamental - Priorizando Yahoo Finance
        st.info(f"🧪 PASO 2: Analizando balances de las {len(sobrevendidas)} candidatas...")
        resultados = []
        prog = st.progress(0)
        
        def to_num(v):
            try: return float(v)
            except: return None

        for i, t in enumerate(sobrevendidas):
            # Pausa de seguridad para evitar bloqueos de IP
            time.sleep(0.5) 
            d = fetch_fundamental_data(t)
            
            if d:
                roe = to_num(d.get("roe"))
                pe = to_num(d.get("pe"))
                fpe = to_num(d.get("fwd_pe"))

                # --- LÓGICA DE FILTROS FLEXIBLES ---
                # Si el usuario pone el slider en el extremo (0 o 80), 
                # permitimos que el activo pase aunque el dato sea "N/A".
                
                ok_roe = (roe_m == 0) or (roe is not None and roe >= roe_m)
                ok_pe = (pe_m == 80) or (pe is not None and pe <= pe_m)
                ok_fpe = (fpe_m == 80) or (fpe is not None and fpe <= fpe_m)
                
                if ok_roe and ok_pe and ok_fpe:
                    resultados.append({
                        "Ticker": t,
                        "Nombre": d.get("nombre", t),
                        "RSI": round(rsi_data[t], 2),
                        "ROE %": f"{roe:.2f}%" if roe is not None else "N/A",
                        "P/E": f"{pe:.2f}x" if pe is not None else "N/A",
                        "Fwd P/E": f"{fpe:.2f}x" if fpe is not None else "N/A",
                        "Precio": f"USD {d.get('precio', 0):.2f}"
                    })
            
            prog.progress((i + 1) / len(sobrevendidas))

        if resultados:
            st.balloons()
            st.subheader(f"🏆 Oportunidades Encontradas ({len(resultados)})")
            # Mostramos los resultados en una tabla interactiva
            st.dataframe(
                pd.DataFrame(resultados), 
                use_container_width=True, 
                hide_index=True
            )
        else:
            st.warning("Las candidatas técnicas no superaron tus filtros de calidad. Probá flexibilizar el ROE o el P/E.")