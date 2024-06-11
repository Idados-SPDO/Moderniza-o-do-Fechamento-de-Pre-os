from enum import unique
from io import BytesIO
from operator import index
from numpy.core.fromnumeric import mean
from numpy.lib.function_base import median
from numpy.ma.core import empty
from pandas.core.frame import DataFrame
import streamlit as st
import pandas as pd
import numpy as np
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode
import plotly.express as px
import streamlit_authenticator as stauth
import os
import os.path

pd.set_option('display.precision', 2)

st.set_page_config(
    page_title="App Outlier",
    layout="wide"
)

#####################################

def load_data(content_file=None):
    if  content_file is not None:
        content = pd.read_excel(content_file)
        content["Situacao"] = 1
        content = content.astype({
            "Cod_FGV":"object",
            "Descrição_FGV":"object",
            "Unidade_FGV":"object",
            "Preço_Anterior":"float64",
            "Preço_Base":"float64",
            "Insumo_informado":"object",
            "Descrição":"object",
            "Marca":"object",
            "Preço":"float64",
            "Situacao":"Int64"
        })
        content["Produto"] = content["Cod_FGV"].astype(str) + " - " + content["Descrição_FGV"]
        content["Preço"] = content["Preço"].round(decimals = 2)
        content["Id_produto"] = range(0,content.shape[0])
        content["Outlier"] = content.groupby("Descrição_FGV")["Preço"].transform(detecta_outlier)
        content.set_index("Id_produto")
        
        return content

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
    return (np.std(x) / np.mean(x))*100

def lim_inf(x):
    return q_25(x) - 1.5 * (q_75(x) - q_25(x))

def lim_sup(x):
    return q_25(x) + 1.5 * (q_75(x) - q_25(x))

def aproveitamento(x):
    return np.mean(x) * 100

def unique_values(x):
    return pd.unique(x)[0]

def cv_status(x):
    if x <= 5: status = "Ótimo"
    elif x > 5 and x <= 15: status = "Bom"
    elif x > 15 and x <= 30: status = "Razoável"
    elif x > 30 and x <= 50: status = "Pouco preciso"
    else: status = "Impreciso"
    return status

def amplitude(x):
    return max(x) - min(x)

def estatisticas_produtos(dados:pd.DataFrame):

    dados = dados.groupby("Produto").agg(
        Media_geral = ("Preço",mean),
        Unidade_FGV = ("Unidade_FGV",unique_values),
        UF_Regiao = ("UF/Regiao", unique_values),
        C_V = ("Preço",cv),
        D_P = ("Preço",np.std),
        Min = ("Preço",min),
        Max = ("Preço",max),
        Amplitude = ("Preço",amplitude),
        Quartil_1 = ("Preço",q_25),
        Quartil_2 = ("Preço",median),
        Quartil_3 = ("Preço",q_75),
        Lim_inf = ("Preço",lim_inf),
        Lim_sup = ("Preço",lim_sup),
        Preco_ant = ("Preço_Anterior", unique_values),
        Preco_base = ("Preço_Base", unique_values),
        Cotacoes_realizadas = ("Preço",np.size)
    )

    dados["Variacao_preco_atual_ant"] = 100*(dados["Media_geral"] - dados["Preco_ant"]) / dados["Preco_ant"]
    dados["Variacao_preco_atual_base"] = 100*(dados["Media_geral"] - dados["Preco_base"]) / dados["Preco_base"]


    return dados

