import streamlit as st
import pandas as pd
import numpy as np
from numpy.core.fromnumeric import mean
from io import BytesIO
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode

# LEITURA DE DADOS -----------------------------------------------------------------------------------------------------------------------

# Tratamento da base para colocá-la no formato de input da ferramenta
def transform_data(content_file=None, contrato=None):

    if content_file is not None:
        content = pd.read_excel(content_file, header=7)

        
        validador = False
        new_content = pd.DataFrame(columns=['Contrato','Cód. Item Elementar', 'Desc. Item Elementar', 'Insinf/Cd Bases', 'Desc. Insinf', 'Sinônimo', 'Marca', 'Emb/Qtd', 
                                    'Status Insinf', 'Cód Inf', 'Desc. Inf', 'Status Inf', 'Period', 'Preço Atual', 'Fator', 'Operador', 'Data Atual', 
                                    'Preço Anterior', 'SFPC Ref', 'Preço Ref Anterior', 'Data Anterior', 'Tipo Preço', 'Região do preço', 'Reg. Ret.']) 

        for i, j in content.iterrows():
            if validador == False and isinstance(j['Elementar'], int):
                elementar = j['Elementar']
                descricao = j['Descrição']
                ref_anterior = j['Preço ant']
                ref_atual = j["Preço atu"]
            if validador == True:
                new_row = [
                    
                    contrato, elementar, descricao, j['Unnamed: 6'], j['Descrição'], '-', j['Unnamed: 2'], j['Medida'], j['Unnamed: 7'],
                    j['Unnamed: 4'], j['Unnamed: 5'], j['Unnamed: 7'], j['Busca'], j['Cota perf.'], j['Usuário Aprovador'], j['Data Última Aprovação do Item'],
                    j['Cota util'], j['Unnamed: 28'], ref_atual, ref_anterior, j['Unnamed: 29'], j['Variação'], j['Nível'], '-'

                ]
                new_content.loc[len(new_content)] = new_row
            if 'Referência' in str(j['Elementar']) or pd.isna(j['Elementar']):
                validador = False 
            if 'Insumo' in str(j['Elementar']):
                validador = True

        new_content = new_content.dropna(subset=['Insinf/Cd Bases'])
        new_content = new_content.dropna(subset=['Data Anterior'])
        new_content = new_content.dropna(subset=['Data Atual'])
        new_content = new_content.dropna(subset=['Preço Atual'])

        new_content = new_content[new_content['Data Anterior'] != ' ']
        new_content = new_content[new_content['Data Atual'] != ' ']
        new_content = new_content[new_content['Preço Atual'] != ' ']

        return new_content


# Tratamento do dataframe que será importado na primeira página da aplicação, definindo os tipos de cada coluna e criando novas colunas.
def load_data(content_file=None):

    # Condicional que verifica se o arquivo que o arquivo recebido não está vazio.
    if content_file is not None:
        content = pd.DataFrame(content_file)
        content["Situacao"] = 1

        # Definição de tipos de dados.
        content = content.astype({
            "Contrato": "object",
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
            "SFPC Ref": "float64",
            "Preço Ref Anterior": "float64",
            "Data Anterior": "datetime64[ns]",
            "Tipo Preço": "object",
            "Região do preço": "object",
            "Reg. Ret.": "object"
        })

        # Criação de novas colunas necessárias.
        content["Produto"] = content["Cód. Item Elementar"].astype(str) + " - " + content["Desc. Item Elementar"]
        content["Preço Atual"] = content["Preço Atual"].round(decimals=2)
        content["Preço Anterior"] = content["Preço Anterior"].round(decimals=2)
        content["Id_produto"] = range(0, content.shape[0])
        content["Outlier"] = content.groupby(["Produto", "Contrato"])["Preço Atual"].transform(detecta_outlier)
        content["Variação analise"] = (content["Preço Atual"] - content["Preço Anterior"]) / content["Preço Anterior"]
        content["Variação"] = content["Variação analise"].apply(formatar_como_porcentagem)
        content.set_index("Id_produto")
        
        return content

