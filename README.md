```md
# Bot Equatorial – Versão Atualizada

Automação em Python utilizando Selenium e Microsoft Edge para solicitar segunda via de faturas da Equatorial via WhatsApp Web, com download automático e organização dos arquivos.

Este repositório é um fork da versão original, com melhorias de estabilidade, tratamento de erros e controle mais confiável do fluxo de mensagens e downloads.

---

## Principais Atualizações em Relação ao Projeto Original

### 1. Envio de mensagens mais robusto

Na versão original, o envio de mensagens utilizava apenas um seletor fixo para localizar a caixa de texto do WhatsApp Web e não possuía múltiplas tentativas ou tratamento detalhado de exceções.

Nesta versão:

- Foram adicionados múltiplos seletores alternativos para localizar a caixa de texto.
- O envio de mensagem possui até 5 tentativas automáticas.
- Há tratamento para:
  - `StaleElementReferenceException`
  - `TimeoutException`
  - `NoSuchElementException`
  - `ElementClickInterceptedException`
- O campo é limpo antes do envio (`CTRL + A` + `BACKSPACE`).
- É feita uma tentativa de confirmação visual da mensagem enviada.

Isso reduz falhas causadas por mudanças no DOM ou por instabilidade do WhatsApp Web.

---

### 2. Espera inteligente pela resposta do bot

Na versão original, grande parte do fluxo dependia de `time.sleep()` e de um texto fixo específico para identificar novas mensagens.

Nesta versão foi implementada a função `aguardar_estabilidade_bot()`, que:

- Aguarda um texto-chave configurável aparecer no chat.
- Verifica se o indicador “digitando” está ativo.
- Monitora se novas mensagens continuam chegando.
- Aguarda a estabilização do chat antes de continuar o fluxo.

O objetivo é reduzir dependência de tempos fixos e tornar o processo mais confiável.

---

### 3. Controle real do download de PDFs

Na versão original, o script apenas aguardava um tempo fixo após solicitar o envio da fatura, sem verificar se o arquivo foi realmente baixado.

Nesta versão:

- O sistema detecta os arquivos existentes antes do clique.
- Após o clique, monitora a pasta de download.
- Aguarda a conclusão de arquivos temporários (`.crdownload` ou `.part`).
- Verifica a estabilidade do tamanho do arquivo antes de renomear.
- Renomeia automaticamente o PDF no formato:

```

YYYY-MM-DD_NOME_UNIDADE_CODIGO.pdf

```

- Evita sobrescrita adicionando contador incremental quando necessário.
- Remove caracteres inválidos do nome do arquivo.

Isso garante que o arquivo esteja completo antes de finalizar o processo.

---

### 4. Melhor organização do fluxo

O fluxo foi reorganizado para depender de textos esperados no chat, em vez de apenas atrasos fixos. O encerramento da conversa também foi estruturado para reduzir interferência no processamento da próxima matrícula.

---

## Estrutura do Projeto

```

bot-equatorial/
│
├── data/
│   └── matriculas.json
│
├── downloads/
│   └── YYYY-MM-DD/
│
├── src/
│   └── main.py
│
├── msedgedriver.exe
└── README.md

```

---

## Configuração

### 1. Instalar dependências

Se houver `requirements.txt`:

```

pip install -r requirements.txt

```

Caso contrário:

```

pip install selenium

```

---

### 2. WebDriver

Baixe a versão do Microsoft Edge WebDriver compatível com seu navegador e coloque o arquivo `msedgedriver.exe` na raiz do projeto.

---

### 3. Configurar matrículas

Arquivo:

```

data/matriculas.json

````

Exemplo:

```json
[
  {
    "nome": "Bloco 1 Apt 101",
    "codigo": "1234567891"
  },
  {
    "nome": "Bloco 1 Apt 102",
    "codigo": "1234567890"
  }
]
````

---

### 4. Configurar telefone e e-mail

No início do script:

```python
TELEFONE_EQUATORIAL = "5599999999999"
EMAIL_CADASTRO = "seuemail@email.com"
```

---

## Execução

```
python main.py
```

Passos:

1. O navegador abrirá o WhatsApp Web.
2. Escaneie o QR Code.
3. Aguarde as conversas carregarem.
4. Pressione ENTER no terminal.
5. O script executará o fluxo automaticamente para cada matrícula.

---

## Observações

* O funcionamento depende da estrutura atual do WhatsApp Web.
* Mudanças significativas no layout podem exigir atualização dos seletores.
* É recomendável manter o WebDriver atualizado.
* O projeto é uma automação baseada em interface web e pode ser impactado por mudanças no comportamento do bot da Equatorial.

```
```
