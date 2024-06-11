from itertools import count
import streamlit as st
import pandas as pd
import numpy as np
from numpy.core.fromnumeric import mean
from numpy.lib.function_base import median
from numpy.ma.core import empty
from io import BytesIO
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode
import plotly.express as px

def load_data(content_file=None):
    if content_file is not None:
        content = pd.read_excel(content_file)
        content["Situacao"] = 1
        content = content.astype({
            "Cód. Item Elementar": "object",
            "Desc. Item Elementar": "object",
            "Insinf/Cd Bases": "object",
            "Desc. Insinf": "object",
            "Sinônimo": "object",
            "Marca": "object",
            "Emb/Qtd": "object",
            "Status Insinf": "object",
            "Cód Inf": "object",
            "Desc. Inf": "object",
            "Status Inf": "object",
            "Period": "object",
            "Preço Atual": "float64",
            "Fator": "object",
            "Operador": "object",
            "Data Atual": "datetime64[ns]",
            "Preço Anterior": "float64",
            "Preço Ref Anterior": "float64",
            "Data Anterior": "datetime64[ns]",
            "Tipo Preço": "object",
            "Região do preço": "object",
            "Reg. Ret.": "object"
        })
        content["Produto"] = content["Cód. Item Elementar"].astype(str) + " - " + content["Desc. Item Elementar"]
        content["Preço Atual"] = content["Preço Atual"].round(decimals=2)
        content["Preço Anterior"] = content["Preço Anterior"].round(decimals=2)
        content["Id_produto"] = range(0, content.shape[0])
        content["Outlier"] = content.groupby("Desc. Item Elementar")["Preço Atual"].transform(detecta_outlier)
        content["Variação analise"] = (content["Preço Atual"] - content["Preço Anterior"]) / content["Preço Anterior"]
        content["Variação"] = content["Variação analise"].apply(formatar_como_porcentagem)
        content.set_index("Id_produto")
        
        return content
    
def formatar_como_porcentagem(x):
    return "{:.2%}".format(x)

def baixar_resultados(df, arquivo):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=arquivo)
    buffer.seek(0)  # Volte ao início do buffer
    return st.download_button(label="Baixar", data=buffer, file_name=f"{arquivo}.xlsx")

def detecta_outlier(x):
    limite_inf = lim_inf(x)
    limite_sup = lim_sup(x)
    outlier = ["*" if valor < limite_inf or valor > limite_sup else "" for valor in x]
    return outlier

def q_25(x):
    return x.quantile(0.25)

def q_75(x):
    return x.quantile(0.75)

def cv(x):
    if len(x.tolist()) > 2:
        return (np.std(x) / np.mean(x)) * 100
    else:
        return None

def lim_inf(x):
    return q_25(x) - 1.5 * (q_75(x) - q_25(x))

def lim_sup(x):
    return q_25(x) + 1.5 * (q_75(x) - q_25(x))

def aproveitamento(x):
    return np.mean(x) * 100

def unique_values(x):
    return pd.unique(x)[0]

def cv_status(x):
    if x is not None:
        if x <= 5: status = "Ótimo"
        elif x > 5 and x <= 15: status = "Bom"
        elif x > 15 and x <= 30: status = "Razoável"
        elif x > 30 and x <= 50: status = "Pouco preciso"
        else: status = "Impreciso"
    else:
        status = "-"
    return status    

def amplitude(x):
    return max(x) - min(x)

def estatisticas_produtos(dados:pd.DataFrame):

    dados = dados.groupby("Produto").agg(
        Media_geral = ("Preço Atual", mean),
        Unidade_FGV = ("Emb/Qtd", unique_values),
        UF_Regiao = ("Região do preço", unique_values),
        C_V = ("Preço Atual", cv),
        D_P = ("Preço Atual", np.std),
        Min = ("Preço Atual", min),
        Max = ("Preço Atual", max),
        Amplitude = ("Preço Atual", amplitude),
        Quartil_1 = ("Preço Atual", q_25),
        Quartil_2 = ("Preço Atual", "median"),
        Quartil_3 = ("Preço Atual", q_75),
        Lim_inf = ("Preço Atual", lim_inf),
        Lim_sup = ("Preço Atual", lim_sup),
        Preco_ant = ("Preço Ref Anterior", unique_values),
        Cotacoes_realizadas = ("Preço Atual", np.size)
    )

    dados["Variacao_preco_atual_ant"] = 100*(dados["Media_geral"] - dados["Preco_ant"]) / dados["Preco_ant"]


    return dados

def agg_table(dados:pd.DataFrame, ids:list, aprove=True, key: str=None):

    nova_ordem = [
            "Cód Inf",
            "Produto",
            "Insinf/Cd Bases",
            "Desc. Insinf",
            "Data Atual",
            "Preço Atual",
            "Outlier",
            "Variação",
            "Data Anterior",
            "Preço Anterior",
            "Preço Ref Anterior",
            "Status Insinf",
            "Tipo Preço",
            "Marca",
            "Emb/Qtd",
            "Desc. Inf",
            "Status Inf",
            "Period",
            "Fator",
            "Operador", 
            "Região do preço",
            "Reg. Ret.",
            "Sinônimo",
            "Cód. Item Elementar",
            "Desc. Item Elementar",
            "Situacao",
            "Id_produto"
    ]
    dados = dados[nova_ordem]
    dados = dados.sort_values(by = "Preço Atual").round(decimals=2)
    gb = GridOptionsBuilder().from_dataframe(dados)
    gb.configure_pagination()

    # if aprove:
    #     if ids is not None:
    #         dados = dados.reset_index(drop=True)
    #         ids_agg = dados.loc[dados["Id_produto"].isin(ids[0])].index.tolist()
    #         gb.configure_selection(selection_mode="multiple",use_checkbox=True)

    #     else:
    #         gb.configure_selection(selection_mode="multiple",use_checkbox=True)
    # else:
    if ids is not None:
        dados = dados.reset_index(drop=True)
        ids_agg = dados.loc[dados["Id_produto"].isin(ids[0])].index.tolist()
        gb.configure_selection(selection_mode="multiple",use_checkbox=True)

    else:
        gb.configure_selection(selection_mode="multiple",use_checkbox=True)

    gridOptions = gb.build()

    data = AgGrid(dados,
                editable=True,
                gridOptions=gridOptions,
                update_mode=GridUpdateMode.SELECTION_CHANGED,
                fit_columns_on_grid_load=False,
                key=key)

    return data