# ESTATÍSTICAS -------------------------------------------------------------------------------------------------------------------------

# Função que faz a detecção de preços outlier.
def detecta_outlier(x):
    limite_inf = lim_inf(x)
    limite_sup = lim_sup(x)
    outlier = ["*" if valor < limite_inf or valor > limite_sup else "" for valor in x]
    return outlier

# Função que define o 1º quartil.
def q_25(x):
    return x.quantile(0.25)

# Função que define a média do 1º quartil.
def media_q25(x):
    limite = q_25(x)
    x = x[x <= limite]


    return x.mean()

# Função que define o 3º quartil.
def q_75(x):
    return x.quantile(0.75)

# Função que define o coeficiente de variação.
def cv(x):
    if len(x.tolist()) > 2:
        return (np.std(x) / np.mean(x)) * 100
    else:
        return None

# Função que define o limite inferior.
def lim_inf(x):
    if (q_25(x) - 1.5 * (q_75(x) - q_25(x))) < 0:
        return 0
    else:
        return q_25(x) - 1.5 * (q_75(x) - q_25(x))

# Função que define o limite superior.
def lim_sup(x):
    return q_75(x) + 1.5 * (q_75(x) - q_25(x))

# Função que define o status do coeficiente de variação.
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

# Função que define a amplitude.
def amplitude(x):
    return max(x) - min(x)


# Função que define valores únicos.
def unique_values(x):
    return pd.unique(x)[0]

def aproveitamento(x):
    return np.mean(x) * 100

# Função que define um dataframe com todas as estatísticas geradas.
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
        Media_Quartil1 = ("Preço Atual", media_q25),
        Quartil_1 = ("Preço Atual", q_25),
        Quartil_2 = ("Preço Atual", "median"),
        Quartil_3 = ("Preço Atual", q_75),
        Lim_inf = ("Preço Atual", lim_inf),
        Lim_sup = ("Preço Atual", lim_sup),
        Preco_ant = ("Preço Ref Anterior", unique_values),
        Cotacoes_realizadas = ("Preço Atual", np.size)
    )

    if dados.index in st.session_state.Itens_media:
        dados["Variacao_preco_atual_ant"] = 100*(dados["Media_geral"] - dados["Preco_ant"]) / dados["Preco_ant"]
    else:
        dados["Variacao_preco_atual_ant"] = 100*(dados["Media_Quartil1"] - dados["Preco_ant"]) / dados["Preco_ant"]
    return dados

# Função que define os parametros para a aprovação de itens.
def aprova_item(df):

    if np.size(df) >= 3 and ( cv_status(cv(df['Preço Atual'])) in ['Bom', 'Ótimo', 'Razoável']) and (estatisticas_produtos(df)["Variacao_preco_atual_ant"].apply(lambda x: -19 <= x <= 19).all()):

        return True
    else:
        
        return False

# Função que adiciona o status do item (Aprovado e Não Aprovado) aos arquivos de download
def status_item(x):

    produto = x['Produto']
    contrato = x['Contrato']
    
    if contrato == "ALIVAR" and produto in st.session_state.ALIVAR_aprove_items:
        return "Aprovado"
    elif contrato == "ALIATA" and produto in st.session_state.ALIATA_aprove_items:
        return "Aprovado"
    else:
        return "Não Aprovado"

# Função que adiciona o status de comparação do preço (igual ao SFPC ou diferente do SFPC) aos arquivos de download.
def status_preco(x):

    try:
        mfp = x['Preco_referencia']
        sfpc = x['SFPC Ref']
    except KeyError:
        mfp = x['Preco_referencia']
        sfpc = x['SFPC_ref']
    
    if mfp == sfpc:
        return "Igual"
    else:
        return "Diferente"

