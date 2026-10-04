# mhp3rd-yakumo-ru

A work-in-progress Russian translation pack for [Yakumo](https://github.com/TeamGDB/Yakumo), plus a simple `.lang` translator.

**Experimental, rough translation.** The pack contains **17,762 translated entries across 23 supported text blocks**. Most were translated by DeepSeek Flash; the final rejected entries were corrected manually. It has not been fully proofread: wording and terminology may be wrong or inconsistent, and long names/descriptions can overflow the game's fixed UI fields. Coverage of the extracted source keys does not mean every piece of text or text drawn in images is translated.

## Download and install

Download `ru.lang` from [Releases](https://github.com/MHunterG/mhp3rd-yakumo-ru/releases). In a compatible Yakumo build, open **System → Text → Import translation…**, import the file, select **Russian** under **Game text language**, then restart the game.

This preview requires Yakumo's translation mechanism and Cyrillic width fix currently in [PR #227](https://github.com/TeamGDB/Yakumo/pull/227). Compatibility with existing stable releases has not been verified. A developer build was tried on Steam Deck; all layouts, quests, dialogue and other platforms have not been exhaustively checked.

Formatting tags, placeholders, exact keys and line-break sequences were checked against the local source, and Yakumo's native parser accepted all 17,762 entries. These are structural checks, not a guarantee of translation quality.

## Translate a file

Python 3.10 or newer; no dependencies to install. Supply your own local source `.lang` file. English source text and game data are not distributed here.

Preview:

```sh
python3 -m tools.translate --source local/en.lang --output work/ru.lang --language ru --name Russian
```

To translate, set `DEEPSEEK_API_KEY` in your environment or in a local `.env` file and add `--execute` to the same command. This sends source text to DeepSeek and incurs API charges. The model defaults to `deepseek-flash`; select another with `--model`.

The script saves each completed batch. Repeat the same command to resume: keys already in the output are preserved. Run one translator at a time per output file. It checks keys, formatting tags, placeholders and line breaks before saving. It does not automatically retry failed HTTP requests. Invalid model output is retried in smaller batches; these additional API calls also incur charges. If a single row still fails validation, its key is saved beside the output in `.failures.json` and the run continues. Deferred rows remain untranslated; the process returns status 2 when any remain. Repeat the command to retry them after the other rows finish. Review wording and text length manually before using a generated pack.

Other languages work the same way: for example, use `--language es --name Spanish`. Source and output files must be different. Keep the same source file when resuming; a small checkpoint beside the output checks its fingerprint. If the balance runs out, top up and repeat the command. Use `--max-batches 1` for a trial run.

Only the Russian pack belongs in Git. Keep source files, generated drafts and API keys local; `local/`, `work/` and other `.lang` files are ignored.

API documentation: [chat completions](https://api-docs.deepseek.com/api/create-chat-completion/), [pricing](https://api-docs.deepseek.com/quick_start/pricing/).

## License

Original scripts and translation contributions are provided under MIT. No game files are included; the license grants no rights to the original game's content.
