# mhp3rd-yakumo-ru

A work-in-progress Russian translation pack for [Yakumo](https://github.com/TeamGDB/Yakumo), plus a simple `.lang` translator.

`translations/ru.lang` currently contains **8 sample UI translations**, not a complete translation. The pack requires Yakumo's language-file support. Cyrillic fonts and layout still need in-game review.

## Translate a file

Python 3.10 or newer; no dependencies to install. Supply your own local source `.lang` file. English source text and game data are not distributed here.

Preview:

```sh
python3 -m tools.translate --source local/en.lang --output work/ru.lang --language ru --name Russian
```

To translate, set `DEEPSEEK_API_KEY` in your environment or in a local `.env` file and add `--execute` to the same command. This sends source text to DeepSeek and incurs API charges. The model defaults to `deepseek-flash`; select another with `--model`.

The script saves each completed batch. Repeat the same command to resume: keys already in the output are preserved. Run one translator at a time per output file. It checks keys, formatting tags, placeholders and line breaks before saving. It does not automatically retry failed HTTP requests. Invalid model output is retried in smaller batches; these additional API calls also incur charges. If even one row fails validation, the run stops without changing that row. Review wording and text length manually before using a generated pack.

Other languages work the same way: for example, use `--language es --name Spanish`. Source and output files must be different. Keep the same source file when resuming; a small checkpoint beside the output checks its fingerprint. If the balance runs out, top up and repeat the command. Use `--max-batches 1` for a trial run.

Only the Russian pack belongs in Git. Keep source files, generated drafts and API keys local; `local/`, `work/` and other `.lang` files are ignored.

API documentation: [chat completions](https://api-docs.deepseek.com/api/create-chat-completion/), [pricing](https://api-docs.deepseek.com/quick_start/pricing/).

## License

Original scripts and translation contributions are provided under MIT. No game files are included; the license grants no rights to the original game's content.
