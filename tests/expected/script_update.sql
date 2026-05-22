UPDATE A 
    SET [nome] = ? 
    ,[DATA_ALTERACAO] = GETDATE() 
FROM tot.[CadCli] A WITH(NOLOCK) 
WHERE [id] = ?
    AND [empresa] = ?