def preco_referencia(dados:pd.DataFrame):
    aprov = st.session_state.Dados.groupby("Produto").agg(Aproveitamento = ("Situacao",aproveitamento),Media_fixa = ("Preço",mean))
    estatisticas = estatisticas_produtos(dados).join(aprov, on="Produto")
    tabela_estatisticas = estatisticas[[
                "Unidade_FGV","UF_Regiao","Media_fixa","Media_geral","Preco_ant","Variacao_preco_atual_ant",
                "Preco_base","Variacao_preco_atual_base",
                "D_P","Min","Max","Amplitude","Quartil_1","Quartil_2","Quartil_3","Lim_inf","Lim_sup","C_V",
                "Cotacoes_realizadas","Aproveitamento"]].rename(columns= {
                    "Unidade_FGV":"Unidade",
                    "UF_Regiao":"UF/Regiao",
                    "Media_fixa":"Média geral",
                    "Media_geral":"Preço atual",
                    "Preco_ant":"Preço anterior",
                    "Variacao_preco_atual_ant":"Variação % (preço atual x anterior)",
                    "Preco_base":"Preço de mercado",
                    "Variacao_preco_atual_base":"Variação % (preço atual x mercado)",
                    "D_P":"Desvio Padrão",
                    "Min":"Mínimo",
                    "Max":"Máximo",
                    "Quartil_1":"1º Quartil",
                    "Quartil_2":"Mediana",
                    "Quartil_3":"3º Quartil",
                    "Lim_inf":"Limite Inferior",
                    "Lim_sup":"Limite Superior",
                    "C_V":"Coeficiente de Variação",
                    "Cotacoes_realizadas":"Cotações Realizadas"
            })
    coef_status = tabela_estatisticas["Coeficiente de Variação"].apply(cv_status)
    tabela_estatisticas.insert(loc=18, column="C.V Status",value=coef_status)

    return tabela_estatisticas.reset_index().round(decimals = 2)

def memoria_de_calculo(dados:pd.DataFrame):

    aprov = st.session_state.Dados.groupby("Produto").agg(Aproveitamento = ("Situacao",aproveitamento),Media_fixa = ("Preço",mean))
    estatisticas = estatisticas_produtos(dados.query("Situacao == 1")).join(aprov, on="Produto").drop(labels="Unidade_FGV", axis=1)
    dados = dados.join(estatisticas, on="Produto")
    dados["Situacao"] = dados["Situacao"].astype(str).replace(['1','0'], ["Aprovado","Excluido"])
    dados = dados.sort_values(by=['Produto',"Preço"])
    tabela_estatisticas = dados[[
                "Produto","Unidade_FGV","UF_Regiao","Media_fixa","Media_geral","Preco_ant","Variacao_preco_atual_ant",
                "Preco_base","Variacao_preco_atual_base",
                "D_P","Min","Max","Amplitude",
                "Quartil_1","Quartil_2","Quartil_3","Lim_inf","Lim_sup","C_V",
                "Cotacoes_realizadas","Aproveitamento"]].rename(columns= {
                    "Unidade_FGV":"Unidade",
                    "UF_Regiao":"UF/Regiao",
                    "Media_fixa":"Média geral",
                    "Media_geral":"Preço atual",
                    "Preco_ant":"Preço anterior",
                    "Variacao_preco_atual_ant":"Variação % (preço atual x anterior)",
                    "Preco_base":"Preço de mercado",
                    "Variacao_preco_atual_base":"Variação % (preço atual x mercado)",
                    "D_P":"Desvio Padrão",
                    "Min":"Mínimo",
                    "Max":"Máximo",
                    "Quartil_1":"1º Quartil",
                    "Quartil_2":"Mediana",
                    "Quartil_3":"3º Quartil",
                    "Lim_inf":"Limite Inferior",
                    "Lim_sup":"Limite Superior",
                    "C_V":"Coeficiente de Variação",
                    "Cotacoes_realizadas":"Cotações Realizadas"
            })
    coef_status = tabela_estatisticas["Coeficiente de Variação"].apply(cv_status)
    tabela_estatisticas.insert(loc=18, column="C.V Status",value=coef_status)

    return tabela_estatisticas

def agg_table(dados:pd.DataFrame, ids:list):

    dados = dados[[
        "Produto","Unidade_FGV","UF/Regiao","Insumo_informado","Descrição","Marca","Preço","Outlier",
        "Preço_Anterior","Preço_Base",
        "Cod_FGV","Situacao","Id_produto","Descrição_FGV"
    ]]
    dados = dados.sort_values(by = "Preço").round(decimals=2)
    gb = GridOptionsBuilder().from_dataframe(dados)
    gb.configure_pagination()

    if ids is not None:
        dados = dados.reset_index(drop=True)
        ids_agg = dados.loc[dados["Id_produto"].isin(ids[0])].index.tolist()
        gb.configure_selection(selection_mode="multiple",use_checkbox=True,pre_selected_rows=ids_agg)

    else:
        gb.configure_selection(selection_mode="multiple",use_checkbox=True)


    gridOptions = gb.build()

    data = AgGrid(dados,
                editable=True,
                gridOptions=gridOptions,
                update_mode=GridUpdateMode.SELECTION_CHANGED,
                fit_columns_on_grid_load=False)

    return data


###########################

