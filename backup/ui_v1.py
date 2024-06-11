import streamlit as st
from numpy.core.fromnumeric import mean
import os
import pandas as pd
import data_processing as dp
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode
import plotly.express as px

def page_carrega_dado():
    st.title("Ferramenta para análise de preços referenciais")

    st.write("Os dados de entrada para o app devem ser preenchidos de acordo com o arquivo abaixo.")
    diretorio_filho = os.getcwd()
    diretorio_pai = os.path.dirname(diretorio_filho)
    pasta_arquivo = os.path.join(diretorio_pai, "data")
    arquivo = os.listdir(pasta_arquivo)[2]
    caminho_arquivo = os.path.join(pasta_arquivo, arquivo)
    modelo = pd.read_excel(caminho_arquivo)
    dp.baixar_resultados(modelo, "Modelo_preenchimento")

    st.file_uploader("Selecione o arquivo de análise", type="xlsx", key="content_file")

    if st.session_state.content_file is not None:
        st.session_state.update({"Dados": dp.load_data(st.session_state.content_file)})
        st.dataframe(st.session_state.Dados.head().drop(labels=["Id_produto"], axis=1).style.format(precision=2))
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
            dados_agg = dp.agg_table(st.session_state.Dados.query("Produto == '{}'".format(p)),ids=list(ids_to_select.values()))
            selected_ids = [row["Id_produto"] for row in dados_agg["selected_rows"]].append(st.session_state.Remove_ids[f"{p}"])

        else:
            dados_agg = dp.agg_table(st.session_state.Dados.query("Produto == '{}'".format(produto)),ids=None)
            
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
                Com a variação percentual entre o preço atual em relação ao preço da referência passada;
                Com a variação percentual entre o preço atual em relação ao preço de mercado;
                3. **C.V**: O Coeficiente de Variação mostra a dispersão dos dados em relação à média. Quanto maior, mais espalhados os dados; quanto menor, mais próximos da média.
                4. **Status C.V (Coeficiente de variação)**: 
                    * **Até 5:** Ótimo;
                    * **Entre 6 e 15:** Bom;
                    * **Entre 16 e 30:** Razoável;
                    * **Entre 31 e 50:** Pouco preciso;
                    * **Maior que 50:** Impreciso.
                ''')
            # Gerando as variáveis de aproveitamento e média fixa que se juntaram as descritivas
            aprov = st.session_state.Dados.groupby("Produto").agg(Aproveitamento = ("Situacao",dp.aproveitamento),Media_fixa = ("Preço Atual",mean))
            
            # Gerando tabela de descritivas 
            dados_analise_aprovados = dados_analise.query("Situacao==1")
            if dados_analise_aprovados.shape[0] == 0:
                st.warning("Todos os itens foram reprovados!")
            else:
                estatisticas = dp.estatisticas_produtos(dados_analise_aprovados).join(aprov,on="Produto")

                tabela_estatisticas = estatisticas[[
                    "Media_fixa","Media_geral","Preco_ant","Variacao_preco_atual_ant"]].rename(columns= {
                        "Media_fixa":"Média geral",
                        "Media_geral":"Preço Atual",
                        "Preco_ant":"Preço Anterior",
                        "Variacao_preco_atual_ant":"Variação % (preço atual x anterior)"
                })


                col1,col2,col3,col4, col5 = st.columns(5)
                col1.metric("Média geral","R$ {:.2f}".format(tabela_estatisticas["Média geral"].tolist()[0]))
                col2.metric("Preço de Referência Atual","R$ {:.2f}".format(tabela_estatisticas["Preço Atual"].tolist()[0]), "{:.2f} %".format(tabela_estatisticas["Variação % (preço atual x anterior)"].tolist()[0]))
                col3.metric("Preço de Referência Anterior","R$ {:.2f}".format(tabela_estatisticas["Preço Anterior"].tolist()[0]))
                col4.metric("C.V","{:.2f} %".format(estatisticas["C_V"].tolist()[0]))
                col5.metric("Status C.V", dp.cv_status(estatisticas["C_V"].tolist()[0]))
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
                        # col3.metric("Aproveitamento", "{:.1f} %".format(estatisticas["Aproveitamento"].tolist()[0]))

                    

                # Gerando gráfico    
                st.subheader("Gráfico")
                fig = px.violin(dados_analise, x="Produto", y="Preço Atual", height=800)

                # Posiciona os pontos dentro do violino
                for trace in fig.data:
                    trace.update(points='all', pointpos=0, hoveron="points")

                st.container
                st.plotly_chart(fig, use_container_width=True)

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

def page_exporta():
    st.write("**Memória de cálculo**")
    dp.baixar_resultados(st.session_state.Dados, "Memória de cálculo")

def display_model_preenchimento():
    st.write("Os dados de entrada para o app devem ser preenchidos de acordo com o arquivo abaixo.")
    diretorio_filho = os.getcwd()
    diretorio_pai = os.path.dirname(diretorio_filho)
    pasta_arquivo = os.path.join(diretorio_pai, "data")
    arquivo = os.listdir(pasta_arquivo)[2]
    caminho_arquivo = os.path.join(pasta_arquivo, arquivo)
    modelo = pd.read_excel(caminho_arquivo)
    dp.baixar_resultados(modelo, "Modelo_preenchimento")
