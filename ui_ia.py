# ui_ia.py
import streamlit as st
from logic_ia import obtener_respuesta_ia

def render_tab_ia():
    # 1. INICIALIZACIÓN DE ESTADOS
    if "conversaciones" not in st.session_state:
        st.session_state.conversaciones = {"Chat Principal": []}
    if "chat_actual" not in st.session_state:
        st.session_state.chat_actual = "Chat Principal"

    # --- BARRA LATERAL: GESTIÓN DE CHATS ---
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 💬 Gestión de Conversaciones")
        
        # --- BOTONES DE ACCIÓN ---
        col_new, col_del = st.columns(2)
        with col_new:
            if st.button("➕ Nuevo", use_container_width=True, key="ia_new_chat"):
                base_name = f"Chat {len(st.session_state.conversaciones) + 1}"
                nuevo_nombre = base_name
                contador = 1
                while nuevo_nombre in st.session_state.conversaciones:
                    nuevo_nombre = f"{base_name} ({contador})"
                    contador += 1
                st.session_state.conversaciones[nuevo_nombre] = []
                st.session_state.chat_actual = nuevo_nombre
                st.rerun()

        with col_del:
            if st.button("🗑️ Borrar", use_container_width=True, key="ia_del_chat"):
                if len(st.session_state.conversaciones) > 1:
                    del st.session_state.conversaciones[st.session_state.chat_actual]
                    nuevo_foco = list(st.session_state.conversaciones.keys())[0]
                    st.session_state.chat_actual = nuevo_foco
                    st.rerun()
                else:
                    st.error("No podés borrar el único chat.")

        # --- RENOMBRAR ---
        with st.expander("✏️ Renombrar Chat"):
            nuevo_nombre_input = st.text_input(
                "Nuevo nombre:", 
                value=st.session_state.chat_actual, 
                key="ia_rename_input"
            )
            if st.button("💾 Guardar Nombre", use_container_width=True, key="ia_save_name"):
                if nuevo_nombre_input and nuevo_nombre_input != st.session_state.chat_actual:
                    if nuevo_nombre_input not in st.session_state.conversaciones:
                        # Reemplazamos la llave en el diccionario
                        historial = st.session_state.conversaciones.pop(st.session_state.chat_actual)
                        st.session_state.conversaciones[nuevo_nombre_input] = historial
                        st.session_state.chat_actual = nuevo_nombre_input
                        st.rerun()
                    else:
                        st.error("Ese nombre ya existe.")

        st.divider()

        # --- SELECTOR DE CHAT ---
        nombres_chats = list(st.session_state.conversaciones.keys())
        try:
            indice_actual = nombres_chats.index(st.session_state.chat_actual)
        except ValueError:
            indice_actual = 0

        seleccion = st.radio(
            "📂 Seleccioná un chat:",
            options=nombres_chats,
            index=indice_actual,
            key="ia_chat_selector"
        )
        
        if seleccion != st.session_state.chat_actual:
            st.session_state.chat_actual = seleccion
            st.rerun()

    # --- ÁREA PRINCIPAL ---
    st.markdown(f'<p class="section-header">🗨️ {st.session_state.chat_actual}</p>',
                unsafe_allow_html=True)
    
    # INPUT ARRIBA (antes del historial)
    prompt = st.chat_input("Escribí tu consulta sobre el mercado o tus activos...")
    
    # HISTORIAL EN CONTENEDOR
    chat_activo = st.session_state.conversaciones[st.session_state.chat_actual]
    contenedor_mensajes = st.container(height=450, border=True)
    
    with contenedor_mensajes:
        for mensaje in chat_activo:
            with st.chat_message(mensaje["role"]):
                st.markdown(mensaje["content"])

    # PROCESAR INPUT
    if prompt:
        chat_activo.append({"role": "user", "content": prompt})
        with contenedor_mensajes:
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("🤔 Analizando..."):
                    portfolio_actual = st.session_state.mi_portfolio if "mi_portfolio" in st.session_state else None
                    respuesta = obtener_respuesta_ia(
                        pregunta_usuario=prompt, 
                        portfolio_df=portfolio_actual,
                        historial_previo=chat_activo[:-1] 
                    )
                    st.markdown(respuesta)
            
        chat_activo.append({"role": "assistant", "content": respuesta})
        st.rerun()