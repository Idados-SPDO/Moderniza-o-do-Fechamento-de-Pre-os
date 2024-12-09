import streamlit as st
from numpy.core.fromnumeric import mean
import pandas as pd
import data_processing as dp
import plotly.express as px

def page_carrega_dado():

    # Título da página.
    st.title("Ferramenta para análise de preços referenciais")

    # Sessão da página que permitirá o upload de arquivos.
    uploaded_files = st.file_uploader('', accept_multiple_files=True, type="xlsx", label_visibility="hidden")

    with st.spinner('Preparando e guardando os dados de fechamento. Por favor aguarde...'):
        # Verifica se o arquivo carregado não está vazio e, caso não esteja, o guarda em session_state.
        if len(uploaded_files) >= 1:
            for uploaded_file in uploaded_files:
                if uploaded_file.name.startswith('ALIVAR_'):
                    content_alivar = dp.transform_data(uploaded_file, 'ALIVAR')
                if uploaded_file.name.startswith('ALIATA_'):
                    content_aliata = dp.transform_data(uploaded_file, 'ALIATA')
            content_file = pd.concat([content_alivar, content_aliata], ignore_index=True)
            st.session_state.update({"Dados": dp.load_data(content_file)})
        
            # PREENCHENDO SESSION_STATE ------------------------------------------------------------------------------------------

            if st.session_state.Dados is not None:

                list_contrato = ['ALIVAR', 'ALIATA']

                for i in range(len(list_contrato)):

                    list_session_aprove = ["ALIVAR_aprove_items", "ALIATA_aprove_items"]
                    list_session_remove = ["ALIVAR_remove_items", "ALIATA_remove_items"]

                    list_name_items= ["ALIVAR_items", "ALIATA_items"]

                    list_aprove_items = [st.session_state.ALIVAR_aprove_items, st.session_state.ALIATA_aprove_items]

                    list_aprove_ids = [st.session_state.ALIVAR_aprove_ids, st.session_state.ALIATA_aprove_ids]
                    list_remove_ids = [st.session_state.ALIVAR_remove_ids, st.session_state.ALIATA_remove_ids]

                    # Variável que irá guardar temporariamente os dados carregados.
                    df_dados = st.session_state.Dados
                    df_dados = df_dados[df_dados['Contrato'] == list_contrato[i]]

                    produtos = list(df_dados["Produto"].unique())
                    st.session_state.update({list_name_items[i]: produtos})

                    # Variável que irá guardar as linhas com preços não outliers.
                    df_aprove = df_dados[df_dados['Outlier'] != '*']

                    # Variável que irá guardar as linhas com preços outliers.
                    df_remove = df_dados[df_dados['Outlier'] == '*']

                    # Lista contendo todos os itens que contém preços não outliers.
                    selected_items = list(set([row["Produto"] for index, row in df_aprove.iterrows()]))

                    # Lista contendo todos os itens que contém preços outliers.
                    remove_items = list(set([row["Produto"] for index, row in df_remove.iterrows()]))

                    # Verifica se Aprove_ids está vazio.
                    if not list_aprove_ids[i]:

                        # Estando vazio, é feito o preenchimento deste dicionário com os dados de df_aprove.
                        for item in selected_items:
                            df_selecionado = df_aprove[df_aprove['Produto'] == item]
                            selected_ids = [row["Id_produto"] for index, row in df_selecionado.iterrows()]
                            list_aprove_ids[i].update({"{}".format(item):selected_ids})

                        #É feito o preenchimento do dicionário Remove_ids com os dados de df_remove.
                        for item in remove_items:
                            df_selecionado = df_remove[df_remove['Produto'] == item]
                            remove_ids = [row["Id_produto"] for index, row in df_selecionado.iterrows()]
                            list_remove_ids[i].update({"{}".format(item):remove_ids})

                    # Verifica se Aprove_items está vazio.
                    if not list_aprove_items[i]:
                        list_update = []

                        for item in selected_items:
                            df_selecionado = df_aprove[df_aprove['Produto'] == item]
                            if dp.aprova_item(df_selecionado):
                                list_update.append(item)
                        st.session_state.update({list_session_aprove[i]: list_update})
                        
                        if list_contrato[i] == 'ALIVAR':
                            list_update = set(st.session_state.ALIVAR_items).difference(st.session_state.ALIVAR_aprove_items)
                        if list_contrato[i] == 'ALIATA':
                            list_update = set(st.session_state.ALIATA_items).difference(st.session_state.ALIATA_aprove_items)

                        st.session_state.update({list_session_remove[i]: list_update})

                st.session_state.update({"Dados_analise": dp.download_resumido(st.session_state.Dados, st.session_state.ALIVAR_aprove_ids, st.session_state.ALIATA_aprove_ids)})
                st.session_state.update({"Download": dp.download_completo(st.session_state.Dados, st.session_state.ALIVAR_aprove_ids, st.session_state.ALIATA_aprove_ids)})

                # Exibe as primeiras 5 linhas do dataframe carregado.
                st.dataframe(st.session_state.Dados.head().drop(labels=["Id_produto"], axis=1).style.format(precision=2))
                st.info('''A tabela acima mostra apenas as 5 primeiras linhas do arquivo carregado.
                    Por favor, confira se as variáveis estão de acordo com o esperado. Boa análise! 📈''')

