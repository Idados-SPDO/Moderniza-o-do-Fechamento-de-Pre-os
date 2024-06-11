
import streamlit as st

import pandas as pd
 
# Carregando a tabela existente

df = pd.read_csv("sua_tabela.csv")
 
# Adicionando uma nova chave ao session_state para armazenar as linhas selecionadas e excluídas

if 'selected_rows' not in st.session_state:

    st.session_state.selected_rows = pd.DataFrame(columns=df.columns)

if 'excluded_rows' not in st.session_state:

    st.session_state.excluded_rows = df.copy()
 
# Modificando o loop para adicionar checkboxes para cada linha

for index, row in df.iterrows():

    selected = index in st.session_state.selected_rows.index

    if selected:

        selected_index = st.checkbox(f'Index: {index}', key=f'row_selector_{index}', value=True)

    else:

        selected_index = st.checkbox(f'Index: {index}', key=f'row_selector_{index}', value=False)

    # Verificando se o estado do checkbox foi alterado

    if selected_index != selected:

        if selected_index:  # Se o checkbox foi marcado

            st.session_state.selected_rows = st.session_state.selected_rows.append(row)

            st.session_state.excluded_rows = st.session_state.excluded_rows.drop(index, axis=0)

        else:  # Se o checkbox foi desmarcado

            st.session_state.selected_rows = st.session_state.selected_rows.drop(index, axis=0)

            st.session_state.excluded_rows = st.session_state.excluded_rows.append(row)
 
# Renderizando as novas tabelas com as linhas selecionadas e excluídas

st.write('Selected Rows:')

st.write(st.session_state.selected_rows)
 
st.write('Excluded Rows:')

st.write(st.session_state.excluded_rows)