import streamlit as st
import ui
import data_processing 
import pandas as pd

pd.set_option('display.precision', 2)

st.set_page_config(
    page_title="APP de Análise e Fechamento de Preços",
    layout="wide"
)

def main():
    pages = {
        "Importar planilha de preços": ui.page_carrega_dado,
        "Análise de preços": ui.page_analisa,
        # "Gerar preço de referência": ui.page_exporta
    }

    if "page" not in st.session_state:
        st.session_state.update({"page": "Importar planilha de preços"})

    if "Dados" not in st.session_state:
        st.session_state.update(
            {
                "Dados": None, 
                "Aprove_items": {}, 
                "Remove_items": {}, 
                "Aprove_ids": {}, 
                "Remove_ids": {}, 
                "estatisticas_default" : [
                    'Média geral', 
                    'Preço de Referência Atual', 
                    'Preço de Referência Anterior', 
                    '3º quartil', 
                    'Status C.V'
                ]
            }
        )

    with st.sidebar:
        st.title("FGV IBRE - SPDO")
        page = st.radio("Menu", tuple(pages.keys()))
        st.markdown('---')

    pages[page]()

if __name__ == "__main__":
    main()

