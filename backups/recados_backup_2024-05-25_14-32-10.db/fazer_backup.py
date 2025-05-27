import shutil
import os
from datetime import datetime

# Nome do arquivo original
banco_origem = 'recados.db'

# Pasta de destino
pasta_backup = 'backups'

# Criar a pasta backups se não existir
os.makedirs(pasta_backup, exist_ok=True)

# Criar nome do arquivo com timestamp
agora = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
arquivo_backup = f'recados_backup_{agora}.db'

# Caminho completo
caminho_backup = os.path.join(pasta_backup, arquivo_backup)

# Fazer a cópia
shutil.copy2(banco_origem, caminho_backup)

print(f'✅ Backup criado com sucesso: {caminho_backup}')
