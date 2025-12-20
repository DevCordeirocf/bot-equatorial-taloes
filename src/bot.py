import time
import json
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

# Imports para espera inteligente
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options as EdgeOptions

# Configurações principais
TELEFONE_EQUATORIAL = "559820550116" 
EMAIL_CADASTRO = "example@gmail.com"

# --- CONFIGURAÇÃO DE CAMINHOS ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'matriculas.json')

HOJE = datetime.now().strftime('%Y-%m-%d')
DOWNLOAD_DIR = os.path.join(BASE_DIR, 'downloads', HOJE)

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

def carregar_dados():
    try:
        with open(DATA_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERRO: Arquivo não encontrado em {DATA_PATH}")
        exit()

def iniciar_driver():
    options = EdgeOptions()
    prefs = {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True, 
        "profile.default_content_settings.popups": 0
    }
    options.add_experimental_option("prefs", prefs)
    
    caminho_driver = os.path.join(BASE_DIR, "msedgedriver.exe")
    
    if not os.path.exists(caminho_driver):
        print("\n ERRO FATAL: O arquivo 'msedgedriver.exe' não está na pasta do projeto!")
        exit()

    try:
        service = Service(executable_path=caminho_driver)
        driver = webdriver.Edge(service=service, options=options)
        return driver
    except Exception as e:
        print(f"\n ERRO ao abrir o Edge: {e}")
        exit()

def enviar_texto(driver, texto):
    try:
        caixa_texto = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[contenteditable="true"][data-tab="10"]'))
        )
        caixa_texto.click()
        caixa_texto.send_keys(texto)
        caixa_texto.send_keys(Keys.ENTER)
    except Exception as e:
        print(f" Erro ao enviar '{texto}': {e}")

# --- NOVA LÓGICA DE ESPERA ---
def contar_avisos_existentes(driver):
    """Conta quantas vezes a mensagem da ANEEL já está no chat (histórico)"""
    try:
        elementos = driver.find_elements(By.XPATH, "//*[contains(text(), '1095/2024')]")
        return len(elementos)
    except:
        return 0

def aguardar_novo_aviso(driver, qtd_anterior):
    """
    Espera até que o número de avisos na tela seja MAIOR que a quantidade anterior.
    Isso garante que estamos pegando a NOVA mensagem, e não a velha.
    """
    print(" Aguardando NOVA mensagem da ANEEL...")
    
    def condicao_nova_msg(d):
        atuais = d.find_elements(By.XPATH, "//*[contains(text(), '1095/2024')]")
        return len(atuais) > qtd_anterior

    try:
        WebDriverWait(driver, 30).until(condicao_nova_msg)
        print(" Novo aviso detectado! (Bot terminou o envio)")
        time.sleep(2) # Pausa extra para garantir que o MENU apareceu depois do aviso
    except:
        print(" Tempo esgotado. O bot pode ter mudado o texto ou não respondeu.")

def processar_pagamento_e_download(driver):
    time.sleep(4) 
    enviar_texto(driver, "2")
    time.sleep(4) 
    enviar_texto(driver, EMAIL_CADASTRO)
    print(f"  Aguardando PDF na pasta: downloads/{HOJE} (15s)...")
    time.sleep(15) 

def main():
    matriculas = carregar_dados()
    print(f"{len(matriculas)} matrículas carregadas.")

    driver = iniciar_driver()

    print(" Abrindo WhatsApp Web para login...")
    driver.get("https://web.whatsapp.com")
    
    print("\n" + "="*50)
    input("AÇÃO NECESSÁRIA: \n1. Escaneie o QR Code.\n2. Espere aparecer a lista de conversas.\n3. Só depois disso, pressione ENTER aqui...")
    print("="*50 + "\n")

    print(" Indo para o chat da Equatorial...")
    link_wpp = f"https://web.whatsapp.com/send?phone={TELEFONE_EQUATORIAL}"
    driver.get(link_wpp)
    
    # Espera a caixa de texto aparecer para garantir que o chat carregou
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[contenteditable="true"][data-tab="10"]'))
        )
        print(" Chat carregado com sucesso!")
    except:
        print(" O chat demorou para carregar, mas vamos tentar seguir...")

    # --- INÍCIO DO LOOP ---
    for unidade in matriculas:
        print(f"\n PROCESSANDO: {unidade['nome']} ({unidade['codigo']})")
        
        # 1. Antes de dar Oi, vê quantos avisos velhos têm na tela
        qtd_antes = contar_avisos_existentes(driver)
        
        # 2. Manda o Oi
        enviar_texto(driver, "Oi") 
        
        # 3. Espera aparecer um aviso NOVO (qtd > qtd_antes)
        aguardar_novo_aviso(driver, qtd_antes)
        
        # 4. Segue o fluxo
        enviar_texto(driver, "6")
        time.sleep(5) 
        
        enviar_texto(driver, unidade['codigo'])
        time.sleep(6) 
        
        enviar_texto(driver, "sim")
        print("    Aguardando busca de faturas...")
        time.sleep(8) 
        
        print("    Baixando Fatura 1...")
        enviar_texto(driver, "1")
        processar_pagamento_e_download(driver)
        
        enviar_texto(driver, "sim")
        time.sleep(6)
        
        print("   Baixando Fatura 2...")
        enviar_texto(driver, "2")
        processar_pagamento_e_download(driver)
        
        # --- ENCERRAMENTO ---
        print("  Finalizando conversa deste bloco...")
        enviar_texto(driver, "não")
        time.sleep(4)
        enviar_texto(driver, "não") 
        time.sleep(4)
        enviar_texto(driver, "4")   
        
        print("  Aguardando mensagens finais (10s)...")
        time.sleep(10)
        
        print(f" Bloco {unidade['nome']} concluído!")

    print("\n TUDO PRONTO! Verifique a pasta 'downloads'.")

if __name__ == "__main__":
    main()