import time
import json
import os
from datetime import datetime
from selenium import webdriver # type: ignore
from selenium.webdriver.common.keys import Keys # type: ignore
from selenium.webdriver.common.by import By # type: ignore
from selenium.webdriver.support.ui import WebDriverWait # type: ignore
from selenium.webdriver.support import expected_conditions as EC # type: ignore
from selenium.webdriver.edge.service import Service # type: ignore
from selenium.webdriver.edge.options import Options as EdgeOptions # type: ignore
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, NoSuchElementException, ElementClickInterceptedException # type: ignore

# Configurações
TELEFONE_EQUATORIAL = "55999999999"  # Substitua pelo número correto da Equatorial (com DDD, sem + ou espaços)
EMAIL_CADASTRO = "teste@gmail.com" # Substitua pelo email que deseja usar no cadastro (pode ser o mesmo para todas as unidades)
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
    except:
        return [{"nome": "Exemplo", "codigo": "3006215636"}]

def iniciar_driver():
    options = EdgeOptions()
    prefs = {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "plugins.always_open_pdf_externally": True,
        "profile.default_content_setting_values.automatic_downloads": 1,
    }
    options.add_experimental_option("prefs", prefs)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    caminho_driver = os.path.join(BASE_DIR, "msedgedriver.exe")
    try:
        if os.path.exists(caminho_driver):
            return webdriver.Edge(service=Service(executable_path=caminho_driver), options=options)
        return webdriver.Edge(options=options)
    except Exception as e:
        print(f"Erro ao iniciar driver: {e}"); exit()

def encontrar_caixa_texto(driver):
    seletores = [
        'div[contenteditable="true"][data-tab="10"]',
        'footer div[contenteditable="true"]',
        '#main footer div.selectable-text[contenteditable="true"]',
        'div.copyable-text.selectable-text[contenteditable="true"]'
    ]
    for seletor in seletores:
        try:
            elemento = driver.find_element(By.CSS_SELECTOR, seletor)
            if elemento.is_displayed():
                return elemento
        except:
            continue
    return None

def enviar_texto(driver, texto):
    for tentativa in range(5):
        try:
            caixa_texto = encontrar_caixa_texto(driver)
            if not caixa_texto:
                # Se não achou, tenta esperar um pouco mais
                caixa_texto = WebDriverWait(driver, 10).until(
                    lambda d: encontrar_caixa_texto(d)
                )
            
            # Garante que o elemento está pronto para interação
            WebDriverWait(driver, 5).until(EC.visibility_of(caixa_texto))
            
            try:
                caixa_texto.click()
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].focus();", caixa_texto)
            
            time.sleep(0.5)
            
            # Limpa e envia usando comandos de teclado
            caixa_texto.send_keys(Keys.CONTROL + "a")
            caixa_texto.send_keys(Keys.BACKSPACE)
            time.sleep(0.3)
            caixa_texto.send_keys(texto)
            time.sleep(0.5)
            caixa_texto.send_keys(Keys.ENTER)
            
            try:
                WebDriverWait(driver, 8).until(
                    EC.presence_of_element_located((By.XPATH, f"//div[contains(@class, 'message-out')]//span[contains(text(), '{texto}')]"))
                )
            except:
                pass 
                
            print(f" [OK] Enviado: {texto}")
            time.sleep(2)
            return True
            
        except (StaleElementReferenceException, TimeoutException, NoSuchElementException) as e:
            print(f" [Tentativa {tentativa+1}] Erro ao interagir com a caixa de texto. Recarregando elemento...")
            time.sleep(2)
            continue
        except Exception as e:
            print(f" Erro inesperado ao enviar '{texto}': {e}")
            time.sleep(2)
            
    print(f" [FALHA] Não foi possível enviar a mensagem: {texto}")
    return False

