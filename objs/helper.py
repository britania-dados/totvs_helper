class helper:
    @staticmethod
    def gera_helpers(considera_campos_livres: str,
                     multi_empresa: str,
                     tabela_selecionada: str,
                     campos: list,
                     campos_pk: list) -> str:
        campos_ignorar = ['char-1','char-2','int-1','int-2','dec-1','dec-2','log-1','log-2','data-1','data-2','check-sum','cod-livre-1','cod-livre-2','cod-livre-3','cod-livre-4','cod-livre-5','dat-livre-1','dat-livre-2','dat-livre-3','dat-livre-4','dat-livre-5','val-livre-1','val-livre-2','val-livre-3','val-livre-4','val-livre-5','log-livre-1','log-livre-2','log-livre-3','log-livre-4','log-livre-5','num-livre-1','num-livre-2','num-livre-3','num-livre-4','num-livre-5' ]
        
        query_etl = 'SELECT \n'
        tabela_formatada = tabela_selecionada.title().replace('-','')
        ddl_create = 'CREATE TABLE [tot].[{}] (\n'.format(tabela_formatada)
        
        divisao_condicional = ''
        script_update = ''

        if multi_empresa:
            query_etl = query_etl + '    \'\' as "empresa",\n'
            ddl_create = ddl_create + '    [empresa] [varchar](2),\n'
        
        for campo in campos:            
            if considera_campos_livres == True or campo[0] not in campos_ignorar:
                field_name = campo[0]
                data_type = campo[1]
                width = campo[2]
                decimals = campo[3]
                fetch_datatype = campo[4]
                ddl_create = ddl_create + '    [{}]'.format(field_name)

                if field_name not in campos_pk:
                    if script_update != '':
                        script_update = script_update + '        ,'
                    if divisao_condicional != '':
                        divisao_condicional = divisao_condicional + ' || '
                    
                    replace = '0' if fetch_datatype in ('numeric','decimal','integer') \
                        else '(DT_DBDATE)"1950-01-01"' if fetch_datatype in ('timestamp','datetime','date') \
                        else '""'

                    script_update = script_update + '[{}] = ? \n'.format(field_name)
                    divisao_condicional = divisao_condicional + 'REPLACENULL([{0}],{1}) != REPLACENULL([{0}_LKP],{1})'.format(field_name,replace)

                if fetch_datatype == 'varchar':
                    ddl_create = ddl_create + ' [varchar]({})'.format(width)
                elif fetch_datatype in ('numeric','decimal'):         
                    ddl_create = ddl_create + ' [numeric]({},{})'.format(width,decimals)       
                elif fetch_datatype in ('datetime','timestamp'):       
                    ddl_create = ddl_create + ' [datetime2](7)'  
                elif fetch_datatype in ('lvarbinary','varbinary','blob'):
                    ddl_create = ddl_create + ' [varbinary](max)'      
                else:
                    ddl_create = ddl_create + ' [{}]'.format(fetch_datatype)            

                if data_type == 'character':
                    query_etl = query_etl + '    SUBSTRING("{0}",1,{1}) AS "{0}", \n'.format(field_name,width)                 
                elif data_type == 'date':
                    query_etl = query_etl + '    case \n'
                    query_etl = query_etl + '        when "{}" <= \'01/01/1900\' then convert(\'date\', \'01/01/1900\') \n'.format(field_name)
                    query_etl = query_etl + '        when "{}" >= \'12/31/9999\' then convert(\'date\', \'12/31/9999\') \n'.format(field_name)
                    query_etl = query_etl + '        else convert(\'date\', "{}") \n'.format(field_name)
                    query_etl = query_etl + '    end AS "{}", \n'.format(field_name)                 
                elif data_type == 'logical':                        
                    query_etl = query_etl + '    CONVERT(\'bit\', CASE WHEN "{0}" <> \'1\' THEN \'0\' ELSE \'1\' END) AS "{0}", \n'.format(field_name)                
                else:
                    query_etl = query_etl + '    "{}", \n'.format(field_name)               

                ddl_create = ddl_create + ',\n'
                
            
        query_etl = query_etl[:-3] + '\nfrom PUB."{0}" WITH (NOLOCK)'.format(tabela_selecionada)
        ddl_create = ddl_create + '    [DATA_ALTERACAO] [datetime2](7) DEFAULT(GETDATE()),\nPRIMARY KEY (\n'

        clausula_where = ''

        for campo in campos_pk:
            ddl_create = ddl_create + '    [{}],\n'.format(campo)

            if clausula_where != '':
                clausula_where = clausula_where + '    AND '

            clausula_where = clausula_where + '[{}] = ?\n'.format(campo)

        if multi_empresa:
            ddl_create = ddl_create + '    [empresa] \n'
            clausula_where = clausula_where + '    AND [empresa] = ?'
        else:
            ddl_create = ddl_create[:-2] + '\n'

        ddl_create = ddl_create + '))'
        script_update = 'UPDATE A \n    SET ' + script_update + '    ,[DATA_ALTERACAO] = GETDATE() \n'
        script_update = script_update + 'FROM tot.[{}] A WITH(NOLOCK) \nWHERE {}'.format(tabela_formatada,clausula_where)
        script_delete = 'DELETE A\nFROM tot.[{}] A WITH(NOLOCK) \nWHERE {}'.format(tabela_formatada,clausula_where)
                
        return query_etl, ddl_create, script_delete, script_update, divisao_condicional