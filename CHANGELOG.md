# Changelog

## 1.100.1.1

- Added centralized app version constant (`scripts/app_version.py`) and displayed it in the dashboard.
- Added dashboard compatibility layer in `scripts/sheet_reader.py` so the web dashboard can call:
  - `get_all_topics()`
  - `get_quotes_by_topic()`
  - `get_remaining_counts()`
  - `write_back()`
  - `write_generation_meta()`
- Added background modes to the generator and dashboard:
  - `none`
  - `custom` (random from `assets/custom_backgrounds/`)
  - `ai` (Hugging Face) using:
    - `scripts/ai_prompt_generator.py`
    - `scripts/ai_image_generator.py`
- Added AI model selector in dashboard:
  - `stable_diffusion`
  - `openjourney`
  - `realistic`
- Repository cleanup:
  - Moved documentation into `docs/`
  - Moved tests into `tests/`