def page_visao_geral():

    # Verifica se existem dados para serem analisados
    if st.session_state.Dados is None:

        # Exibe uma mensagem de alerta, caso não existam.
        st.warning("Carregue os dados primeiro")

    else:

        # Criando filtro por nível de regionalização
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            list_status = ["Todos", "Aprovados", "Não Aprovados"]
            tipo_filtro = st.selectbox("Status de Aprovação", options=list_status, index= st.session_state.filter_status)
            st.session_state.update({"filter_status": list_status.index(tipo_filtro)})

        with col2:
            list_praticado = ["Todos", "Aprovado", "Não Aprovado"]
            praticado_filtro = st.selectbox("Status do Preço Praticado", options=list_praticado, index= st.session_state.filter_praticado)
            st.session_state.update({"filter_praticado": list_praticado.index(praticado_filtro)})

        with col3:
            list_comparacao = ["Todos", "Iguais", "Diferentes"]
            comparacao_filtro = st.selectbox("Comparação SFPC", options=list_comparacao, index= st.session_state.filter_comparacao)
            st.session_state.update({"filter_comparacao": list_comparacao.index(comparacao_filtro)})
        
        # Espaçamento.
        st.write('')
        st.write('')

        Aprove_items = list(st.session_state.ALIVAR_aprove_items)
        for item in st.session_state.ALIATA_aprove_items:
            Aprove_items.append(item)
        Aprove_items = list(set(Aprove_items))

        Remove_items = list(st.session_state.ALIVAR_remove_items)
        for item in st.session_state.ALIATA_remove_items:
            Remove_items.append(item)
        Aprove_items = list(set(Remove_items))
       


        # Criando fitros para seleção dos itens.
        col1, col2, col3 = st.columns([1.5, 0.05, 1.5])
        with col1:
            st.header(f'ALIVAR', divider="red")
            st.subheader(f'Aprovados: {len(st.session_state.ALIVAR_aprove_items)} ({dp.formatar_como_porcentagem(len(st.session_state.ALIVAR_aprove_items)/185)})')
            st.subheader(f':red[Não Aprovados:] {len(st.session_state.ALIVAR_remove_items)} ({dp.formatar_como_porcentagem(len(st.session_state.ALIVAR_remove_items)/185)})')
            st.subheader(f':red[Itens Sem Preço:] {185-(len(st.session_state.ALIVAR_aprove_items)+len(st.session_state.ALIVAR_remove_items))}') 
            st.subheader(f':red[Atacado > Varejo:] {dp.qtd_praticado(st.session_state.Dados_analise, "ALIVAR")}')
        with col3:
            st.header(f'ALIATA', divider="red")
            st.subheader(f'Aprovados: {len(st.session_state.ALIATA_aprove_items)} ({dp.formatar_como_porcentagem(len(st.session_state.ALIATA_aprove_items)/185)})')
            st.subheader(f':red[Não Aprovados:] {len(st.session_state.ALIATA_remove_items)} ({dp.formatar_como_porcentagem(len(st.session_state.ALIATA_remove_items)/185)})')
            st.subheader(f':red[Itens Sem Preço:] {185-(len(st.session_state.ALIATA_aprove_items)+len(st.session_state.ALIATA_remove_items))}') 

        # Espaçamento.
        st.write('')
        st.write('')

        df_analise = st.session_state.Dados_analise

        if tipo_filtro == "Todos":

            if comparacao_filtro == "Todos":

                if praticado_filtro == "Aprovado":
                    df_analise = df_analise[df_analise["Preço Praticado"].notna()]
                if praticado_filtro == "Não Aprovado":
                    df_analise = df_analise[df_analise["Preço Praticado"].isna()]

            if comparacao_filtro == "Iguais":

                df_analise = df_analise [ df_analise ["Comparação"] == "Igual" ]

                if praticado_filtro == "Aprovado":
                    df_analise = df_analise[df_analise["Preço Praticado"].notna()]
                if praticado_filtro == "Não Aprovado":
                    df_analise = df_analise[df_analise["Preço Praticado"].isna()]

            if comparacao_filtro == "Diferentes":
                df_analise = df_analise [ df_analise ["Comparação"] == "Diferente" ]

                if praticado_filtro == "Aprovado":
                    df_analise = df_analise[df_analise["Preço Praticado"].notna()]
                if praticado_filtro == "Não Aprovado":
                    df_analise = df_analise[df_analise["Preço Praticado"].isna()]
            
        if tipo_filtro == "Aprovados":

            df_analise = df_analise [ df_analise ["Status"] == "Aprovado" ]

            if comparacao_filtro == "Todos":

                if praticado_filtro == "Aprovado":
                    df_analise = df_analise[df_analise["Preço Praticado"].notna()]
                if praticado_filtro == "Não Aprovado":
                    df_analise = df_analise[df_analise["Preço Praticado"].isna()]

            if comparacao_filtro == "Iguais":
                df_analise = df_analise [ df_analise ["Comparação"] == "Igual" ]

                if praticado_filtro == "Aprovado":
                    df_analise = df_analise[df_analise["Preço Praticado"].notna()]
                if praticado_filtro == "Não Aprovado":
                    df_analise = df_analise[df_analise["Preço Praticado"].isna()]

            if comparacao_filtro == "Diferentes":
                df_analise = df_analise [ df_analise ["Comparação"] == "Diferente" ]

                if praticado_filtro == "Aprovado":
                    df_analise = df_analise[df_analise["Preço Praticado"].notna()]
                if praticado_filtro == "Não Aprovado":
                    df_analise = df_analise[df_analise["Preço Praticado"].isna()]

        if tipo_filtro == "Não Aprovados":

            df_analise = df_analise [ df_analise ["Status"] == "Não Aprovado" ]

            if comparacao_filtro == "Todos":

                if praticado_filtro == "Aprovado":
                    df_analise = df_analise[df_analise["Preço Praticado"].notna()]
                if praticado_filtro == "Não Aprovado":
                    df_analise = df_analise[df_analise["Preço Praticado"].isna()]

            if comparacao_filtro == "Iguais":
                df_analise = df_analise [ df_analise ["Comparação"] == "Igual" ]

                if praticado_filtro == "Aprovado":
                    df_analise = df_analise[df_analise["Preço Praticado"].notna()]
                if praticado_filtro == "Não Aprovado":
                    df_analise = df_analise[df_analise["Preço Praticado"].isna()]

            if comparacao_filtro == "Diferentes":
                df_analise = df_analise [ df_analise ["Comparação"] == "Diferente" ]

                if praticado_filtro == "Aprovado":
                    df_analise = df_analise[df_analise["Preço Praticado"].notna()]
                if praticado_filtro == "Não Aprovado":
                    df_analise = df_analise[df_analise["Preço Praticado"].isna()]

        st.header('Resumo do Fechamento', divider="red")

        st.write('')
        st.write('')
        
        itens_apresentados = df_analise["Produto"]
        col1, col2, col3 = st.columns([1.5, 0.05, 1.5])
        with col1:
            itens_apresentados = df_analise[df_analise["Contrato"] == "ALIVAR"]
            st.subheader(f'Itens disponíveis no ALIVAR: {len(list(set(itens_apresentados["Produto"])))}')
        with col3:
            itens_apresentados = df_analise[df_analise["Contrato"] == "ALIATA"]
            st.subheader(f'Itens disponíveis no ALIATA: {len(list(set(itens_apresentados["Produto"])))}')

        st.write('')
        st.write('')

        itens_apresentados = list(set(itens_apresentados["Produto"]))
        itens_apresentados.insert(0, "Todos")

        # Garantir que o produto selecionado ainda está na lista, senão voltar para 'Todos'
        if st.session_state.filter_desc_geral not in itens_apresentados:
            produto_selecionado = "Todos"
        else:
            produto_selecionado = st.session_state.filter_desc_geral

        produto = st.selectbox(label="Descrição",options=itens_apresentados, index= itens_apresentados.index(produto_selecionado))
        st.session_state.update({"filter_desc_geral": produto})

        st.write('')
        st.write('')
        st.write('')
        st.write('')
        
        if produto == "Todos":
            st.dataframe(df_analise, width = 2000)
        if produto != "Todos":
            st.dataframe(df_analise[df_analise["Produto"] == produto], width = 2000)

        dp.baixar_resultados(st.session_state.Dados_analise, "Dados de Fechamento resumido", "Resumo")
        dp.baixar_resultados(st.session_state.Download, "Dados de Fechamento completo", "Completo")

