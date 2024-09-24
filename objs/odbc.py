import pyodbc
from pyodbc import Connection, Row, Cursor

lista_rows_tabelas = []

class odbc:    

    @staticmethod
    def lista_odbcs() -> list:
        lista_retorno = []
        data_sources = pyodbc.dataSources()

        for data_source in data_sources:
            if 'OpenEdge' in data_sources[data_source]:            
                lista_retorno.append(data_source)
        return lista_retorno


    @staticmethod
    def conecta(dataSource:str) -> Connection:
        try:    
            conn = pyodbc.connect('DSN=' + dataSource + ';Uid=SYSPROGRESS;Pwd=SYSPROGRESS;',timeout=1)
        except:
            try:
                conn = pyodbc.connect('DSN=' + dataSource + ';Uid=sysprogress;Pwd=sysprogress;',timeout=1)  
            except:
                pass
            
        return conn

    @classmethod
    def lista_campos(cls,
                     dataSource:str, 
                     recid_tabela:str,
                     conn: Connection) -> list:        
        try:
            cursor = conn.cursor()
            cursor.execute('''
                    SELECT 
                        C."_field-name"
                        , C."_Data-Type"
                        , C."_Width"
                        , c."_Decimals"
                        , C."_Fetch-Type"
                    from PUB."_field" C        
                    WHERE c."_file-recid" = '{}'
                    ORDER BY C."_Order"     
                    with(nolock)
                '''.format(recid_tabela)
            )
            rows = cursor.fetchall()        
            campos_pk = cls.lista_campos_pk (cursor,recid_tabela)      
                
            cursor.close()
            return rows, campos_pk
        except:
            pass


    @staticmethod
    def lista_campos_pk (cursor: Cursor, 
                         recid_tabela: str) -> list:
        try:
            cursor.execute('''
                    SELECT 
                        C."_Field-Name"	 
                    FROM (
                        SELECT top 1
                            I.ROWID
                        FROM PUB."_Index" I
                        WHERE I."_file-recid" = '{}'
                            AND I."_Active" = 1
                            AND I."_Unique" = 1	
                    ) I
                        JOIN PUB."_Index-Field" IC 
                            ON IC."_Index-recid" = I.ROWID
                        JOIN PUB."_field" C
                            ON c.ROWID = IC."_Field-recid" 
                    with(nolock)
                '''.format(recid_tabela)
            )
            rows = cursor.fetchall()        

            lista_pk = []
            for row in rows:
                lista_pk.append(row[0])

            return lista_pk   
        except:
            pass
        

    @staticmethod
    def lista_tabelas(conn: Connection) -> list: 
        global lista_rows_tabelas
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT
                    "_File-Name"
                    , ROWID 
                FROM PUB."_file" 
                WHERE "_Hidden" = 0
                WITH (nolock)
            ''')

            lista_rows_tabelas = cursor.fetchall()            
            cursor.close()    

            tabelas = []

            for row in lista_rows_tabelas:
                tabelas.append(row[0])
            
            return tabelas
        except:
            pass
    

    @staticmethod
    def retorna_recid_tabela_selecionada(tabela_selecionada :str) -> str:
        global lista_rows_tabelas
        recid_tabela = ''        
        for row in lista_rows_tabelas:
            if row[0] == tabela_selecionada:
                recid_tabela = row[1]
                break
        
        return recid_tabela   
    