def aguardar_estabilidade_bot(driver, texto_chave, timeout=60):
    """
    Aguarda o bot terminar de enviar mensagens.
    """
    print(f" Aguardando bot estabilizar em: '{texto_chave}'...")
    deadline = time.time() + timeout
    
    low = texto_chave.lower()
    xpath_msg = f"//div[contains(@class, 'message-in')]//*[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{low}')]"
    
    # 1. Espera o texto aparecer
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath_msg)))
    except:
        print(f" [!] Texto '{texto_chave}' não detectado no tempo limite.")
        return False

    # 2. Espera o bot parar de 'digitar' e de mandar novas mensagens
    print(" Texto detectado. Aguardando estabilidade do chat...")
    time.sleep(2) # Pausa inicial para o bot começar a próxima mensagem se houver
    
    while time.time() < deadline:
        try:
            # Verifica indicador de digitação
            digitando = driver.find_elements(By.XPATH, "//header//span[contains(text(), 'digitando')]")
            if digitando:
                time.sleep(2)
                continue
            
            # Verifica se o número de mensagens recebidas mudou
            msgs_antes = len(driver.find_elements(By.XPATH, "//div[contains(@class, 'message-in')]"))
            time.sleep(4) # Tempo de espera para o bot da Equatorial (que é lento entre blocos)
            msgs_depois = len(driver.find_elements(By.XPATH, "//div[contains(@class, 'message-in')]"))
            
            if msgs_antes == msgs_depois:
                print(" Chat estável.")
                return True
            else:
                print(" Bot ainda enviando mensagens...")
        except:
            time.sleep(1)
            
    return True

def clicar_download(driver, unidade=None, timeout=30):
    print(" Localizando arquivo para download...")
    time.sleep(1)

    # Lista de arquivos antes do clique para detectar o novo arquivo
    try:
        pre_files = set(os.listdir(DOWNLOAD_DIR))
    except Exception:
        pre_files = set()

    try:
        # Seletores para o botão de download ou o próprio documento
        seletores = [
            "(//div[contains(@class, 'message-in')]//div[@role='button' and @title])[last()]",
            "(//div[contains(@class, 'message-in')]//span[@data-icon='download'])[last()]",
            "(//div[contains(@class, 'message-in')]//div[contains(@aria-label, 'Download')])[last()]",
            "(//div[contains(@class, 'message-in')]//span[contains(text(), '.pdf')])[last()]"
        ]
        clicked = False
        for sel in seletores:
            try:
                btn = driver.find_element(By.XPATH, sel)
                # Tenta clicar via JS para evitar problemas de sobreposição
                driver.execute_script("arguments[0].click();", btn)
                clicked = True
                print(" Clique de download realizado!")
                break
            except:
                continue

        if not clicked:
            print(" Não foi possível localizar o botão de download para clicar.")
            return False

        # Aguarda o novo arquivo aparecer na pasta de downloads
        deadline = time.time() + timeout
        downloaded_file = None
        while time.time() < deadline:
            time.sleep(1)
            try:
                current_files = set(os.listdir(DOWNLOAD_DIR))
            except Exception:
                current_files = set()

            new_files = current_files - pre_files
            if not new_files:
                continue

            # Procura arquivos PDF definitivos entre os novos
            pdfs = [f for f in new_files if f.lower().endswith('.pdf')]
            if pdfs:
                # escolhe o mais recente
                pdfs.sort(key=lambda x: os.path.getmtime(os.path.join(DOWNLOAD_DIR, x)), reverse=True)
                downloaded_file = pdfs[0]
                break

            # Se houver .crdownload/.part, espera que seja concluído e apareça o .pdf
            in_progress = [f for f in new_files if f.lower().endswith('.crdownload') or f.lower().endswith('.part')]
            if in_progress:
                # espera mais algumas iterações até o .pdf aparecer
                continue

        if not downloaded_file:
            # tenta detectar qualquer PDF novo mesmo que não estivesse na diferença (em casos raros)
            all_pdfs = [f for f in os.listdir(DOWNLOAD_DIR) if f.lower().endswith('.pdf')]
            candidates = [f for f in all_pdfs if f not in pre_files]
            if candidates:
                candidates.sort(key=lambda x: os.path.getmtime(os.path.join(DOWNLOAD_DIR, x)), reverse=True)
                downloaded_file = candidates[0]

        if not downloaded_file:
            print(" Tempo esgotado aguardando o download do arquivo.")
            return False

        src = os.path.join(DOWNLOAD_DIR, downloaded_file)

        # Gera nome seguro a partir da unidade (se fornecida)
        if unidade and isinstance(unidade, dict):
            nome_raw = unidade.get('nome', '').strip()
            codigo = unidade.get('codigo', '').strip()
            # remove caracteres ilegais do nome do arquivo
            safe_nome = ''.join(c for c in nome_raw if c.isalnum() or c in ' _-').strip()
            if safe_nome == '':
                safe_nome = 'unidade'
            new_basename = f"{HOJE}_{safe_nome}_{codigo}.pdf" if codigo else f"{HOJE}_{safe_nome}.pdf"
        else:
            new_basename = f"{HOJE}_{downloaded_file}"

        dst = os.path.join(DOWNLOAD_DIR, new_basename)
        base, ext = os.path.splitext(dst)
        counter = 1
        while os.path.exists(dst):
            dst = f"{base}({counter}){ext}"
            counter += 1

        # Aguarda arquivo estar estável (tamanho não mudar) antes de renomear
        stable_deadline = time.time() + 5
        try:
            prev_size = -1
            while time.time() < stable_deadline:
                size = os.path.getsize(src)
                if size == prev_size:
                    break
                prev_size = size
                time.sleep(0.4)
        except Exception:
            pass

        os.rename(src, dst)
        print(f" Arquivo renomeado para: {os.path.basename(dst)}")
        return True

    except Exception as e:
        print(f" Erro no clicar_download: {e}")
        return False

