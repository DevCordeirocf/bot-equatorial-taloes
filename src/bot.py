import time
import json
import os
import csv
import re
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
# Caminho para salvar a sessão do WhatsApp (evita escanear QR Code toda vez)
SESSION_DIR = os.path.join(BASE_DIR, 'sessao_whatsapp')

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

if not os.path.exists(SESSION_DIR):
    os.makedirs(SESSION_DIR)

def carregar_dados():
    try:
        with open(DATA_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return [{"nome": "Exemplo", "codigo": "3006215636"}]

def iniciar_driver():
    options = EdgeOptions()
    
    # Configuração de Perfil de Usuário para Persistência de Sessão
    options.add_argument(f"user-data-dir={SESSION_DIR}")
    options.add_argument("profile-directory=Default")
    
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
                caixa_texto = WebDriverWait(driver, 10).until(
                    lambda d: encontrar_caixa_texto(d)
                )
            
            WebDriverWait(driver, 5).until(EC.visibility_of(caixa_texto))
            
            try:
                caixa_texto.click()
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].focus();", caixa_texto)
            
            time.sleep(0.5)
            
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
    print(f" Aguardando bot estabilizar em: '{texto_chave}'...")
    deadline = time.time() + timeout
    
    low = texto_chave.lower()
    xpath_msg = f"//div[contains(@class, 'message-in')]//*[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{low}')]"
    
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath_msg)))
    except:
        print(f" [!] Texto '{texto_chave}' não detectado no tempo limite.")
        return False

    print(" Texto detectado. Aguardando estabilidade do chat...")
    time.sleep(2)
    
    while time.time() < deadline:
        try:
            digitando = driver.find_elements(By.XPATH, "//header//span[contains(text(), 'digitando')]")
            if digitando:
                time.sleep(2)
                continue
            
            msgs_antes = len(driver.find_elements(By.XPATH, "//div[contains(@class, 'message-in')]"))
            time.sleep(4)
            msgs_depois = len(driver.find_elements(By.XPATH, "//div[contains(@class, 'message-in')]"))
            
            if msgs_antes == msgs_depois:
                print(" Chat estável.")
                return True
            else:
                print(" Bot ainda enviando mensagens...")
        except:
            time.sleep(1)
            
    return True

def extrair_dados_fatura(driver):
    """
    Extrai Referência, Valor e Vencimento da última mensagem do bot.
    """
    try:
        mensagens = driver.find_elements(By.XPATH, "//div[contains(@class, 'message-in')]//span")
        for msg in reversed(mensagens):
            texto = msg.text
            if "Referência:" in texto and "Valor:" in texto and "Vencimento:" in texto:
                ref = re.search(r"Referência:\s*(\d{2}/\d{4})", texto)
                val = re.search(r"Valor:\s*R\$\s*([\d,.]+)", texto)
                ven = re.search(r"Vencimento:\s*(\d{2}/\d{2}/\d{4})", texto)
                
                return {
                    "referencia": ref.group(1) if ref else "N/A",
                    "valor": val.group(1) if val else "N/A",
                    "vencimento": ven.group(1) if ven else "N/A"
                }
    except Exception as e:
        print(f" Erro ao extrair dados da fatura: {e}")
    return {"referencia": "N/A", "valor": "N/A", "vencimento": "N/A"}

def extrair_codigo_pix(driver):
    """
    Extrai o código Pix Copia e Cola da última mensagem.
    """
    try:
        mensagens = driver.find_elements(By.XPATH, "//div[contains(@class, 'message-in')]//span")
        for msg in reversed(mensagens):
            texto = msg.text.strip()
            if texto.startswith("000201") and len(texto) > 100:
                return texto
    except Exception as e:
        print(f" Erro ao extrair código Pix: {e}")
    return "N/A"

def salvar_dados_csv(dados):
    caminho_csv = os.path.join(DOWNLOAD_DIR, f"faturas_equatorial_{HOJE}.csv")
    arquivo_existe = os.path.exists(caminho_csv)
    
    try:
        with open(caminho_csv, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=["nome", "codigo", "referencia", "valor", "vencimento", "pix"], delimiter=';')
            if not arquivo_existe:
                writer.writeheader()
            writer.writerow(dados)
        print(f" [OK] Dados salvos no CSV: {caminho_csv}")
    except Exception as e:
        print(f" Erro ao salvar no CSV: {e}")

def clicar_download(driver, unidade=None, timeout=30):
    print(" Localizando arquivo para download...")
    time.sleep(1)

    try:
        pre_files = set(os.listdir(DOWNLOAD_DIR))
    except Exception:
        pre_files = set()

    try:
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
                driver.execute_script("arguments[0].click();", btn)
                clicked = True
                print(" Clique de download realizado!")
                break
            except:
                continue

        if not clicked:
            print(" Não foi possível localizar o botão de download para clicar.")
            return False

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

            pdfs = [f for f in new_files if f.lower().endswith('.pdf')]
            if pdfs:
                pdfs.sort(key=lambda x: os.path.getmtime(os.path.join(DOWNLOAD_DIR, x)), reverse=True)
                downloaded_file = pdfs[0]
                break

        if not downloaded_file:
            all_pdfs = [f for f in os.listdir(DOWNLOAD_DIR) if f.lower().endswith('.pdf')]
            candidates = [f for f in all_pdfs if f not in pre_files]
            if candidates:
                candidates.sort(key=lambda x: os.path.getmtime(os.path.join(DOWNLOAD_DIR, x)), reverse=True)
                downloaded_file = candidates[0]

        if not downloaded_file:
            print(" Tempo esgotado aguardando o download do arquivo.")
            return False

        src = os.path.join(DOWNLOAD_DIR, downloaded_file)

        if unidade and isinstance(unidade, dict):
            nome_raw = unidade.get('nome', '').strip()
            codigo = unidade.get('codigo', '').strip()
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

