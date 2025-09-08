# ===================== FILA DO DIA =====================
hoje = datetime.datetime.now().date()

if not df_fila.empty:
    df_fila["Data"] = pd.to_datetime(df_fila["Data"], errors="coerce").dt.date
    fila_hoje = df_fila[
        (df_fila["Data"] == hoje) & (df_fila["Status"] == "Agendado")
    ]

    if not fila_hoje.empty:
        st.sidebar.subheader("👥 Agendados Hoje")
        for _, row in fila_hoje.iterrows():
            paciente_id = row["Paciente_ID"]
            paciente_info = df_pacientes[df_pacientes["ID"] == paciente_id]

            if not paciente_info.empty:
                nome = paciente_info.iloc[0]["Nome"]
            else:
                nome = f"ID {paciente_id}"

            # Links para páginas específicas com query param idpaciente
            ficha_url = f"/ficha_clinica?idpaciente={paciente_id}"
            evolucao_url = f"/evolucao_tratamento?idpaciente={paciente_id}"

            st.sidebar.markdown(
                f"- {nome} "
                f"[📋]({ficha_url}) "
                f"[🦷]({evolucao_url})",
                unsafe_allow_html=True
            )
    else:
        st.sidebar.info("Nenhum paciente agendado para hoje.")
else:
    st.sidebar.warning("A aba 'Fila' está vazia ou não existe.")