def main():
    matriculas = carregar_dados()
    driver = iniciar_driver()
    driver.get("https://web.whatsapp.com")
    print("\n" + "="*50)
    input(" AÇÃO: Escaneie o QR Code e espere as conversas carregarem. Então pressione ENTER...")
    print("="*50 + "\n")

    # Força a abertura do chat da Equatorial
    driver.get(f"https://web.whatsapp.com/send?phone={TELEFONE_EQUATORIAL}")
    
    try:
        WebDriverWait(driver, 60).until(lambda d: encontrar_caixa_texto(d))
        print(" Chat da Equatorial carregado e pronto!")
    except:
        print(" Erro ao carregar o chat. Verifique se o número está correto ou se o WhatsApp Web carregou.")
        driver.quit(); return

    for unidade in matriculas:
        print(f"\n>>> PROCESSANDO: {unidade['nome']} ({unidade['codigo']})")
        
        # Início do Fluxo
        if not enviar_texto(driver, "Oi"): continue
        
        if not aguardar_estabilidade_bot(driver, "Segunda via de Fatura"): continue
        if not enviar_texto(driver, "6"): continue
        
        if not aguardar_estabilidade_bot(driver, "informe o CPF"): continue
        if not enviar_texto(driver, unidade['codigo']): continue
            
        if not aguardar_estabilidade_bot(driver, "deseja atendimento"): continue
        if not enviar_texto(driver, "Sim"): continue
            
        if not aguardar_estabilidade_bot(driver, "Referência"): continue
        if not enviar_texto(driver, "1"): continue
            
        if not aguardar_estabilidade_bot(driver, "Pagar com boleto"): continue
        if not enviar_texto(driver, "2"): continue
            
        if not aguardar_estabilidade_bot(driver, "Informe o email"): continue
        if not enviar_texto(driver, EMAIL_CADASTRO): continue
            
        if aguardar_estabilidade_bot(driver, "Aqui está a sua fatura"):
            clicar_download(driver, unidade)
            print(" Aguardando 10s para o download processar...")
            time.sleep(10)

        # Finalização da conversa para limpar o estado do bot
        if aguardar_estabilidade_bot(driver, "outra conta"): enviar_texto(driver, "Não")
        if aguardar_estabilidade_bot(driver, "ajudar com mais"): enviar_texto(driver, "Não")
        if aguardar_estabilidade_bot(driver, "achou da nossa conversa"): enviar_texto(driver, "4")

        print(f" [SUCESSO] Unidade {unidade['nome']} concluída.")
        time.sleep(5)

    print("\n TUDO PRONTO! Verifique sua pasta de downloads.")
    driver.quit()

if __name__ == "__main__":
    main()