def apagar_conversa(driver):
    """
    Apaga a conversa inteira com a Equatorial (Opção C).
    """
    print(" Iniciando limpeza da conversa...")
    try:
        # 1. Clica no menu do chat (três pontinhos ou seta para baixo no cabeçalho)
        try:
            menu_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//header//div[@role='button' and @title='Menu']"))
            )
            menu_btn.click()
        except:
            # Tenta seletor alternativo
            menu_btn = driver.find_element(By.XPATH, "//header//span[@data-icon='menu']")
            driver.execute_script("arguments[0].click();", menu_btn)
        
        time.sleep(1)
        
        # 2. Clica em "Apagar conversa"
        apagar_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and .//div[contains(text(), 'Apagar conversa')]]"))
        )
        apagar_btn.click()
        
        time.sleep(1)
        
        # 3. Confirma a exclusão no modal
        confirmar_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and .//div[text()='Apagar conversa']]"))
        )
        confirmar_btn.click()
        
        print(" [LIMPEZA] Conversa apagada com sucesso!")
        time.sleep(3)
        return True
    except Exception as e:
        print(f" [!] Erro ao apagar conversa: {e}")
        return False

def main():
    print("\n" + "="*50)
    print(" BOT EQUATORIAL - ATUALIZADO")
    print("="*50)
    print(" Escolha o que deseja fazer:")
    print(" 1 - Baixar Boletos (PDF)")
    print(" 2 - Extrair apenas dados do Pix (Excel/CSV)")
    opcao_global = input("\n Digite a opção desejada (1 ou 2): ").strip()
    
    if opcao_global not in ['1', '2']:
        print(" Opção inválida. Saindo...")
        return

    matriculas = carregar_dados()
    driver = iniciar_driver()
    driver.get("https://web.whatsapp.com")
    
    print("\n" + "="*50)
    print(" Verificando conexão do WhatsApp...")
    
    # Aguarda o WhatsApp carregar. Se não estiver logado, pede para escanear.
    try:
        # Se aparecer a caixa de busca ou de texto, é porque já está logado
        WebDriverWait(driver, 15).until(lambda d: encontrar_caixa_texto(d) or d.find_elements(By.XPATH, "//div[@id='pane-side']"))
        print(" Conectado automaticamente via sessão salva!")
    except:
        input(" AÇÃO: Escaneie o QR Code e espere as conversas carregarem. Então pressione ENTER...")
    
    print("="*50 + "\n")

    for unidade in matriculas:
        print(f"\n>>> PROCESSANDO: {unidade['nome']} ({unidade['codigo']})")
        
        # Abre o chat diretamente a cada unidade para garantir foco
        driver.get(f"https://web.whatsapp.com/send?phone={TELEFONE_EQUATORIAL}")
        
        try:
            WebDriverWait(driver, 60).until(lambda d: encontrar_caixa_texto(d))
            print(" Chat da Equatorial carregado e pronto!")
        except:
            print(" Erro ao carregar o chat. Pulando unidade...")
            continue

        if not enviar_texto(driver, "Oi"): continue
        if not aguardar_estabilidade_bot(driver, "Segunda via de Fatura"): continue
        if not enviar_texto(driver, "6"): continue
        
        if not aguardar_estabilidade_bot(driver, "informe o CPF"): continue
        if not enviar_texto(driver, unidade['codigo']): continue
            
        if not aguardar_estabilidade_bot(driver, "deseja atendimento"): continue
        if not enviar_texto(driver, "Sim"): continue
            
        if not aguardar_estabilidade_bot(driver, "Referência"): continue
        dados_fatura = extrair_dados_fatura(driver)
        if not enviar_texto(driver, "1"): continue
            
        if not aguardar_estabilidade_bot(driver, "Como você prefere"): continue
        
        if opcao_global == '1':
            if not enviar_texto(driver, "2"): continue # 2 - Pagar com boleto
            if not aguardar_estabilidade_bot(driver, "Informe o email"): continue
            if not enviar_texto(driver, EMAIL_CADASTRO): continue
            
            if aguardar_estabilidade_bot(driver, "Aqui está a sua fatura"):
                clicar_download(driver, unidade)
                print(" Aguardando 10s para o download processar...")
                time.sleep(10)
        else:
            if not enviar_texto(driver, "4"): continue # 4 - Pagar com pix
            if aguardar_estabilidade_bot(driver, "código Pix"):
                time.sleep(2)
                codigo_pix = extrair_codigo_pix(driver)
                
                dados_completos = {
                    "nome": unidade['nome'],
                    "codigo": unidade['codigo'],
                    "referencia": dados_fatura['referencia'],
                    "valor": dados_fatura['valor'],
                    "vencimento": dados_fatura['vencimento'],
                    "pix": codigo_pix
                }
                salvar_dados_csv(dados_completos)

        # Fluxo de finalização
        if aguardar_estabilidade_bot(driver, "outra conta"): enviar_texto(driver, "Não")
        if aguardar_estabilidade_bot(driver, "ajudar com mais"): enviar_texto(driver, "Não")
        if aguardar_estabilidade_bot(driver, "achou da nossa conversa"): enviar_texto(driver, "5")
        if aguardar_estabilidade_bot(driver, "conseguiu resolver"): enviar_texto(driver, "3")

        print(f" [SUCESSO] Unidade {unidade['nome']} concluída.")
        
        # LIMPEZA TOTAL (Opção C)
        apagar_conversa(driver)
        
        time.sleep(5)

    print("\n TUDO PRONTO! Verifique sua pasta de downloads.")
    driver.quit()

if __name__ == "__main__":
    main()
