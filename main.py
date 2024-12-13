import os
from concurrent.futures import ThreadPoolExecutor
from translatepy import Translator
import re
from pathlib import Path
from functools import lru_cache

translator = Translator()

@lru_cache(maxsize=1000)
def translate_to(string, lang_to):
    if not string:
        return ''
    trans = re.sub(r'&([0-9]{1,3}|[a-z])', '^^*^^', string)
    tend = re.findall(r'&([0-9]{1,3}|[a-z])', string)
    trans = str(translator.translate(trans, lang_to)).replace('"', "''")
    for j, replacement in enumerate(tend):
        trans = trans.replace('^^*^^', '&' + replacement, 1)
    return trans

def translate_description(description, lang_to):
    lines = description.split('\n')
    translated_lines = []
    for line in lines:
        match = re.match(r'^(\s*")(.*?)("\s*)$', line)
        if match:
            indent, content, end = match.groups()
            translated_content = translate_to(content, lang_to)
            translated_lines.append(f"{indent}{translated_content}{end}")
        else:
            translated_lines.append(line)  # Keep non-matching lines as is
    return '\n'.join(translated_lines)

def process_file(input_path, lang_to):
    output_path = str(input_path).replace('chapters', 'chapters-translate')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(input_path, 'r', encoding='utf-8') as file, open(output_path, 'w', encoding='utf-8') as translated_file:
        content = file.read()
        
        # Translate title while preserving formatting
        content = re.sub(r'(title:\s*")([^"]+)(")', lambda m: f'{m.group(1)}{translate_to(m.group(2), lang_to)}{m.group(3)}', content)
        
        # Translate description while preserving formatting
        content = re.sub(r'(description:\s*\[)([^\]]+)(\])', 
                         lambda m: f'{m.group(1)}{translate_description(m.group(2), lang_to)}{m.group(3)}', 
                         content, flags=re.DOTALL)
        
        translated_file.write(content)

def main():
    target = input('Enter the path to the file folder (example: C:/.../quests/chapters)\n')
    lang_to = input('Enter into which language to translate using abbreviated or full names (example: ru or Russian): ')
    quest_path = Path(target)
    
    with ThreadPoolExecutor() as executor:
        futures = []
        for input_path in quest_path.rglob("*.snbt"):
            futures.append(executor.submit(process_file, input_path, lang_to))
        
        for i, future in enumerate(futures):
            future.result()
            print(f'Progress: {(i+1)/len(futures)*100:.2f}%')

if __name__ == '__main__':
    main()