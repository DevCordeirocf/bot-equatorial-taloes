# Automação de Faturas - Equatorial Energia (WhatsApp)

Automação desenvolvida em **Python** com **Selenium** para coletar faturas (PDFs) via atendimento do WhatsApp da Equatorial Energia. Ideal para gestão de condomínios, com salvamento automático e organização por data.

---

## Funcionalidades principais

- **Interação com o bot da Equatorial** respeitando tempos de resposta.
- **Espera explícita** com `WebDriverWait` para fluxos mais estáveis.
- **Organização automática**: pastas diárias em `downloads/YYYY-MM-DD/`.
- **Login via QR Code** do WhatsApp Web (Edge).

## Tecnologias

- **Python 3.x**
- **Selenium WebDriver**
- **Microsoft Edge** + **msedgedriver.exe**

## Pré-requisitos

1. Python instalado (3.x)
2. Microsoft Edge instalado
3. Baixe o Edge WebDriver compatível: https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/
   - Coloque `msedgedriver.exe` na raiz do projeto ou no PATH.

## Instalação

1. Clone o repositório:

```powershell
git clone https://github.com/seu-usuario/nome-do-repo.git
```

2. Instale as dependências:

```powershell
pip install -r requirements.txt
```

> Se preferir instalar manualmente apenas o Selenium:

```powershell
pip install selenium
```

---

## Configuração dos Dados

Crie (ou confirme) o arquivo `data/matriculas.json` com a estrutura abaixo para indicar as unidades/consumidores que o robô deve processar:

```json
[
  {
    "nome": "Bloco 1 Apt 101",
    "codigo": "0000000000"
  },
  {
    "nome": "Bloco 1 Apt 102",
    "codigo": "1111111111"
  }
]
```

- **Local do arquivo:** `data/matriculas.json`
- **Formato:** array de objetos com `nome` e `codigo` (string).

---

## Como Usar

1. Abra um terminal na pasta do projeto.
2. Execute o script principal:

```powershell
python main.py
# (ou `python src/bot.py` / outro nome se você alterou o entrypoint)
```

3. Uma janela do Microsoft Edge será aberta no WhatsApp Web.
4. Escaneie o QR Code com seu celular para logar.
5. Aguarde até que a lista de conversas carregue completamente.
6. Localize e clique na conversa com a Equatorial (ou no atendimento/contato oficial que responde com faturas) para abri-la — o robô envia mensagens para a conversa ativa.
7. Assim que a conversa estiver aberta e visível no WhatsApp Web, volte ao terminal e pressione **ENTER** para iniciar o fluxo automático. Pressionar ENTER serve como confirmação de que a conversa correta está selecionada; o bot só começará após esse passo.
8. O robô então:
   - enviará os códigos do arquivo `data/matriculas.json` um a um,
   - aguardará a resposta e o envio das faturas (PDFs),
   - fará o download automático dos arquivos para `downloads/YYYY-MM-DD/`.
9. Durante a execução, não mexa no mouse ou teclado na janela do navegador e mantenha a conexão estável — interações manuais podem atrapalhar o fluxo.
10. Para interromper a execução, pressione Ctrl+C no terminal.

Os arquivos PDF serão salvos automaticamente na pasta `downloads/` organizada por data.

---

## Notas Importantes

> **Antes de iniciar:** Depois de abrir a conversa correta com a Equatorial no WhatsApp Web, volte ao terminal e pressione **ENTER** para confirmar e iniciar o fluxo automático — o robô aguardará esse comando e só começará após a confirmação.

> **Interferência Humana:** Não mexa no mouse ou teclado na janela do navegador enquanto o bot estiver operando — isso pode interromper a automação.

> **Evite execuções em massa:** Não rode o script centenas de vezes seguidas em curto período, pois o WhatsApp pode considerar comportamento de spam e bloquear temporariamente o número.

> **Uso responsável:** Ferramenta criada para **automação administrativa**. Respeite políticas de privacidade e termos de uso do serviço.

---

## Dicas e Solução de Problemas

- Se o WhatsApp Web não carregar, verifique sua conexão e se o Edge foi iniciado corretamente.
- Mantenha o `msedgedriver.exe` na versão compatível com seu Edge.
- Logs e saídas aparecem no terminal — acompanhe-os para identificar passo a passo.

---

## Contribuição

Se quiser contribuir: abra uma issue ou envie um pull request descrevendo a melhoria.

---

_Desenvolvido para automação administrativa e de tarefas repetitivas — use com responsabilidade._
