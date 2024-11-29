import streamlit as st
import ui
import data_processing 
import pandas as pd

# Define que, por padrão serão exibidos números decimais com 2 casas decimais.
pd.set_option('display.precision', 2)

# Define o tipo de tela utilizado na aplicação.
st.set_page_config(
    page_title="APP de Análise e Fechamento de Preços",
    layout="wide"
)

def main():

    # Lista contendo as páginas da aplicação.
    pages = {
        "Importar planilha de preços": ui.page_carrega_dado,
        "Visão geral": ui.page_visao_geral,
        "Análise de preços": ui.page_analisa
    }

    # Condicionais de preenchimento de dados no session_state (memória temporária).
    if "page" not in st.session_state:
        st.session_state.update({"page": "Importar planilha de preços"})

    if "Dados" not in st.session_state:
        st.session_state.update(
            {
                "Dados": None,
                "Dados_analise": None,
                "Download": None,

                "desc": None,
                 

                "Items" : [],
                "ALIVAR_items" : [],
                "ALIATA_items" : [],

                "ALIVAR_aprove_items": [], 
                "ALIATA_aprove_items": [],

                "ALIVAR_remove_items": [],
                "ALIATA_remove_items": [],

                "ALIVAR_aprove_ids": {},
                "ALIATA_aprove_ids": {}, 

                "ALIVAR_remove_ids": {}, 
                "ALIATA_remove_ids": {},

                "estatisticas_default" : [
                    'Média (Aprovados e Não Aprovados)', 
                    'Média', 
                    'Preço de Referência Anterior', 
                    'Média 1º quartil', 
                    'Status C.V'

                ],
                "Itens_media": [
                    "304885 - LEITE EM PÓ, DESNATADO",
                    "304886 - LEITE EM PÓ, INTEGRAL",
                    "304887 - LEITE INTEGRAL, UAT (UHT)",
                    "304888 - LEITE DE VACA, SEM LACTOSE, PÓ",
                    "304889 - QUEIJO PROCESSADO, UHT",
                    "304890 - FORMULA INFANTIL, SEM LACTOSE",
                    "304891 - FORMULA INFANTIL, AR",
                    "304892 - FORMULA INFANTIL, ISENTA DE FENILALANINA",
                    "304893 - ALIMENTO DIETÉTICO, SOJA",
                    "304894 - FORMULA INFANTIL, SOJA, DE SEGMENTO",
                    "304895 - FORMULA INFANTIL, SEMI ELEMENTAR HIDROLISADA",
                    "304896 - FORMULA INFANTIL, ELEMENTAR",
                    "304897 - FORMULA INFANTIL, EXTENSAMENTE HIDROLISADA",
                    "304898 - FORMULA INFANTIL,  DE SEGMENTO",
                    "304899 - ALIMENTO DIETÉTICO A BASE DE ARROZ, EM PÓ",
                    "304900 - FORMULA INFANTIL, ELEMENTAR",
                    "304901 - ALIMENTO DIETÉTICO, SOJA",
                    "304902 - FORMULA INFANTIL, PTN, LÁCTEA",
                    "304903 - COMPLEMENTO ALIMENTAR, EM PÓ",
                    "304904 - COMPLEMENTO ALIMENTAR, PÓ",
                    "304905 - ADOÇANTE DIETÉTICO LÍQUIDO",
                    "304906 - MANTEIGA",
                    "304908 - IOGURTE NATURAL",
                    "304909 - IOGURTE, POLPA DE FRUTAS",
                    "304910 - IOGURTE, POLPA DE FRUTAS",
                    "304911 - IOGURTE DESNATADO, SEM LACTOSE",
                    "307378 - LEITE DESNATADO, UAT (UHT)"
                ]

            }
        )

    # Criação de uma sidebar contendo as páginas que podem ser acessadas na aplicação.
    with st.sidebar:
        st.title("FGV IBRE - SPDO")
        page = st.radio("Menu", tuple(pages.keys()))
        st.markdown('---')

    pages[page]()

if __name__ == "__main__":
    main()