# Função que adiciona os preços de referência aos arquivos de download.
def calcular_referencia(df, resumo, row=None):
    """
    df --> dataframe que será recebido pela função;
    resumo --> parâmetro booleano que indica se será retornada uma agregação ou não;
    row --> Caso resumo seja False, é necessário que a função receba o argumento row, já que terá que ser aplicada como lambda na coluna que será criada;
    """

    if resumo:

        produto = df["Produto"].iloc[0]

        if produto in st.session_state.Itens_media:
            preco_referencia = mean(df["Preço Atual"])
        else:
            preco_referencia = media_q25(df["Preço Atual"])

        return pd.Series({
            "Preco_referencia": preco_referencia,
            "Preco_ant": unique_values(df["Preço Ref Anterior"]),
            "SFPC_ref": unique_values(df["SFPC Ref"]),
            "C_V": cv(df["Preço Atual"]),
            "Cotacoes_realizadas": len(df)
        })
    else:

        produto = row['Produto']
        contrato = row['Contrato']
        precos = df[(df['Produto'] == produto) & (df['Contrato'] == contrato)]
        preco = precos["Preço Atual"]

        if produto in st.session_state.Itens_media:
            preco_referencia = mean(preco)
        else:
            preco_referencia = media_q25(preco)

        return preco_referencia

# Função que adiciona os preços praticados aos arquivos de download.
def calcular_praticado(row, df, preco):

    produto = row['Produto']
    
    # Filtra os preços de referência para o mesmo produto nos dois contratos.
    precos = df[df['Produto'] == produto]
    preco_alivar = precos.loc[precos['Contrato'] == 'ALIVAR', preco].values
    preco_aliata = precos.loc[precos['Contrato'] == 'ALIATA', preco].values
    
    # Garante que ambos os preços existam para o cálculo.
    if len(preco_alivar) > 0 and len(preco_aliata) > 0:
        preco_alivar = preco_alivar[0]
        preco_aliata = preco_aliata[0]
        
        # Calcula o Preco_praticado para o contrato ALIATA se o ALIVAR tiver maior preço.
        if preco_alivar > preco_aliata:
            return preco_aliata + 0.75 * (preco_alivar - preco_aliata)
    
    # Retorna None para todos os outros casos.
    return None

# Função que retorna a quantidade de itens que possuem o preço de atacado maior que o preço de varejo.
def qtd_praticado(df, contrato):

    df_filtrado = df[df["Contrato"] == contrato]

    total_none = df_filtrado['Preço Praticado'].isna().sum()

    return total_none

# DATAFRAMES -----------------------------------------------------------------------------------------------------

