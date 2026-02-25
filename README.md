Aqui está uma proposta de README.md focada em clareza, organização técnica e legibilidade para o GitHub, evitando o uso de ícones e mantendo um tom profissional.

Bot Equatorial – Versão Atualizada
Automação em Python desenvolvida com Selenium e Microsoft Edge para a solicitação automática de segunda via de faturas da Equatorial via WhatsApp Web. O projeto inclui gerenciamento inteligente de downloads e organização sistemática de arquivos.

Este repositório é um fork da versão original, implementando melhorias críticas em estabilidade, tratamento de exceções e controle de fluxo de mensagens.

Principais Atualizações
1. Envio de Mensagens Robusto
A versão anterior utilizava seletores fixos e não possuía tratamento para instabilidades do DOM. Esta versão implementa:

Múltiplos seletores alternativos para localizar a caixa de texto.

Sistema de retentativa: até 5 tentativas automáticas em caso de erro.

Tratamento de exceções específicas: StaleElementReferenceException, TimeoutException, NoSuchElementException e ElementClickInterceptedException.

Limpeza de buffer: Executa o comando CTRL + A + BACKSPACE antes de cada envio.

Confirmação visual: Verificação de entrega da mensagem no chat.

2. Espera Inteligente (Smart Wait)
Substituição de atrasos fixos (time.sleep) pela função aguardar_estabilidade_bot(), que monitora:

Presença de textos-chave configuráveis no chat.

Status do indicador "digitando" do bot.

Fluxo de novas mensagens para garantir que o chat estabilizou antes de prosseguir.

3. Controle de Download e Integridade
O script agora valida o ciclo de vida do arquivo PDF:

Monitoramento de pasta: Detecta novos arquivos e ignora temporários (.crdownload ou .part).

Validação de escrita: Verifica se o tamanho do arquivo parou de oscilar antes de manipulá-lo.

Padronização de nomenclatura: Renomeia arquivos para o formato YYYY-MM-DD_NOME_UNIDADE_CODIGO.pdf.

Sanitização: Remove caracteres inválidos e evita sobrescrita com contadores incrementais.

Estrutura do Projeto
Plaintext
bot-equatorial/
│
├── data/
│   └── matriculas.json      # Dados das unidades consumidoras
│
├── downloads/
│   └── YYYY-MM-DD/          # Faturas baixadas organizadas por data
│
├── src/
│   └── main.py              # Script principal
│
├── msedgedriver.exe         # WebDriver do Microsoft Edge
└── README.md
Configuração
1. Instalação de Dependências
Caso o projeto possua um arquivo de requisitos:

Bash
pip install -r requirements.txt
Ou instale manualmente a biblioteca Selenium:

Bash
pip install selenium
2. WebDriver
Baixe o Microsoft Edge WebDriver compatível com a versão instalada no seu navegador e coloque o executável msedgedriver.exe na raiz do projeto.

3. Configuração de Dados
Edite o arquivo data/matriculas.json seguindo o modelo:

JSON
[
  {
    "nome": "Bloco 1 Apt 101",
    "codigo": "3006215636"
  },
  {
    "nome": "Bloco 1 Apt 102",
    "codigo": "1234567890"
  }
]
No início do script main.py, configure suas credenciais:

Python
TELEFONE_EQUATORIAL = "559820550116"
EMAIL_CADASTRO = "seuemail@email.com"
Execução
Execute o script principal:

Bash
python main.py
O navegador Edge abrirá no WhatsApp Web. Escaneie o QR Code.

Aguarde o carregamento total das conversas.

Volte ao terminal e pressione ENTER.

O bot processará cada matrícula cadastrada sequencialmente.

Observações Técnicas
O projeto depende inteiramente da estrutura HTML atual do WhatsApp Web. Mudanças globais na interface podem exigir a atualização dos seletores CSS/XPath.

É recomendável manter o WebDriver e o navegador sempre na mesma versão para evitar erros de compatibilidade.

Por se tratar de uma automação baseada em interface (UI), o desempenho pode variar de acordo com a velocidade da conexão e a latência de resposta do bot da Equatorial.
