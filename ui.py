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


    # Definindo o estilo CSS
    hide_label = '''
    <style>
    [data-testid="stFileUploadDropzone"] div div::before {font-size: 1.5em; content:"Selecione o arquivo."}
    [data-testid="stFileUploadDropzone"] div div span{display:none;}
    [data-testid="stFileUploadDropzone"] div div::after {content:"Limite de 200Mb por arquivo."}
    [data-testid="stFileUploadDropzone"] div div small{display:none;}
    </style>
    '''

    st.markdown(hide_label, unsafe_allow_html=True)

    st.file_uploader("a", type="xlsx", key="content_file", label_visibility="hidden")

    

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
        
        df_dados = st.session_state.Dados
        df_aprove = df_dados[df_dados['Outlier'] != '*']
        df_remove = df_dados[df_dados['Outlier'] == '*']

        selected_items = list(set([row["Produto"] for index, row in df_aprove.iterrows()]))
        remove_items = list(set([row["Produto"] for index, row in df_remove.iterrows()]))
        if not st.session_state.Aprove_ids:
            for item in selected_items:
                df_selecionado = df_aprove[df_aprove['Produto'] == item]
                selected_ids = [row["Id_produto"] for index, row in df_selecionado.iterrows()]
                st.session_state.Aprove_ids.update({"{}".format(item):selected_ids})

            for item in remove_items:
                df_selecionado = df_remove[df_remove['Produto'] == item]
                remove_ids = [row["Id_produto"] for index, row in df_selecionado.iterrows()]
                st.session_state.Remove_ids.update({"{}".format(item):remove_ids})
        
        # Criando fitros para seleção dos itens
        col1,col2 = st.columns(2)
        with col1:
            tipo_filtro = st.radio("Tipo de filtro", options=["Pré-analisados", "Aprovados"])
        with col2: 
            if tipo_filtro == "Pré-analisados": 
                itens_disp = set(produtos).difference(st.session_state.Aprove_items.keys())
            else: 
                itens_disp = st.session_state.Aprove_items.keys()
            st.metric("Itens disponíveis", len(itens_disp))

        # Definindo filtros para seleção dos produtos
        
        if tipo_filtro == "Pré-analisados":
            produtos = set(produtos).difference(st.session_state.Aprove_items.keys())
            produto = st.selectbox(label="Descrição",options=produtos)
        else:
            produtos = st.session_state.Aprove_items.keys()
            produto = st.selectbox(label="Descrição",options=produtos)        
        
        # Fazendo seleção dos itens que irão sair
        # if produto in st.session_state.Aprove_items:
        ids_to_select = {key:value for (key,value) in st.session_state.Aprove_ids.items() if key == produto}
        ids_to_remove = {key:value for (key,value) in st.session_state.Remove_ids.items() if key == produto}

        s = list(ids_to_select.keys())[0]
        id_s = list(set(list(ids_to_select.values())[0]))

        if ids_to_remove:
            r = list(ids_to_remove.keys())[0]
            id_r = list(set(list(ids_to_remove.values())[0]))
        else:
            r = []
            id_r = []

        # Criação da tabela com preços aprovados para o item selecionado.
        st.subheader('Preços Aprovados:', divider="red")
        dados_aprove_agg = dp.agg_table(st.session_state.Dados.query("Produto == '{}' and Id_produto == {}".format(s, id_s)),ids=list(ids_to_select.values()), key=f"agg_table_{s}_{id_s}")

        # Mecanismo para passar Ids selecionados da tabela de 'Preços Aprovados' para a tabela de 'Precos para Análise'.
        if len([row["Id_produto"] for row in dados_aprove_agg["selected_rows"]]) >= 1:
            id_r.extend([row["Id_produto"] for row in dados_aprove_agg["selected_rows"]])
            id_s = list(set(id_s).difference(set(id_r)))
            st.write(id_s)
            st.session_state.Remove_ids.update({"{}".format(produto):id_r})
            st.session_state.Aprove_ids.update({"{}".format(produto):id_s})
            st.experimental_rerun()

        if ids_to_remove:  # Verifica se existem Ids para analisar      

            # Criação da tabela com preços em análise para o item selecionado.
            st.subheader('Preços para Análise:', divider="red")
            dados_remove_agg = dp.agg_table(st.session_state.Dados.query("Produto == '{}' and Id_produto == {}".format(r, id_r)),ids=list(ids_to_remove.values()), aprove=False, key=f"agg_table_{r}_{id_r}")

            # Mecanismo para passar Ids selecionados da tabela de 'Precos para Análise' para a tabela de 'Preços Aprovados'.
            if len([row["Id_produto"] for row in dados_remove_agg["selected_rows"]]) >= 1:
                id_s.extend([row["Id_produto"] for row in dados_remove_agg["selected_rows"]])
                id_r = list(set(id_r).difference(set(id_s)))
                st.write(id_r)
                st.session_state.Aprove_ids.update({"{}".format(produto):id_s})
                if id_r:
                    st.session_state.Remove_ids.update({"{}".format(produto):id_r})
                    st.experimental_rerun()
                else:
                    st.session_state.Remove_ids.pop(produto, None)
                    st.experimental_rerun()

        else: # Caso não tenha, retorna apenas o título e uma mensagem de que não há dados a serem analisados.
            st.subheader('Preços para Análise:', divider="red")
            with st.container():
                col1, col2, col3 = st.columns([1.5,1,1])
                col2.write(':grey[Não há dados a serem mostrados.]')
                
        # else:
        #     # dados_remove_agg = dp.agg_table(st.session_state.Dados.query("Produto == '{}'".format(produto)),ids=None)
        #     dados_agg = dp.agg_table(st.session_state.Dados.query("Produto == '{}'".format(produto)),ids=None)
      
        # Transformando a seleção em um Dataframe
        # selected_ids = [row["Id_produto"] for row in dados_remove_agg["selected_rows"]]
        dados_analise = pd.DataFrame(dados_aprove_agg["data"])
        #dados_analise["Situacao"] = [0 if p_id in selected_ids else 1 for p_id in dados_analise["Id_produto"]]

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
            # dados_analise_aprovados = dados_analise.query("Situacao==1")
            if dados_analise.shape[0] == 0:
                st.warning("Todos os itens foram reprovados!")
            else:
                estatisticas = dp.estatisticas_produtos(dados_analise).join(aprov,on="Produto")

                tabela_estatisticas = estatisticas[[
                    "Media_fixa","Media_geral","Preco_ant","Variacao_preco_atual_ant"]].rename(columns= {
                        "Media_fixa":"Média geral",
                        "Media_geral":"Preço Atual",
                        "Preco_ant":"Preço Ref Anterior",
                        "Variacao_preco_atual_ant":"Variação % (preço atual x anterior)"
                })

                def criar_metrica(titulo, valor, subtitulo=None):
                    metrica = {
                        "titulo": titulo,
                        "valor": valor,
                        "subtitulo": subtitulo
                    }
                    return metrica

                # Dicionário contendo as métricas
                if estatisticas["C_V"].tolist()[0] is not None:
                    metricas = {
                        "Média geral": criar_metrica("Média geral", "R$ {:.2f}".format(tabela_estatisticas["Média geral"].tolist()[0])),
                        "Preço de Referência Atual": criar_metrica("Preço de Referência Atual", "R$ {:.2f}".format(tabela_estatisticas["Preço Atual"].tolist()[0]), "{:.2f} %".format(tabela_estatisticas["Variação % (preço atual x anterior)"].tolist()[0])),
                        "Preço de Referência Anterior": criar_metrica("Preço de Referência Anterior", "R$ {:.2f}".format(tabela_estatisticas["Preço Ref Anterior"].tolist()[0])),
                        "C.V": criar_metrica("C.V", "{:.2f} %".format(estatisticas["C_V"].tolist()[0])),
                        "Status C.V": criar_metrica("Status C.V", dp.cv_status(estatisticas["C_V"].tolist()[0])),
                        "Mínimo": criar_metrica("Mínimo", "R$ {:.2f}".format(estatisticas["Min"].tolist()[0])),
                        "Máximo": criar_metrica("Máximo", "R$ {:.2f}".format(estatisticas["Max"].tolist()[0])),
                        "Amplitude": criar_metrica("Amplitude", "R$ {:.2f}".format(estatisticas["Amplitude"].tolist()[0])),
                        "Desvio padrão": criar_metrica("Desvio padrão", "{:.2f}".format(estatisticas["D_P"].tolist()[0])),
                        "1º quartil": criar_metrica("1º quartil", "R$ {:.2f}".format(estatisticas["Quartil_1"].tolist()[0])),
                        "Mediana": criar_metrica("Mediana", "R$ {:.2f}".format(estatisticas["Quartil_2"].tolist()[0])),
                        "3º quartil": criar_metrica("3º quartil", "R$ {:.2f}".format(estatisticas["Quartil_3"].tolist()[0])),
                        "Limite inferior": criar_metrica("Limite inferior", "R$ {:.2f}".format(estatisticas["Lim_inf"].tolist()[0])),
                        "Limite superior": criar_metrica("Limite superior", "R$ {:.2f}".format(estatisticas["Lim_sup"].tolist()[0])),
                        "Cotações realizadas": criar_metrica("Cotações realizadas", "{}".format(estatisticas["Cotacoes_realizadas"].tolist()[0]))                   
                    }
                else:
                    metricas = {
                        "Média geral": criar_metrica("Média geral", "R$ {:.2f}".format(tabela_estatisticas["Média geral"].tolist()[0])),
                        "Preço de Referência Atual": criar_metrica("Preço de Referência Atual", "R$ {:.2f}".format(tabela_estatisticas["Preço Atual"].tolist()[0]), "{:.2f} %".format(tabela_estatisticas["Variação % (preço atual x anterior)"].tolist()[0])),
                        "Preço de Referência Anterior": criar_metrica("Preço de Referência Anterior", "R$ {:.2f}".format(tabela_estatisticas["Preço Ref Anterior"].tolist()[0])),
                        "C.V": criar_metrica("C.V", "-"),
                        "Status C.V": criar_metrica("Status C.V", dp.cv_status(estatisticas["C_V"].tolist()[0])),
                        "Mínimo": criar_metrica("Mínimo", "R$ {:.2f}".format(estatisticas["Min"].tolist()[0])),
                        "Máximo": criar_metrica("Máximo", "R$ {:.2f}".format(estatisticas["Max"].tolist()[0])),
                        "Amplitude": criar_metrica("Amplitude", "R$ {:.2f}".format(estatisticas["Amplitude"].tolist()[0])),
                        "Desvio padrão": criar_metrica("Desvio padrão", "{:.2f}".format(estatisticas["D_P"].tolist()[0])),
                        "1º quartil": criar_metrica("1º quartil", "R$ {:.2f}".format(estatisticas["Quartil_1"].tolist()[0])),
                        "Mediana": criar_metrica("Mediana", "R$ {:.2f}".format(estatisticas["Quartil_2"].tolist()[0])),
                        "3º quartil": criar_metrica("3º quartil", "R$ {:.2f}".format(estatisticas["Quartil_3"].tolist()[0])),
                        "Limite inferior": criar_metrica("Limite inferior", "R$ {:.2f}".format(estatisticas["Lim_inf"].tolist()[0])),
                        "Limite superior": criar_metrica("Limite superior", "R$ {:.2f}".format(estatisticas["Lim_sup"].tolist()[0])),
                        "Cotações realizadas": criar_metrica("Cotações realizadas", "{}".format(estatisticas["Cotacoes_realizadas"].tolist()[0]))                   
                    }

                # Converter o dicionário em uma lista de dicionários
                list_metricas = [metricas[chave] for chave in metricas]

                # Criar DataFrame a partir da lista de dicionários
                df = pd.DataFrame(list_metricas)

                # Título do aplicativo
                st.subheader('Selecione as estatísticas desejadas:')

                # Multi-seleção para escolher as estatísticas
                estatisticas_selecionadas = st.multiselect('', df['titulo'], default= st.session_state.estatisticas_default, placeholder = "Escolha suas estatísticas", label_visibility = "collapsed" )
                if len(estatisticas_selecionadas) == 5 and estatisticas_selecionadas != st.session_state.estatisticas_default:
                    st.session_state.estatisticas_default = estatisticas_selecionadas
                # Geração interativa das estatísticas 
                if estatisticas_selecionadas:
                    num_estatisticas = len(estatisticas_selecionadas)
                    num_colunas = min(num_estatisticas, 5)
                    
                    with st.container():
                        colunas = st.columns(num_colunas)
                        
                        with st.container():
                            for i in range(0, num_estatisticas, 5):
                                with st.container():
                                    colunas = st.columns(num_colunas)
                                    
                                    for j in range(num_colunas):
                                        index = i + j
                                        if index < num_estatisticas:
                                            col = colunas[j]
                                            col.metric(
                                                metricas[estatisticas_selecionadas[index]]['titulo'],
                                                metricas[estatisticas_selecionadas[index]]['valor'],
                                                metricas[estatisticas_selecionadas[index]]['subtitulo']
                                            )           

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
                    st.session_state.Aprove_items.update({"{}".format(s):id_s})

                    # Pegando todos os produtos e ids que devem ser removidos
                    ids_rem = []
                    keys_rem = []
                    for k,v in st.session_state.Aprove_items.items():
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

                    st.experimental_rerun()
                
                    # Removendo Produtos que tiveram sua aprovações revogadas
                    # st.session_state.Aprove_items = {k:v for k,v in st.session_state.Aprove_items.items() if len(v) > 0}

def page_exporta():
    st.write("**Memória de cálculo**")
    dp.baixar_resultados(st.session_state.Dados, "Memória de cálculo")

    