def main():
    
    # Definindo páginas
    pages = {
            "Importar planilha de preços": page_carrega_dado,
            "Análise de preços": page_analisa,
            "Visualização prévia dos resultados": resultados_previos,
            "Gerar preço de referência": page_exporta
        }

    # Caso não tenha nenhuma página, vai pra página de carregamento
    if "page" not in st.session_state:
        st.session_state.update({
            "page": "Importar planilha de preços"
        })

    # Caso não tenha nenhum dado carregado, dados vai receber null
    if "Dados" not in st.session_state:
        st.session_state.update({
            "Dados": None,
            "Remove_ids": dict()
        })

    # Criando menu na barra lateral
    with st.sidebar:
        st.title("FGV IBRE - SPDO")
        page = st.radio("Menu", tuple(pages.keys()))
        st.markdown("---")
        with st.expander("Modelo preenchimento"):
            st.write("Os dados de entrada para o app devem ser preenchidos de acordo com o arquivo abaixo.")
            diretorio_filho = os.getcwd()                          # Para obter o diretório da raiz do código que está rodando
            diretorio_pai = os.path.dirname(diretorio_filho)       # Para voltar uma pasta
            pasta_arquivo = os.path.join(diretorio_pai, "data")    # Para acessar a pasta "data" dentro desse diretório pai
            arquivo = os.listdir(pasta_arquivo)[2]                 # Para obter o nome do arquivo de interesse: "Modelo_preenchimento_usuário.xlsx"
            caminho_arquivo = os.path.join(pasta_arquivo, arquivo) # Definindo o nome do arquivo a ser lido, com a pasta que ele está presente
            modelo = pd.read_excel(caminho_arquivo)
            baixar_resultados(modelo, "Modelo_preenchimento")
        st.markdown('---')
        #st.write('Bem vindo *%s*' % (name))
        #authenticator.logout('Logout', 'main')

    pages[page]()

def page_carrega_dado():
    st.title("Ferramenta para análise de preços referenciais")

    st.file_uploader("Selecione o arquivo de análise",type="xlsx",key="content_file")

    if st.session_state.content_file is not None:
        st.session_state.update({
            "Dados": load_data(st.session_state.content_file)
        })
        st.dataframe(st.session_state.Dados.head().drop(labels = ["Id_produto","Situacao"],axis=1).style.format(precision = 2))
        st.info('''A tabela acima mostra apenas as 5 primeiras linhas do arquivo carregado.
         Por favor, confira se as variáveis estão de acordo com o esperado. Boa análise! 📈''')

