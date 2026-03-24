import asyncio, re, os, subprocess
from dotenv import load_dotenv
from scraper import CortexScraper
from bridge import CortexBridge
from reporter import CortexReporter

load_dotenv() # Завантажуємо змінні з .env

def clean_artifacts():
    files_to_delete = ["generated_test_result.py", "failure_screenshot.png"]
    for file in files_to_delete:
        if os.path.exists(file):
            os.remove(file)
            print(f"[*] Видалено старий артефакт: {file}")

def extract_code(llm_output):
    # Видаляємо зайві пробіли/рядки на початку і в кінці
    llm_output = llm_output.strip()
    # Шукаємо блоки коду python
    code_blocks = re.findall(r'```python\n(.*?)\n```', llm_output, re.DOTALL)
    if code_blocks:
        return code_blocks[0]
    
    # Якщо блоків з назвою мови немає, шукаємо будь-які блоки з ```
    generic_blocks = re.findall(r'```\n(.*?)\n```', llm_output, re.DOTALL)
    if generic_blocks:
        return generic_blocks[0]
    
    return llm_output

async def execute_test(filepath):
    print(f"\n--- Автоматичний запуск тесту ---")
    try:
        # Важливо: таймаут тут (45с) має бути більшим за таймаут у Playwright (30с)
        result = subprocess.run(
            ["python3", filepath], 
            capture_output=True, 
            text=True, 
            timeout=45 
        )

        print(f"DEBUG: Return code: {result.returncode}")
        
        if result.returncode == 0:
            print("[✅] ТЕСТ ПРОЙДЕНО УСПІШНО")
            return True, ""
        else:
            print("[❌] ТЕСТ ВПАВ")
            return False, result.stderr
            
    except subprocess.TimeoutExpired:
        return False, "Process timed out after 45 seconds"
    except Exception as e:
        print(f"[!] Критична помилка при запуску: {e}")
        return False, str(e)

async def run_agentic_qa(url, task, bridge):
    clean_artifacts()
    scraper = CortexScraper()
    reporter = CortexReporter()
    
    cleaned_html = await scraper.get_cleaned_html(url)
    raw_code = bridge.generate_test(f"URL: {url}\nHTML: {cleaned_html}", task)
    generated_code = extract_code(raw_code)
    
    test_file = os.path.join(os.path.dirname(__file__), "generated_test_result.py")
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(generated_code)
    
    success, error_msg = await execute_test(test_file)
    
    # Визначаємо статус та скриншот
    screenshot_path = "failure_screenshot.png"
    status = "PASSED" if success else "FAILED"
    
    # Створюємо звіт
    reporter.generate_report(url, task, status, error_msg, screenshot_path)
    
    if not success:        
        # Перевіряємо скриншот перед ремонтом
        screenshot_path = os.path.join(os.path.dirname(__file__), "failure_screenshot.png")
        if os.path.exists(screenshot_path):
            print(f"[📸] Скриншот помилки знайдено: {screenshot_path}")
        
        print("[🛠] ЗАПУСК РЕМОНТУ...")
        raw_repaired = bridge.repair_test(generated_code, error_msg, cleaned_html, task)
        repaired_code = extract_code(raw_repaired)

        print("\n" + "~"*50)
        print("🤔 ПОЯСНЕННЯ ВІД ШІ (DIAGNOSIS):")
        # Витягуємо думки з тегів <think>, які генерує DeepSeek
        think_match = re.search(r'<think>(.*?)</think>', raw_repaired, re.DOTALL)
        if think_match:
            print(think_match.group(1).strip())
        else:
            # Фолбек, якщо тегів <think> немає
            diagnosis = raw_repaired.split("```python")[0].strip()
            print(diagnosis if diagnosis else "Діагноз відсутній у відповіді")
        print("~"*50)

        if "DIAGNOSTIC_FAIL" in raw_repaired:
            print("\n" + "!"*50)
            print("🛑 ШІ-АГЕНТ ВИЯВИВ КРИТИЧНУ ПОМИЛКУ:")
            print(f"Повідомлення: {raw_repaired.strip()}")
            print("Пояснення: Елемент відсутній в DOM-дереві. ШІ відмовився створювати хибний тест.")
            print("!"*50)
            return # Виходимо з функції, не запускаючи зламаний файл
        
        # Показуємо код ТІЛЬКИ для ознайомлення
        print("\n" + "="*50)
        print("🤖 ШІ ЗАПРОПОНУВАВ ВИПРАВЛЕННЯ:")
        print("-" * 50)
        print(repaired_code)
        print("-" * 50)
        
        user_choice = input("✅ Застосувати ці зміни? (y/n): ").lower()
        
        if user_choice == 'y':
            with open(test_file, "w", encoding="utf-8") as f:
                f.write(repaired_code)
            
            print("[*] Перезапуск виправленого тесту...")
            # Тепер просто запускаємо. Якщо впаде — спрацює гілка else нижче.
            success, error_msg = await execute_test(test_file)
            
            if success:
                print("[✨] САМОВІДНОВЛЕННЯ УСПІШНЕ!")
            else:
                # ТУТ ВІН ПРОСТО ПАДАЄ БЕЗ ЗАПИТАНЬ
                print("[💀] AI не зміг це виправити.")
                if error_msg:
                    print(f"Остаточна помилка:\n{error_msg}")
        else:
            print("[⚠️] Ремонт скасовано користувачем. Вихід.")

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🧠 ВІТАЄМО У CORTEX-SDET ORCHESTRATOR")
    print("="*50)
    print("Оберіть режим роботи ШІ:")
    print("1. 💻 Локальний (Ollama - deepseek-r1:8b) - Безкоштовно, навантажує ПК")
    print("2. ☁️ Хмарний (OpenAI - gpt-4o-mini) - Швидко, точно, потрібен API ключ")
    
    choice = input("Ваш вибір (1 або 2): ").strip()
    
    if choice == "2":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ ПОМИЛКА: Не знайдено OPENAI_API_KEY у файлі .env")
            exit(1)
        bridge = CortexBridge(model_name="gpt-4o-mini", use_cloud=True, api_key=api_key)
    else:
        bridge = CortexBridge(model_name="deepseek-r1:8b", use_cloud=False)

    target_url = input("\n🌐 Введіть URL сайту (напр. https://the-internet.herokuapp.com/login): ").strip()
    user_task = input("📝 Введіть завдання для тесту: ").strip()
    
    # Викликаємо нашу головну функцію
    asyncio.run(run_agentic_qa(target_url, user_task, bridge))