CREATE TABLE [tot].[CadCli] (
    [empresa] [varchar](2),
    [id] [integer],
    [nome] [varchar](10),
    [DATA_ALTERACAO] [datetime2](7) DEFAULT(GETDATE()),
PRIMARY KEY (
    [id],
    [empresa] 
))

