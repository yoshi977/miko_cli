import argparse
import nmap
import requests
import time
import sys
import os
import pyfiglet
from openai import OpenAI

# --- НАСТРОЙКИ ---
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
MODEL_NAME = "qwen2.5:3b"

# --- БАННЕР И КРАСИВЫЙ ВЫВОД ---
def print_banner():
    # Очищаем экран (для Windows)
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Генерируем логотип
    banner = pyfiglet.figlet_format("Miko CLI")
    print("\033[96m" + banner + "\033[0m") # \033[96m делает текст бирюзовым
    
    print("\033[93m" + "="*55 + "\033[0m") # Желтая линия
    print("\033[92m" + "       AI-Powered Pentest Scanner (v1.0)" + "\033[0m") # Зеленая надпись
    print("\033[93m" + "="*55 + "\033[0m")
    print("\n\033[97m[*] Использование:\033[0m python kimo_cli.py -t <target> [-l login] [-p pass] [-c cookie]")
    print("\033[97m[*] Пример:\033[0m python kimo_cli.py -t testphp.vulnweb.com")
    print("\n")
    time.sleep(1) # Небольшая пауза для эффекта

# --- ФУНКЦИЯ АВТОРИЗАЦИИ ---
def check_auth(target, login, password, cookies):
    print(f"\033[94m[*] Проверяю авторизацию на {target}...\033[0m")
    
    headers = {}
    if cookies:
        headers['Cookie'] = cookies
        print(f"\033[92m[*] Использую куки: {cookies}\033[0m")
    
    if login and password:
        print(f"\033[94m[*] Пробую войти под логином: {login}\033[0m")
        data = {"username": login, "password": password}
        try:
            response = requests.post(target, data=data, headers=headers, timeout=5)
            if response.status_code == 200:
                print("\033[92m[+] Успешный вход (страница ответила 200 OK).\033[0m")
                return response.cookies.get_dict()
        except Exception as e:
            print(f"\033[91m[-] Ошибка авторизации: {e}\033[0m")
            
    return headers.get('Cookie', '')

# --- ФУНКЦИЯ ОТПРАВКИ В ИИ ---
def generate_report(target, results):
    print("\033[94m[*] Нейросеть пишет отчет...\033[0m")
    prompt = f"Ты пентестер. Напиши краткий отчет для {target}. Данные:\n{results}"
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Ошибка ИИ: {e}"

# --- ГЛАВНАЯ ФУНКЦИЯ ---
def main():
    print_banner() # Показываем логотип
    
    parser = argparse.ArgumentParser(description="Miko CLI - AI Pentest Scanner")
    parser.add_argument("-t", "--target", required=True, help="Целевой URL или IP")
    parser.add_argument("-l", "--login", help="Логин")
    parser.add_argument("-p", "--password", help="Пароль")
    parser.add_argument("-c", "--cookie", help="Строка куки")
    
    args = parser.parse_args()

    print(f"\033[95m=== НАЧАЛО СКАНИРОВАНИЯ {args.target} ===\033[0m\n")

    # 1. Авторизация
    active_cookies = check_auth(args.target, args.login, args.password, args.cookie)
    
    # 2. Сканирование Nmap
    print(f"\033[94m[*] Запускаю Nmap для {args.target}...\033[0m")
    nm = nmap.PortScanner()
    try:
        clean_target = args.target.replace("http://", "").replace("https://", "").split('/')[0]
        nm.scan(hosts=clean_target, arguments='-sV -F')
        nmap_results = ""
        for host in nm.all_hosts():
            nmap_results += f"Хост: {host}\n"
            for proto in nm[host].all_protocols():
                for port in nm[host][proto].keys():
                    state = nm[host][proto][port]['state']
                    service = nm[host][proto][port]['name']
                    nmap_results += f"  Порт {port}: {state} ({service})\n"
        
        if not nmap_results:
            nmap_results = "Открытых портов не найдено."
        else:
            print(f"\033[92m[+] Nmap нашел открытые порты!\033[0m")
            
    except Exception as e:
        nmap_results = f"Ошибка Nmap: {e}"
        print(f"\033[91m[-] {nmap_results}\033[0m")

    # 3. Отчет ИИ
    full_data = f"Куки: {active_cookies}\nРезультаты Nmap:\n{nmap_results}"
    report = generate_report(args.target, full_data)
    
    print("\n" + "\033[93m" + "="*55 + "\033[0m")
    print("\033[96m ОТЧЕТ ДЛЯ КЛИЕНТА:\033[0m")
    print("\033[93m" + "="*55 + "\033[0m")
    print(report)
    print("\033[93m" + "="*55 + "\033[0m\n")

if __name__ == "__main__":
    main()