SELECT 
    '' as "empresa", 
    "id", 
    SUBSTRING("nome",1,10) AS "nome"
from PUB."cad-cli" WITH (NOLOCK)

