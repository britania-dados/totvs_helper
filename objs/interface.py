import PySimpleGUI as sg
from odbc import odbc

class interface:
    @staticmethod
    def seleciona_odbc(lista_odbcs, odbc: odbc):
        layout = [
            [sg.Text("Conexão ODBC:"), sg.Listbox(lista_odbcs, size=(30, 35), bind_return_key=True, key='-ODBC-')],
            [sg.Button("Carregar Tabelas")]
        ]

        window = sg.Window("Totvs Helper", layout, resizable=True, finalize=True)

        while True:
            event, values = window.read()
            if event == sg.WIN_CLOSED:
                window.close()
                return None
            if event == "Carregar Tabelas":
                if not values['-ODBC-']:
                    sg.Popup('ODBC selecionado inválido!')
                else:
                    selected_odbc = values['-ODBC-'][0]
                    try:
                        conn = odbc.conecta(selected_odbc)
                        conn.cursor()
                        window.close()
                        return selected_odbc
                    except Exception as e:
                        sg.Popup(f'ODBC com problema de conexão, validar no odbcad32.exe!\nErro: {e}')

    @staticmethod
    def seleciona_tabela(lista_tabelas):
        layout = [
            [sg.Checkbox('Considera campos livres? ex: char-1, int-1', key='-FREE-FIELDS-')],
            [sg.Checkbox('Tabela Multi-empresa?', default=True, key='-MULTI-EMPRESA-')],
            [sg.Text("Tabela:"), sg.Listbox(lista_tabelas, size=(35, 35), bind_return_key=True, key='-TABLE-')],
            [sg.Button("Selecionar Tabela")]
        ]

        window = sg.Window("Totvs Helper", layout, resizable=True, finalize=True)

        while True:
            event, values = window.read()
            if event == sg.WIN_CLOSED:
                window.close()
                return None, None, None
            if event == "Selecionar Tabela":
                if not values['-TABLE-']:
                    sg.Popup('Tabela inválida!')
                else:
                    selected_table = values['-TABLE-'][0]
                    free_fields = values['-FREE-FIELDS-']
                    multi_empresa = values['-MULTI-EMPRESA-']
                    window.close()
                    return selected_table, free_fields, multi_empresa

    @staticmethod
    def mostra_helpers(query_etl, ddl_create, script_delete, script_update, diferencial):
        
        # Coluna 1
        coluna_1 = [
            [sg.Button('Gerar TXT')],
            [sg.Text("Query para ETL:")],
            [sg.Multiline(query_etl, size=(100, 30), disabled=True)],
            [sg.Text("Diferencial para divisão condicional do SSIS:")],
            [sg.Multiline(diferencial, size=(100, 10), disabled=True)]
        ]

        # Coluna 2
        coluna_2 = [
            [sg.Text("DDL de CREATE:")],
            [sg.Multiline(ddl_create, size=(100, 15), disabled=True)],
            [sg.Text("Script para UPDATE:")],
            [sg.Multiline(script_update, size=(100, 15), disabled=True)],
            [sg.Text("Script para DELETE:")],
            [sg.Multiline(script_delete, size=(100, 15), disabled=True)]
        ]

        # Layout principal com as duas colunas lado a lado
        layout = [
            [sg.Column(coluna_1), sg.VerticalSeparator(), sg.Column(coluna_2)]
        ]

        # Criando a janela
        window = sg.Window("Totvs Helper", layout, resizable=True, finalize=True)

        while True:
            event, values = window.read()
            if event == 'Gerar TXT':
                filename = sg.popup_get_file('Salvar Arquivo', save_as=True, no_window=True, file_types=(("Text Files", "*.txt"),))
                if filename:
                    with open(filename, 'w') as f:
                        f.write('*' * 150)
                        f.write('\nQuery para ETL:\n\n')
                        f.write(query_etl)
                        f.write('\n\n\n\n')
                        f.write('*' * 150)
                        f.write('\nDiferencial para divisão condicional do SSIS:\n\n')
                        f.write(diferencial)
                        f.write('\n\n\n\n')
                        f.write('*' * 150)
                        f.write('\nDDL de CREATE:\n\n')
                        f.write(ddl_create)
                        f.write('\n\n\n\n')
                        f.write('*' * 150)
                        f.write('\nScript para UPDATE:\n\n')
                        f.write(script_update)
                        f.write('\n\n\n\n')
                        f.write('*' * 150)
                        f.write('\nScript para DELETE:\n\n')
                        f.write(script_delete)

                    sg.popup('Arquivo salvo com sucesso!')
            if event == sg.WIN_CLOSED:
                window.close()
                return None

        window.close()