# Função que retorna o dataframe com os dados de fechamento resumidos por item.
def download_resumido(dados, ALIVAR_aprove_ids, ALIATA_aprove_ids):

    # Inicializando 'dados_selecionados' com as colunas de 'dados'
    dados_selecionados = pd.DataFrame(columns=dados.columns)

    list_dicts_ids = [ALIVAR_aprove_ids, ALIATA_aprove_ids]

    # Combina todos os IDs dos dicionários em um único conjunto
    ids_aprovados = set(id for d in list_dicts_ids for id_list in d.values() for id in id_list)
    
    # Filtra o DataFrame para incluir apenas os produtos cujos IDs estão no conjunto
    dados_selecionados = dados[dados['Id_produto'].isin(ids_aprovados)]

    dados_selecionados = dados_selecionados.groupby(["Produto", "Contrato"]).apply(calcular_referencia, resumo=True).reset_index()

    dados_selecionados['Var. (%)'] = (
        (dados_selecionados['Preco_referencia'] - dados_selecionados['Preco_ant'])
        / dados_selecionados['Preco_ant']
    ) * 100
    dados_selecionados['Status'] = dados_selecionados.apply(status_item, axis=1)
    dados_selecionados['Preço Praticado Ant.'] = dados_selecionados.apply(lambda row: calcular_praticado(row, dados_selecionados, "Preco_ant"), axis=1)
    dados_selecionados['Preço Praticado'] = dados_selecionados.apply(lambda row: calcular_praticado(row, dados_selecionados, "Preco_referencia"), axis=1)

    dados_selecionados['Var. Praticado (%)'] = (
        (dados_selecionados['Preço Praticado'] - dados_selecionados['Preço Praticado Ant.'])
        / dados_selecionados['Preço Praticado Ant.']
    ) * 100

    dados_selecionados["SFPC_ref"] = pd.to_numeric(dados_selecionados["SFPC_ref"], errors='coerce').round(2)
    dados_selecionados["Preco_referencia"] = pd.to_numeric(dados_selecionados["Preco_referencia"], errors='coerce').round(2)
    dados_selecionados["Preço Praticado"] = pd.to_numeric(dados_selecionados["Preço Praticado"], errors='coerce').round(2)
    dados_selecionados["C_V"] = pd.to_numeric(dados_selecionados["C_V"], errors='coerce').round(2)
    dados_selecionados["Preço Praticado Ant."] = pd.to_numeric(dados_selecionados["Preço Praticado Ant."], errors='coerce').round(2)
    dados_selecionados['Var. (%)'] = pd.to_numeric(dados_selecionados['Var. (%)'], errors='coerce').round(2)
    dados_selecionados['Var. Praticado (%)'] = pd.to_numeric(dados_selecionados['Var. Praticado (%)'], errors='coerce').round(2)

    dados_selecionados['Comparação'] = dados_selecionados.apply(status_preco, axis=1)

    dados_selecionados = dados_selecionados.rename(columns={
        'SFPC_ref': 'SFPC Ref',
        'Preco_referencia': 'Preço de Referência',
        'Preco_ant': 'Preço de Referência Ant.',
        'C_V': 'C.V (%)',
        'Cotacoes_realizadas': 'Cotações Realizadas'
    })

    # Nova ordem das colunas
    nova_ordem = [
        'Produto', 'Contrato', 'Cotações Realizadas', 'C.V (%)', 'Comparação', 'SFPC Ref', 'Preço de Referência', 
        'Preço de Referência Ant.', 'Var. (%)', 'Status', 'Preço Praticado', 
        'Preço Praticado Ant.', 'Var. Praticado (%)'
    ]

    # Reordenando o DataFrame
    dados_selecionados = dados_selecionados[nova_ordem]

    return dados_selecionados