def page_analisa():
    #st.title("Análise")

    if st.session_state.Dados is None:
        st.warning("Carregue os dados primeiro")

    else:
        # Definindo variável para produtos
        produtos = st.session_state.Dados["Produto"].unique()

        # Criando fitros para seleção dos itens
        col1,col2 = st.columns(2)
        with col1:
            tipo_filtro = st.radio("Tipo de filtro", options=["Todos","Não aprovados","Aprovados"])
        with col2: 
            if tipo_filtro == "Todos": itens_disp = produtos
            elif tipo_filtro == "Não aprovados": itens_disp = set(produtos).difference(st.session_state.Remove_ids.keys())
            else: itens_disp = st.session_state.Remove_ids.keys()
            st.metric("Itens disponíveis", len(itens_disp))
            
        #********#    
        #Ficou um pouco reduntande como eu associo esses produtos aqui em cima e logo embaixo. Tenho que pensar
        #em algo que otimize essa parte e não tenha que executar a mesma tarefa duas vezes.
        #********#

        # Definindo filtros para seleção dos produtos
        if tipo_filtro == "Todos":
            produto= st.selectbox(label="Descrição",options=produtos)
        elif tipo_filtro == "Não aprovados":
            produtos = set(produtos).difference(st.session_state.Remove_ids.keys())
            produto = st.selectbox(label="Descrição",options=produtos)
        else:
            produtos = st.session_state.Remove_ids.keys()
            produto = st.selectbox(label="Descrição",options=produtos)

        # Fazendo seleção dos itens que irão sair
        if produto in st.session_state.Remove_ids:
            ids_to_select = {key:value for (key,value) in st.session_state.Remove_ids.items() if key == produto}
            p = list(ids_to_select.keys())[0]
            dados_agg = agg_table(st.session_state.Dados.query("Produto == '{}'".format(p)),ids=list(ids_to_select.values()))
            selected_ids = [row["Id_produto"] for row in dados_agg["selected_rows"]].append(st.session_state.Remove_ids[f"{p}"])

        else:
            dados_agg = agg_table(st.session_state.Dados.query("Produto == '{}'".format(produto)),ids=None)
            
        # Transformando a seleção em um Dataframe
        selected_ids = [row["Id_produto"] for row in dados_agg["selected_rows"]]
        dados_analise = pd.DataFrame(dados_agg["data"])
        dados_analise["Situacao"] = [0 if p_id in selected_ids else 1 for p_id in dados_analise["Id_produto"]]

        # Descritivas e gráfico
        if dados_analise.shape[0] > 0:
            st.subheader("Descritivas")

            # Definindo expander para dicionário de variáveis
            with st.expander("Dicionário das descritivas abaixo."):
                st.markdown(''' 
                1. **Média geral**: média calculada para todos os preços disponíveis, sejam eles removidos ou não;
                2. **Preço atual x Preço anterior**: média calculada apenas para os preços que foram validados pelo analista. 
                Com a variação percentual entre o preço atual em relação ao preço do mês passado;
                3. **Preço atual x Preço Mercado**: média calculada apenas para os preços que foram validados pelo analista.
                Com a variação percentual entre o preço atual em relação ao preço de mercado;
                4. **Status Coeficiente de variação:**: 
                    * **Até 5:** Ótimo;
                    * **Mais de 5 a 15:** Bom;
                    * **Mais de 15 a 30:** Razoável;
                    * **Mais de 30 a 50:** Pouco preciso;
                    * **Mais de 50:** Impreciso.
                ''')
            # Gerando as variáveis de aproveitamento e média fixa que se juntaram as descritivas
            aprov = st.session_state.Dados.groupby("Produto").agg(Aproveitamento = ("Situacao",aproveitamento),Media_fixa = ("Preço",mean))
            
            # Gerando tabela de descritivas 
            dados_analise_aprovados = dados_analise.query("Situacao==1")
            if dados_analise_aprovados.shape[0] == 0:
                st.warning("Todos os itens foram reprovados!")
            else:
                estatisticas = estatisticas_produtos(dados_analise_aprovados).join(aprov,on="Produto")

                tabela_estatisticas = estatisticas[[
                    "Media_fixa","Media_geral","Preco_ant","Preco_base","Variacao_preco_atual_ant",
                    "Variacao_preco_atual_base"]].rename(columns= {
                        "Media_fixa":"Média geral",
                        "Media_geral":"Preço atual",
                        "Preco_ant":"Preço anterior",
                        "Variacao_preco_atual_ant":"Variação % (preço atual x anterior)",
                        "Preco_base":"Preço de mercado",
                        "Variacao_preco_atual_base":"Variação % (preço atual x mercado)"
                })

                
                col1,col2,col3,col4,col5 = st.columns(5)
                col1.metric("Média geral","R$ {:.2f}".format(tabela_estatisticas["Média geral"].tolist()[0]))
                col2.metric("Preço atual","R$ {:.2f}".format(tabela_estatisticas["Preço atual"].tolist()[0]))
                col3.metric("Preço anterior","R$ {:.2f}".format(tabela_estatisticas["Preço anterior"].tolist()[0]), "{:.2f} %".format(tabela_estatisticas["Variação % (preço atual x anterior)"].tolist()[0]))
                col4.metric("Preço de mercado","R$ {:.2f}".format(tabela_estatisticas["Preço de mercado"].tolist()[0]), "{:.2f} %".format(tabela_estatisticas["Variação % (preço atual x mercado)"].tolist()[0]))
                col5.metric("Status C.V", cv_status(estatisticas["C_V"].tolist()[0]),"{:.2f} %".format(estatisticas["C_V"].tolist()[0]))
                # Gerando expanders com informações adicionais
                with st.expander("Estatísticas adicionais"):
                    with st.container():
                        col1,col2,col3,col4 = st.columns(4)
                        col1.metric("Mínimo","R$ {:.2f}".format(estatisticas["Min"].tolist()[0]))
                        col2.metric("Máximo", "R$ {:.2f}".format(estatisticas["Max"].tolist()[0]))
                        col3.metric("Amplitude", "R$ {:.2f}".format(estatisticas["Amplitude"].tolist()[0]))
                        col4.metric("Desvio padrão","{:.2f}".format(estatisticas["D_P"].tolist()[0]))
                        
                    with st.container():
                        col1,col2,col3,col4 = st.columns(4)
                        col1.metric("1º quartil", "R$ {:.2f}".format(estatisticas["Quartil_1"].tolist()[0]))
                        col2.metric("2º quartil", "R$ {:.2f}".format(estatisticas["Quartil_2"].tolist()[0]))
                        col3.metric("3º quartil", "R$ {:.2f}".format(estatisticas["Quartil_3"].tolist()[0]))
                        col4.metric("Limite inferior","R$ {:.2f}".format(estatisticas["Lim_inf"].tolist()[0]))
                        
                    with st.container():
                        col1,col2,col3,col4 = st.columns(4)
                        col1.metric("Limite superior","R$ {:.2f}".format(estatisticas["Lim_sup"].tolist()[0]))
                        col2.metric("Cotações realizadas", "{}".format(estatisticas["Cotacoes_realizadas"].tolist()[0]))
                        col3.metric("Aproveitamento", "{:.1f} %".format(estatisticas["Aproveitamento"].tolist()[0]))

                    

                # Gerando gráfico    
                st.subheader("Gráfico")
                fig = px.violin(dados_analise,x="Produto",y="Preço",color="Situacao",points="all",box=False)
                st.plotly_chart(fig)

                # Finalizando a análise
                st.markdown("---")
                if st.button("Registrar análise"):

                    # Atualizando ids dos produtos que serão removidos
                    st.session_state.Remove_ids.update({"{}".format(produto):selected_ids})

                    # Pegando todos os produtos e ids que devem ser removidos
                    ids_rem = []
                    keys_rem = []
                    for k,v in st.session_state.Remove_ids.items():
                        keys_rem.append(k)
                        for v_unitario in v:
                            ids_rem.append(v_unitario)
                    
                    # Atualizando situacao dos produtos no df principal
                    def atualiza_situacao(x):

                        if (x["Produto"] in keys_rem) and (x["Id_produto"] in ids_rem): sit = 0
                        else: sit = 1
                        return sit

                    st.session_state.Dados["Situacao"] = st.session_state.Dados.apply(atualiza_situacao, axis=1)

                    st.success("Análise do {} registrada com sucesso".format(produto))
                
                    # Removendo Produtos que tiveram sua aprovações revogadas
                    st.session_state.Remove_ids = {k:v for k,v in st.session_state.Remove_ids.items() if len(v) > 0}

