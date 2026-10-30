# FTB Quest Translator

[Русский](README.md) · English

Translate FTB Quests and KubeJS language files for Minecraft.

## Get started

Download `FTB_Quest_Translator.exe` from [Releases](https://github.com/Tevuu/Ftb-quest-translator/releases) and run it. No Python installation is needed. Translation requires an internet connection.

## Translate your files

Choose a tab, select a folder, enter a target language code (`ru` for Russian), and click the start translation button.

| Tab | Folder in your modpack | Translation output |
| --- | --- | --- |
| **FTB Quests** | `config/ftbquests/quests/chapters` | A `chapters-translate` folder next to `chapters` |
| **KubeJS / Assets** | `kubejs/assets` with `<mod>/lang` subfolders | A new file in each `lang` folder, such as `ru_ru.json` |

For FTB Quests, back up `chapters`, then copy the files from `chapters-translate` into it, replacing the originals. Check the translation in-game.

For KubeJS, the app uses `en_us.json` or the first JSON file it finds. Existing target language files are skipped.

## Run from source

Install Python 3.9+, download the source code, and run these commands in the project folder:

```powershell
py -m pip install -r requirements.txt
py gui.py
```

For the quest translator's command-line version, run `py main.py`.

[Report a bug](https://github.com/Tevuu/Ftb-quest-translator/issues) and attach the original file that causes the problem.