# Função que retorna o dataframe de dados de fechamento completo.
def download_completo(dados, ALIVAR_aprove_ids, ALIATA_aprove_ids):

    # Inicializando 'dados_selecionados' com as colunas de 'dados'
    dados_selecionados = pd.DataFrame(columns=dados.columns)

    list_dicts_ids = [ALIVAR_aprove_ids, ALIATA_aprove_ids]

    # Combina todos os IDs dos dicionários em um único conjunto
    ids_aprovados = set(id for d in list_dicts_ids for id_list in d.values() for id in id_list)
    
    # Filtra o DataFrame para incluir apenas os produtos cujos IDs estão no conjunto
    dados_selecionados = dados[dados['Id_produto'].isin(ids_aprovados)]

    dados_selecionados['Preco_referencia'] = dados_selecionados.apply(lambda row: calcular_referencia(dados_selecionados, False, row), axis=1)

    dados_selecionados['Var. (%)'] = (
        (dados_selecionados['Preco_referencia'] - dados_selecionados["Preço Ref Anterior"])
        / dados_selecionados["Preço Ref Anterior"]
    ) * 100
    dados_selecionados['Status'] = dados_selecionados.apply(status_item, axis=1)
    dados_selecionados['Preço Praticado Ant.'] = dados_selecionados.apply(lambda row: calcular_praticado(row, dados_selecionados, "Preço Ref Anterior"), axis=1)
    dados_selecionados['Preço Praticado'] = dados_selecionados.apply(lambda row: calcular_praticado(row, dados_selecionados, "Preco_referencia"), axis=1)

    dados_selecionados['C.V (%)'] = dados_selecionados.apply(
        lambda row: cv(
            dados_selecionados[
                (dados_selecionados['Produto'] == row['Produto']) &
                (dados_selecionados['Contrato'] == row['Contrato'])
            ]['Preço Atual']
        ), 
        axis=1
    )

    dados_selecionados['Cotações Realizadas'] = dados_selecionados.apply(
    lambda row: dados_selecionados[
        (dados_selecionados['Produto'] == row['Produto']) &
        (dados_selecionados['Contrato'] == row['Contrato'])
    ].shape[0], 
    axis=1
    )

    dados_selecionados['Var. Praticado (%)'] = (
        (dados_selecionados['Preço Praticado'] - dados_selecionados['Preço Praticado Ant.'])
        / dados_selecionados['Preço Praticado Ant.']
    ) * 100

    dados_selecionados["SFPC Ref"] = pd.to_numeric(dados_selecionados["SFPC Ref"], errors='coerce').round(2)
    dados_selecionados["Preco_referencia"] = pd.to_numeric(dados_selecionados["Preco_referencia"], errors='coerce').round(2)
    dados_selecionados["Preço Praticado"] = pd.to_numeric(dados_selecionados["Preço Praticado"], errors='coerce').round(2)
    dados_selecionados["C.V (%)"] = pd.to_numeric(dados_selecionados["C.V (%)"], errors='coerce').round(2)
    dados_selecionados["Preço Praticado Ant."] = pd.to_numeric(dados_selecionados["Preço Praticado Ant."], errors='coerce').round(2)
    dados_selecionados['Var. (%)'] = pd.to_numeric(dados_selecionados['Var. (%)'], errors='coerce').round(2)
    dados_selecionados['Var. Praticado (%)'] = pd.to_numeric(dados_selecionados['Var. Praticado (%)'], errors='coerce').round(2)

    dados_selecionados['Comparação'] = dados_selecionados.apply(status_preco, axis=1)

    dados_selecionados = dados_selecionados.rename(columns={
        'Preco_referencia': 'Preço de Referência',
        "Preço Ref Anterior": 'Preço de Referência Ant.'
    })

    # Nova ordem das colunas
    nova_ordem = [
        "Contrato", "Cód. Item Elementar", "Desc. Item Elementar", "Comparação", 
        "Cotações Realizadas", "C.V (%)", "SFPC Ref", "Preço de Referência", 
        "Preço de Referência Ant.", "Var. (%)","Status", "Preço Praticado", 
        "Preço Praticado Ant.", "Var. Praticado (%)", "Insinf/Cd Bases", "Desc. Insinf", 
        "Preço Atual", "Preço Anterior", "Marca", "Emb/Qtd", "Cód Inf", "Desc. Inf", 
        "Period", "Fator", "Operador", "Data Atual", "Data Anterior", "Tipo Preço", 
        "Região do preço", "Reg. Ret.", "Produto"
    ]

    # Reordenando o DataFrame
    dados_selecionados = dados_selecionados[nova_ordem]

    return dados_selecionados
    
# Função que define a tabela de checkbox para seleção manual de preços aprovados ou não aprovados.
def agg_table(dados:pd.DataFrame, ids:list, aprove=True, key: str=None):

    # Definição de nova ordem da tabela.
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

    # Define a ordenação das linhas pelos preços atuais, de forma crescente.
    dados = dados.sort_values(by = "Preço Atual").round(decimals=2)

    gb = GridOptionsBuilder().from_dataframe(dados)
    gb.configure_pagination()

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

def criar_metrica(titulo, valor, subtitulo=None):
    metrica = {
        "titulo": titulo,
        "valor": valor,
        "subtitulo": subtitulo
    }
    
    return metrica

# FORMATAÇÃO -----------------------------------------------------------------------------------------------------
    
# Função que define um formato padrão para porcentagens.
def formatar_como_porcentagem(x):
    return "{:.2%}".format(x)
    
# DOWNLOAD -------------------------------------------------------------------------------------------------------

# Função que permite ao usuário fazer download de arquivos.
def baixar_resultados(df, arquivo, tipo):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=arquivo)
    buffer.seek(0)  # Volte ao início do buffer
    if tipo == "Resumo":
        return st.download_button(label="Baixar Dados resumidos de Fechamento", data=buffer, file_name=f"{arquivo}.xlsx")
    if tipo == "Completo":
        return st.download_button(label="Baixar Dados completos de Fechamento", data=buffer, file_name=f"{arquivo}.xlsx")