def page_analisa():

    # Verifica se existem dados para serem analisados
    if st.session_state.Dados is None:

        # Exibe uma mensagem de alerta, caso não existam.
        st.warning("Carregue os dados primeiro")

    else:

        # Criando filtro por nível de regionalização
        col1, col2, col3 = st.columns([1.5, 0.05, 1.5])
        with col1:
            list_contratos = ['ALIVAR', 'ALIATA']
            contrato = st.selectbox("Contrato", options=list_contratos, index= st.session_state.filter_contrato)
            st.session_state.update({"filter_contrato": list_contratos.index(contrato)})


        # Espaçamento.
        st.write('')
        st.write('')
        st.write('')
        st.write('')

        if contrato == 'ALIVAR':
            Aprove_items = st.session_state.ALIVAR_aprove_items  
            Remove_items = st.session_state.ALIVAR_remove_items

            Aprove_ids = st.session_state.ALIVAR_aprove_ids  
            Remove_ids = st.session_state.ALIVAR_remove_ids

        if contrato == 'ALIATA':
            Aprove_items = st.session_state.ALIATA_aprove_items  
            Remove_items = st.session_state.ALIATA_remove_items

            Aprove_ids = st.session_state.ALIATA_aprove_ids  
            Remove_ids = st.session_state.ALIATA_remove_ids

        # Criando fitros para seleção dos itens.
        col1,col2 = st.columns([1.57, 1.5])
        with col1:
            list_tipo = ["Pré-analisados", "Aprovados"]
            tipo_filtro = st.radio("Tipo de filtro", options= list_tipo, index= st.session_state.filter_tipo)
            st.session_state.update({"filter_tipo": list_tipo.index(tipo_filtro)})
        with col2: 
            if tipo_filtro == "Pré-analisados": 
                itens_disp = list(Remove_items)
            else: 
                itens_disp = list(Aprove_items)
            st.metric("Itens disponíveis", len(itens_disp))
        
        produto_selecionado = st.session_state.filter_desc
        if produto_selecionado > len(itens_disp):
            produto_selecionado = 0

        produto = st.selectbox(label="Descrição",options=itens_disp, index= produto_selecionado)
        st.session_state.update({"filter_desc": itens_disp.index(produto)})  

            
        
        # Fazendo seleção dos itens que irão sair.
        ids_to_select = {key:value for (key,value) in Aprove_ids.items() if key == produto}
        ids_to_remove = {key:value for (key,value) in Remove_ids.items() if key == produto}

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
        dados_aprove_agg = dp.agg_table(st.session_state.Dados.query("Produto == '{}' and Id_produto == {} and Contrato == '{}'".format(s, id_s, contrato)),ids=list(ids_to_select.values()), key=f"agg_table_{s}_{id_s}")

        if dados_aprove_agg["selected_rows"] is not None and not dados_aprove_agg["selected_rows"].empty:

            id_r.extend(dados_aprove_agg["selected_rows"]["Id_produto"].tolist())
            id_s = list(set(id_s).difference(set(id_r)))

            if contrato == 'ALIVAR':
                st.session_state.ALIVAR_remove_ids.update({"{}".format(produto):id_r})
                st.session_state.ALIVAR_aprove_ids.update({"{}".format(produto):id_s})
                st.rerun()

            if contrato == 'ALIATA':
                st.session_state.ALIATA_remove_ids.update({"{}".format(produto):id_r})
                st.session_state.ALIATA_aprove_ids.update({"{}".format(produto):id_s})
                st.rerun()

        if ids_to_remove:  # Verifica se existem Ids para analisar.      

            # Criação da tabela com preços em análise para o item selecionado.
            st.subheader('Preços para Análise:', divider="red")
            dados_remove_agg = dp.agg_table(st.session_state.Dados.query("Produto == '{}' and Id_produto == {} and Contrato == '{}'".format(r, id_r, contrato)),ids=list(ids_to_remove.values()), aprove=False, key=f"agg_table_{r}_{id_r}")

            # Mecanismo para passar Ids selecionados da tabela de 'Precos para Análise' para a tabela de 'Preços Aprovados'.
            if dados_remove_agg["selected_rows"] is not None and not dados_remove_agg["selected_rows"].empty:

                id_s.extend(dados_remove_agg["selected_rows"]["Id_produto"].tolist())
                id_r = list(set(id_r).difference(set(id_s)))

                if contrato == 'ALIVAR':
                    st.session_state.ALIVAR_aprove_ids.update({"{}".format(produto):id_s})
                    if id_r:
                        st.session_state.ALIVAR_remove_ids.update({"{}".format(produto):id_r})
                        st.rerun()
                    else:
                        st.session_state.ALIVAR_remove_ids.pop(produto, None)
                        st.rerun()

                if contrato == 'ALIATA':
                    st.session_state.ALIATA_aprove_ids.update({"{}".format(produto):id_s})
                    if id_r:
                        st.session_state.ALIATA_remove_ids.update({"{}".format(produto):id_r})
                        st.rerun()
                    else:
                        st.session_state.ALIATA_remove_ids.pop(produto, None)
                        st.rerun()

        else: # Caso não tenha, retorna apenas o título e uma mensagem de que não há dados a serem analisados.
            st.subheader('Preços para Análise:', divider="red")
            with st.container():
                col1, col2, col3 = st.columns([1.5,1,1])
                col2.write(':grey[Não há dados a serem mostrados.]')
      
        # Transformando a seleção em um Dataframe.
        dados_analise = pd.DataFrame(dados_aprove_agg["data"])
            
        # Gerando tabela de descritivas. 
        if dados_analise.shape[0] == 0:
            st.warning("Todos os itens foram reprovados!")
        else:

            st.subheader("Descritivas")

            # Definindo expander para dicionário de variáveis.
            with st.expander("Dicionário das descritivas abaixo."):

                st.markdown(''' 
                1. **Média (Aprovados e Não Aprovados)**: Média calculada para todos os preços disponíveis, sejam eles removidos ou não.
                2. **Média**: Média calculada considerando apenas os preços que foram validados pelo analista na referência atual.
                        (Com a variação percentual entre o preço atual em relação ao preço da referência passada). 
                3. **Preço de Referência Anterior**: Média calculada considerando apenas os preços que foram validados pelo analista na referência anterior.
                4. **C.V**: O Coeficiente de Variação mostra a dispersão dos dados em relação à média. Quanto maior, mais espalhados os dados; quanto menor, mais próximos da média.
                5. **Status C.V (Coeficiente de variação)**: 
                    * **Até 5:** Ótimo;
                    * **Entre 6 e 15:** Bom;
                    * **Entre 16 e 30:** Razoável;
                    * **Entre 31 e 50:** Pouco preciso;
                    * **Maior que 50:** Impreciso.
                6. **Mínimo**: Menor preço encontrado para o item em análise, considerando apenas os preços que foram validados pelo analista na referência atual.
                7. **Máximo**: Maior preço encontrado para o item em análise, considerando apenas os preços que foram validados pelo analista na referência atual.
                8. **Amplitude**: Diferença entre o maior e o menor preços encontrados para o item analisado, considerando apenas os preços que foram validados pelo analista na referência atual.
                9. **Desvio Padrão**: Dispersão dos preços em relação à média destes para o item analisado, considerando apenas os preços que foram validados pelo analista na referência atual.
                10. **1º Quartil**: Grupo dos 25% menores preços para o item em análise, considerando apenas os preços que foram validados pelo analista na referência atual.  
                11. **Mediana**: Preço central para o item em análise, considerando apenas os preços que foram validados pelo analista na referência atual. 
                12. **3º Quartil**: Grupo dos 75% maiores preços para o item em análise, considerando apenas os preços que foram validados pelo analista na referência atual.   
                13. **Limite Inferior**: Menor preço não discrepante para o item em análise, considerando apenas os preços que foram validados pelo analista na referência atual.
                14. **Limite Superior**: Maior preço não discrepante para o item em análise, considerando apenas os preços que foram validados pelo analista na referência atual.
                15. **Cotações**: Quantidade de preços para o item em análise, considerando apenas os preços que foram validados pelo analista na referência atual.
                ''')

            # Gerando as variáveis de aproveitamento e média fixa que se juntaram as descritivas
            aprov = st.session_state.Dados.groupby("Produto").agg(Media_fixa = ("Preço Atual",mean))

            estatisticas = dp.estatisticas_produtos(dados_analise).join(aprov,on="Produto")

            tabela_estatisticas = estatisticas[[
                "Media_fixa","Media_geral","Preco_ant","Variacao_preco_atual_ant"]].rename(columns= {
                    "Media_fixa":"Média (Aprovados e Não Aprovados)",
                    "Media_geral":"Preço Atual",
                    "Preco_ant":"Preço Ref Anterior",
                    "Variacao_preco_atual_ant":"Variação % (preço atual x anterior)"
            })

            

            # Dicionário contendo as métricas.
            if estatisticas["C_V"].tolist()[0] is not None:
                metricas = {
                    "Média (Aprovados e Não Aprovados)": dp.criar_metrica("Média (Aprovados e Não Aprovados)", "R$ {:.2f}".format(tabela_estatisticas["Média (Aprovados e Não Aprovados)"].tolist()[0])),
                    "Média": dp.criar_metrica("Média", "R$ {:.2f}".format(tabela_estatisticas["Preço Atual"].tolist()[0])),
                    "Preço de Referência Anterior": dp.criar_metrica("Preço de Referência Anterior", "R$ {:.2f}".format(tabela_estatisticas["Preço Ref Anterior"].tolist()[0])),
                    "C.V": dp.criar_metrica("C.V", "{:.2f} %".format(estatisticas["C_V"].tolist()[0])),
                    "Status C.V": dp.criar_metrica("Status C.V", dp.cv_status(estatisticas["C_V"].tolist()[0])),
                    "Mínimo": dp.criar_metrica("Mínimo", "R$ {:.2f}".format(estatisticas["Min"].tolist()[0])),
                    "Máximo": dp.criar_metrica("Máximo", "R$ {:.2f}".format(estatisticas["Max"].tolist()[0])),
                    "Amplitude": dp.criar_metrica("Amplitude", "R$ {:.2f}".format(estatisticas["Amplitude"].tolist()[0])),
                    "Desvio padrão": dp.criar_metrica("Desvio padrão", "{:.2f}".format(estatisticas["D_P"].tolist()[0])),
                    "1º quartil": dp.criar_metrica("1º quartil", "R$ {:.2f}".format(estatisticas["Quartil_1"].tolist()[0])),
                    "Média 1º quartil": dp.criar_metrica("Média 1º quartil", "R$ {:.2f}".format(estatisticas["Media_Quartil1"].tolist()[0])),
                    "Mediana": dp.criar_metrica("Mediana", "R$ {:.2f}".format(estatisticas["Quartil_2"].tolist()[0])),
                    "3º quartil": dp.criar_metrica("3º quartil", "R$ {:.2f}".format(estatisticas["Quartil_3"].tolist()[0])),
                    "Limite inferior": dp.criar_metrica("Limite inferior", "R$ {:.2f}".format(estatisticas["Lim_inf"].tolist()[0])),
                    "Limite superior": dp.criar_metrica("Limite superior", "R$ {:.2f}".format(estatisticas["Lim_sup"].tolist()[0])),
                    "Cotações realizadas": dp.criar_metrica("Cotações realizadas", "{}".format(estatisticas["Cotacoes_realizadas"].tolist()[0]))                   
                }
            else:
                metricas = {
                    "Média (Aprovados e Não Aprovados)": dp.criar_metrica("Média (Aprovados e Não Aprovados)", "R$ {:.2f}".format(tabela_estatisticas["Média (Aprovados e Não Aprovados)"].tolist()[0])),
                    "Média": dp.criar_metrica("Média", "R$ {:.2f}".format(tabela_estatisticas["Preço Atual"].tolist()[0])),
                    "Preço de Referência Anterior": dp.criar_metrica("Preço de Referência Anterior", "R$ {:.2f}".format(tabela_estatisticas["Preço Ref Anterior"].tolist()[0])),
                    "C.V": dp.criar_metrica("C.V", "-"),
                    "Status C.V": dp.criar_metrica("Status C.V", dp.cv_status(estatisticas["C_V"].tolist()[0])),
                    "Mínimo": dp.criar_metrica("Mínimo", "R$ {:.2f}".format(estatisticas["Min"].tolist()[0])),
                    "Máximo": dp.criar_metrica("Máximo", "R$ {:.2f}".format(estatisticas["Max"].tolist()[0])),
                    "Amplitude": dp.criar_metrica("Amplitude", "R$ {:.2f}".format(estatisticas["Amplitude"].tolist()[0])),
                    "Desvio padrão": dp.criar_metrica("Desvio padrão", "{:.2f}".format(estatisticas["D_P"].tolist()[0])),
                    "1º quartil": dp.criar_metrica("1º quartil", "R$ {:.2f}".format(estatisticas["Quartil_1"].tolist()[0])),
                    "Média 1º quartil": dp.criar_metrica("Média 1º quartil", "R$ {:.2f}".format(estatisticas["Media_Quartil1"].tolist()[0])),
                    "Mediana": dp.criar_metrica("Mediana", "R$ {:.2f}".format(estatisticas["Quartil_2"].tolist()[0])),
                    "3º quartil": dp.criar_metrica("3º quartil", "R$ {:.2f}".format(estatisticas["Quartil_3"].tolist()[0])),
                    "Limite inferior": dp.criar_metrica("Limite inferior", "R$ {:.2f}".format(estatisticas["Lim_inf"].tolist()[0])),
                    "Limite superior": dp.criar_metrica("Limite superior", "R$ {:.2f}".format(estatisticas["Lim_sup"].tolist()[0])),
                    "Cotações realizadas": dp.criar_metrica("Cotações realizadas", "{}".format(estatisticas["Cotacoes_realizadas"].tolist()[0]))                   
                }

            # Converter o dicionário em uma lista de dicionários.
            list_metricas = [metricas[chave] for chave in metricas]

            # Criar DataFrame a partir da lista de dicionários.
            df = pd.DataFrame(list_metricas)

            # Título do aplicativo
            st.subheader('Selecione as estatísticas desejadas:')

            # Multi-seleção para escolher as estatísticas.
            estatisticas_selecionadas = st.multiselect('', df['titulo'], default= st.session_state.estatisticas_default, placeholder = "Escolha suas estatísticas", label_visibility = "collapsed" )
            if len(estatisticas_selecionadas) == 5 and estatisticas_selecionadas != st.session_state.estatisticas_default:
                st.session_state.estatisticas_default = estatisticas_selecionadas

            # Geração interativa das estatísticas. 
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

            # Gerando gráfico.    
            st.subheader("Gráfico")
            fig = px.violin(dados_analise, x="Produto", y="Preço Atual", height=800)

            # Posiciona os pontos dentro do violino.
            for trace in fig.data:
                trace.update(points='all', pointpos=0, hoveron="points")

            st.container
            st.plotly_chart(fig, use_container_width=True)

            # Finalizando a análise.
            st.markdown("---")
            if st.button("Registrar análise"):

                with st.spinner('Registrando análise. Por favor aguarde...'):
                    # Atualizando ids dos produtos que serão removidos.
                    if contrato == 'ALIVAR':
                        if s not in st.session_state.ALIVAR_aprove_items:
                            st.session_state.ALIVAR_aprove_items.append(s)
                        st.session_state.update({"Dados_analise": dp.download_resumido(st.session_state.Dados, st.session_state.ALIVAR_aprove_ids, st.session_state.ALIATA_aprove_ids)})
                        st.session_state.update({"Download": dp.download_completo(st.session_state.Dados, st.session_state.ALIVAR_aprove_ids, st.session_state.ALIATA_aprove_ids)})

                    if contrato == 'ALIATA':
                        if s not in st.session_state.ALIATA_aprove_items:
                            st.session_state.ALIATA_aprove_items.append(s)
                        st.session_state.update({"Dados_analise": dp.download_resumido(st.session_state.Dados, st.session_state.ALIVAR_aprove_ids, st.session_state.ALIATA_aprove_ids)})
                        st.session_state.update({"Download": dp.download_completo(st.session_state.Dados, st.session_state.ALIVAR_aprove_ids, st.session_state.ALIATA_aprove_ids)})

                st.success("Análise do {} registrada com sucesso".format(produto))

                st.rerun()

def page_exporta():
    st.write("**Memória de cálculo**")
    dp.baixar_resultados(st.session_state.Dados, "Memória de cálculo")

    
