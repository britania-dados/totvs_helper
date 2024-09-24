from objs.helper import helper
from objs.interface import interface
from objs.odbc import odbc  # type: ignore


odbc = odbc()
lista_odbcs = odbc.lista_odbcs()

interface = interface()
odbc_selecionado = interface.seleciona_odbc(lista_odbcs, odbc)

if odbc_selecionado == None:
    quit()

conn = odbc.conecta(odbc_selecionado)    
tabelas = odbc.lista_tabelas(conn)

tabela_selecionada, considera_campos_livres, multi_empresa = interface.seleciona_tabela(tabelas)

if tabela_selecionada == None:
    quit()

recid_tabela = odbc.retorna_recid_tabela_selecionada(tabela_selecionada)   
campos, campos_pk = odbc.lista_campos(odbc_selecionado,recid_tabela, conn)

helper = helper()
query_etl, ddl_create, script_delete, script_update, diferencial = helper.gera_helpers(considera_campos_livres,multi_empresa,tabela_selecionada,campos,campos_pk)

interface.mostra_helpers(query_etl, ddl_create, script_delete, script_update, diferencial)