def resultados_previos():
    st.title("Resultados prévios")
    if st.session_state.Dados is None:
        st.warning("Carregue os dados primeiro")

    elif not st.session_state.Remove_ids:
        st.warning("Ainda não há produtos validados.")
    else:
        produtos_validados = list(st.session_state.Remove_ids.keys())
        filtro_produtos = st.multiselect("Produtos validados", options=produtos_validados)

        if len(filtro_produtos) == 0:
            df_pre_visualizacao = st.session_state.Dados.query(f"Situacao==1 & Produto in {produtos_validados}")
        else:
            df_pre_visualizacao = st.session_state.Dados.query(f"Situacao==1 & Produto in {filtro_produtos}")
        tabela_pre_viz = preco_referencia(df_pre_visualizacao)
        
        st.dataframe(tabela_pre_viz.style.format(precision = 2))

def page_exporta():
    if st.session_state.Dados is None:
        st.warning("Carregue os dados primeiro")
        
    elif not st.session_state.Remove_ids:
        st.warning("Ainda não há produtos validados.")
    else:
        st.title("Resultados")
        produtos_validados = list(st.session_state.Remove_ids.keys())
        
        # Resultados para análise
        st.write("**Análise**")
        resultados_analise = preco_referencia(st.session_state.Dados.query(f"Situacao == 1 & Produto in {produtos_validados}"))
        st.write(resultados_analise.head().style.format(precision = 2))
        baixar_resultados(resultados_analise, "Resultados análise")

        # Resultados para memória de cálculo
        st.write("**Memória de cálculo**")
        resultados_memoria_de_calculo = memoria_de_calculo(st.session_state.Dados.query(f"Produto in {produtos_validados}"))
        st.write(resultados_memoria_de_calculo.head().style.format(precision = 2))
        baixar_resultados(resultados_memoria_de_calculo, "Memória de cálculo")
        



if __name__ == "__main__":

        main()
