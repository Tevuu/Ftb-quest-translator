# gui.py

import os
import re
import sys
import threading
from pathlib import Path
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

import customtkinter as ctk
from tkinter import filedialog, messagebox
from translatepy import Translator

# --- Logic from main.py ---

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
        return string

def process_array(match, lang_to):
    prefix = match.group(1)
    opening = match.group(2)
    array_content = match.group(3)
    closing = match.group(4)

    lines = []
    for line in array_content.strip().split('\n'):
        line = line.strip()
        if line.startswith('"') and line.endswith('"'):
            text = line[1:-1]
            if text:
                text = translate_to(text, lang_to)
            lines.append(f'"{text}"')
        else:
            lines.append(line)

    indent = ' ' * 4
    result = f'{prefix}{opening}'
    if lines:
        result += '\n' + '\n'.join(f'{indent}{line}' for line in lines) + '\n'
    result += closing

    return result

def translate_snbt_content(content, lang_to):
    content = re.sub(r'(^|\s)(title:\s*")([^"]+)(")',
                    lambda m: f'{m.group(1)}{m.group(2)}{translate_to(m.group(3), lang_to)}{m.group(4)}',
                    content)
    content = re.sub(r'(^|\s)(subtitle:\s*")([^"]+)(")',
                    lambda m: f'{m.group(1)}{m.group(2)}{translate_to(m.group(3), lang_to)}{m.group(4)}',
                    content)
    content = re.sub(r'(^|\s)(description:\s*")([^"]+)(")',
                    lambda m: f'{m.group(1)}{m.group(2)}{translate_to(m.group(3), lang_to)}{m.group(4)}',
                    content)
    content = re.sub(r'(^|\s)(description:\s*\[\s*)([\s\S]*?)(\s*\])',
                    lambda m: process_array(m, lang_to),
                    content)

    def translate_task_title(match):
        full_match = match.group(0)
        title_content = match.group(2)
        if (':' in title_content and len(title_content) < 30 and not ' ' in title_content):
            return full_match
        return f'{match.group(1)}{translate_to(title_content, lang_to)}{match.group(3)}'

    content = re.sub(r'(tasks:\s*\[[^\]]*?title:\s*")([^"]+)(")',
                    translate_task_title,
                    content)

    def translate_display_name(match):
        name_content = match.group(2)
        if ' ' in name_content and not name_content.startswith('{'):
            return f'{match.group(1)}{translate_to(name_content, lang_to)}{match.group(3)}'
        return match.group(0)

    content = re.sub(r'(display:\s*\{[^}]*?Name:\s*")([^"]+)(")',
                    translate_display_name,
                    content, flags=re.DOTALL)

    def translate_lore(match):
        lore_content = match.group(1)
        def translate_lore_line(line):
            line = line.strip()
            if (not line or any(char in line for char in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя') or
                line.startswith('{') or line.endswith('}') or
                (':' in line and len(line) < 30 and not ' ' in line) or
                '(Part of the' in line or line.startswith(' 8') or
                line.startswith(' 7') or line.startswith(' e(')):
                return f'"{line}"'
            translated_line = translate_to(line, lang_to)
            return f'"{translated_line}"'
        lines = re.findall(r'"\s*([^"]*)"', lore_content)
        translated_lines = [translate_lore_line(line) for line in lines]
        return 'Lore: [' + ', '.join(translated_lines) + ']'

    content = re.sub(r'Lore:\s*\[([^\]]+)\]', translate_lore, content)
    content = re.sub(r'(hover:\s*\[[^\]]*?")([^"]*)("[^\]]*\])',
                    lambda m: f'{m.group(1)}{translate_to(m.group(2), lang_to)}{m.group(3)}',
                    content)
    return content

# --- GUI Class ---

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("FTB Quest Translator")
        self.geometry("600x500")
        
        # Appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        # Title
        self.title_label = ctk.CTkLabel(self, text="FTB Quest Translator", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=20)

        # Folder selection
        self.folder_frame = ctk.CTkFrame(self)
        self.folder_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.folder_frame.grid_columnconfigure(1, weight=1)

        self.folder_label = ctk.CTkLabel(self.folder_frame, text="Папка chapters:")
        self.folder_label.grid(row=0, column=0, padx=10, pady=10)

        self.folder_path = ctk.CTkEntry(self.folder_frame, placeholder_text="Выберите путь к папке chapters")
        self.folder_path.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        self.browse_button = ctk.CTkButton(self.folder_frame, text="Обзор", width=100, command=self.browse_folder)
        self.browse_button.grid(row=0, column=2, padx=10, pady=10)

        # Language selection
        self.lang_frame = ctk.CTkFrame(self)
        self.lang_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        self.lang_label = ctk.CTkLabel(self.lang_frame, text="Язык перевода:")
        self.lang_label.pack(side="left", padx=10, pady=10)

        self.lang_entry = ctk.CTkEntry(self.lang_frame, width=100)
        self.lang_entry.insert(0, "ru")
        self.lang_entry.pack(side="left", padx=10, pady=10)

        # Start button
        self.start_button = ctk.CTkButton(self, text="Начать перевод", command=self.start_translation)
        self.start_button.grid(row=3, column=0, padx=20, pady=20)

        # Progress and Logs
        self.log_area = ctk.CTkTextbox(self, height=150)
        self.log_area.grid(row=4, column=0, padx=20, pady=10, sticky="nsew")

        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.grid(row=5, column=0, padx=20, pady=10, sticky="ew")
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(self, text="Готов к работе")
        self.status_label.grid(row=6, column=0, padx=20, pady=5)

    def browse_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.folder_path.delete(0, "end")
            self.folder_path.insert(0, path)

    def log(self, message):
        self.log_area.insert("end", message + "\n")
        self.log_area.see("end")

    def update_progress(self, value):
        self.progress_bar.set(value)

    def start_translation(self):
        target_path = self.folder_path.get().strip()
        lang_to = self.lang_entry.get().strip().lower()

        if not target_path or not os.path.exists(target_path):
            messagebox.showerror("Ошибка", "Выберите корректный путь к папке chapters!")
            return

        quest_path = Path(target_path)
        snbt_files = list(quest_path.rglob("*.snbt"))
        
        if not snbt_files:
            messagebox.showerror("Ошибка", "В выбранной папке не найдено .snbt файлов!")
            return

        self.start_button.configure(state="disabled")
        self.log_area.delete("1.0", "end")
        self.log(f"Найдено {len(snbt_files)} файлов. Начинаю перевод...")
        
        # Run translation in a separate thread
        threading.Thread(target=self.run_translation, args=(snbt_files, lang_to), daemon=True).start()

    def run_translation(self, snbt_files, lang_to):
        successful = 0
        total_files = len(snbt_files)

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = []
            for input_path in snbt_files:
                futures.append(executor.submit(self.process_file_task, input_path, lang_to))

            for i, future in enumerate(futures):
                if future.result():
                    successful += 1
                
                progress = (i + 1) / total_files
                self.after(0, lambda p=progress, idx=i+1: self.update_ui_progress(p, idx, total_files))

        self.after(0, lambda: self.finish_translation(successful, total_files))

    def update_ui_progress(self, progress, current, total):
        self.progress_bar.set(progress)
        self.status_label.configure(text=f"Обработка: {current}/{total} ({progress*100:.1f}%)")

    def process_file_task(self, input_path, lang_to):
        output_path = str(input_path).replace('chapters', 'chapters-translate')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        try:
            with open(input_path, 'r', encoding='utf-8') as file:
                content = file.read()

            self.after(0, lambda: self.log(f"Обработка файла: {input_path.name}"))

            translated_content = translate_snbt_content(content, lang_to)

            with open(output_path, 'w', encoding='utf-8') as translated_file:
                translated_file.write(translated_content)

            self.after(0, lambda: self.log(f"✓ Успешно: {input_path.name}"))
            return True

        except Exception as e:
            self.after(0, lambda: self.log(f"✗ Ошибка {input_path.name}: {e}"))
            return False

    def finish_translation(self, successful, total):
        self.start_button.configure(state="normal")
        self.status_label.configure(text="Перевод завершен")
        self.log(f"\n✅ Перевод завершен! Успешно: {successful}/{total}")
        self.log(f"📂 Файлы сохранены в папку chapters-translate")
        messagebox.showinfo("Готово", f"Перевод завершен!\nУспешно: {successful}/{total}")

if __name__ == "__main__":
    app = App()
    app.mainloop()
