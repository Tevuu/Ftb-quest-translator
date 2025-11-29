#main.py

import os
from concurrent.futures import ThreadPoolExecutor
from translatepy import Translator
import re
from pathlib import Path
from functools import lru_cache
import sys

translator = Translator()

@lru_cache(maxsize=1000)
def translate_to(string, lang_to):
    if not string or not string.strip():
        return string
    
    try:
        # Пропускаем строки, которые уже на русском
        if any(char in string for char in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'):
            return string
            
        # Пропускаем технические строки
        if (':' in string and len(string) < 50 and  # ID предметов/ресурсов
            not ' ' in string and  # Нет пробелов - вероятно ID
            any(c in string for c in [':','/','.','_','-'])):  # Содержит разделители
            return string
            
        # Пропускаем строки с фигурными скобками (скорее всего это ID или команды)
        if '{' in string or '}' in string:
            return string
            
        # Сохраняем форматирующие коды
        trans = re.sub(r'&([0-9a-z])', '^^*^^', string)
        tend = re.findall(r'&([0-9a-z])', string)
        
        # Переводим
        translated = translator.translate(trans, lang_to)
        trans = str(translated).replace('"', "''")
        
        # Восстанавливаем форматирующие коды
        for j, replacement in enumerate(tend):
            trans = trans.replace('^^*^^', '&' + replacement, 1)
        
        return trans
    except Exception as e:
        print(f"Translation error for '{string}': {e}")
        return string

def translate_snbt_content(content, lang_to):
    """Безопасно переводит только текстовые поля в SNBT файле"""
    
    # 1. Переводим основной title (но не внутри структур)
    content = re.sub(r'(^|\s)(title:\s*")([^"]+)(")', 
                    lambda m: f'{m.group(1)}{m.group(2)}{translate_to(m.group(3), lang_to)}{m.group(4)}', 
                    content)
    
    # 2. Переводим основной description
    content = re.sub(r'(^|\s)(description:\s*")([^"]+)(")', 
                    lambda m: f'{m.group(1)}{m.group(2)}{translate_to(m.group(3), lang_to)}{m.group(4)}', 
                    content)
    
    # 3. Переводим title внутри tasks
    def translate_task_title(match):
        full_match = match.group(0)
        title_content = match.group(2)
        
        # Проверяем, не является ли это ID предмета
        if (':' in title_content and len(title_content) < 30 and 
            not ' ' in title_content):
            return full_match  # Пропускаем ID предметов
            
        return f'{match.group(1)}{translate_to(title_content, lang_to)}{match.group(3)}'
    
    content = re.sub(r'(tasks:\s*\[[^\]]*?title:\s*")([^"]+)(")', 
                    translate_task_title, 
                    content)
    
    # 4. Переводим только display Name, который явно является текстом (с пробелами)
    def translate_display_name(match):
        name_content = match.group(2)
        # Переводим только если есть пробелы или это явно текст для игрока
        if ' ' in name_content and not name_content.startswith('{'):
            return f'{match.group(1)}{translate_to(name_content, lang_to)}{match.group(3)}'
        return match.group(0)
    
    content = re.sub(r'(display:\s*\{[^}]*?Name:\s*")([^"]+)(")', 
                    translate_display_name, 
                    content, flags=re.DOTALL)
    
    # 5. Перевод Lore - только явные описательные тексты
    def translate_lore(match):
        lore_content = match.group(1)
        
        def translate_lore_line(line):
            line = line.strip()
            # Пропускаем технические строки, ID, команды
            if (not line or
                any(char in line for char in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя') or
                line.startswith('{') or 
                line.endswith('}') or
                (':' in line and len(line) < 30 and not ' ' in line) or
                '(Part of the' in line or  # Пропускаем технические описания
                line.startswith(' 8') or   # Пропускаем форматированные строки
                line.startswith(' 7') or
                line.startswith(' e(')):
                return f'"{line}"'
            
            # Переводим только явные описательные тексты
            translated_line = translate_to(line, lang_to)
            return f'"{translated_line}"'
        
        # Разбиваем и обрабатываем каждую строку Lore
        lines = re.findall(r'"\s*([^"]*)"', lore_content)
        translated_lines = [translate_lore_line(line) for line in lines]
        
        return 'Lore: [' + ', '.join(translated_lines) + ']'
    
    content = re.sub(r'Lore:\s*\[([^\]]+)\]', translate_lore, content)
    
    # 6. Переводим hover текст (описания при наведении)
    content = re.sub(r'(hover:\s*\[[^\]]*?")([^"]*)("[^\]]*\])', 
                    lambda m: f'{m.group(1)}{translate_to(m.group(2), lang_to)}{m.group(3)}', 
                    content)
    
    return content

def process_file(input_path, lang_to):
    output_path = str(input_path).replace('chapters', 'chapters-translate')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        with open(input_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        print(f"Обработка файла: {input_path.name}")
        
        # Переводим содержимое файла
        translated_content = translate_snbt_content(content, lang_to)
        
        with open(output_path, 'w', encoding='utf-8') as translated_file:
            translated_file.write(translated_content)
        
        print(f"✓ Успешно обработан: {input_path.name}")
        return True
        
    except Exception as e:
        print(f"✗ Ошибка обработки {input_path.name}: {e}")
        return False

def main():
    print("=" * 60)
    print("FTB Quest Translator")
    print("=" * 60)
    
    if len(sys.argv) >= 3:
        target = sys.argv[1]
        lang_to = sys.argv[2]
    else:
        print("\nВведите путь к папке chapters:")
        target = input("Путь: ").strip()
        lang_to = input("Язык перевода: ").strip().lower()
    
    quest_path = Path(target)
    
    if not quest_path.exists():
        print(f"\n❌ Ошибка: Путь не существует!")
        input("Нажмите Enter для выхода...")
        return
    
    snbt_files = list(quest_path.rglob("*.snbt"))
    if not snbt_files:
        print("❌ Не найдено .snbt файлов!")
        input("Нажмите Enter для выхода...")
        return
    
    print(f"📄 Найдено {len(snbt_files)} файлов")
    print("🔄 Начинаю перевод...\n")
    
    successful = 0
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = []
        for input_path in snbt_files:
            futures.append(executor.submit(process_file, input_path, lang_to))
        
        for i, future in enumerate(futures):
            if future.result():
                successful += 1
            progress = (i+1)/len(futures)*100
            print(f'📊 Прогресс: {progress:.1f}% ({i+1}/{len(futures)})')
    
    print(f"\n✅ Перевод завершен! Успешно: {successful}/{len(snbt_files)}")
    print("📂 Файлы в chapters-translate")
    input("Нажмите Enter для выхода...")

if __name__ == '__main__':
    main()

#main.py