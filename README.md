# FTB Quest Translator

Русский · [English](README.en.md)

Перевод квестов FTB Quests и языковых файлов KubeJS для Minecraft.

## Запуск

Скачайте `FTB_Quest_Translator.exe` из [релизов](https://github.com/Tevuu/Ftb-quest-translator/releases) и запустите. Python не нужен, для перевода требуется интернет.

## Как перевести

Выберите вкладку, укажите папку и язык (`ru` — русский), затем нажмите кнопку начала перевода.

| Вкладка | Папка внутри сборки | Куда сохраняется перевод |
| --- | --- | --- |
| **FTB Quests** | `config/ftbquests/quests/chapters` | В соседнюю папку `chapters-translate` |
| **KubeJS / Assets** | `kubejs/assets` с подпапками `<мод>/lang` | В эти же папки `lang`, например в `ru_ru.json` |

Для FTB Quests сделайте резервную копию `chapters`, затем скопируйте в неё файлы из `chapters-translate` с заменой. Проверьте перевод в игре.

Для KubeJS программа берёт `en_us.json` или первый найденный JSON-файл. Уже существующие файлы целевого языка пропускаются.

## Запуск из исходников

Установите Python 3.9+, скачайте исходники и выполните в папке проекта:

```powershell
py -m pip install -r requirements.txt
py gui.py
```

Консольная версия для квестов: `py main.py`.

[Сообщить об ошибке](https://github.com/Tevuu/Ftb-quest-translator/issues) — приложите проблемный исходный файл.
