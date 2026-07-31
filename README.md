# Помощник инженера ПТО

RAG-приложение (Retrieval-Augmented Generation) для инженеров производственно-технического отдела. Позволяет загружать PDF-документы (СП, ГОСТы, регламенты и т.п.) и задавать по ним вопросы на естественном языке — ответ формируется на основе релевантных фрагментов документов, с указанием источников.

## Возможности

- Загрузка PDF-документов через веб-интерфейс
- Индексация документов и хранение векторов в облаке (Supabase) — не нужно загружать документы заново при каждом запуске
- Чат с историей сообщений в рамках сессии
- Ответы со ссылками на источники: имя файла, релевантность и цитата фрагмента
- Список всех документов, уже загруженных в базу

## Стек технологий

- **Python** — основной язык
- **Streamlit** — веб-интерфейс
- **LlamaIndex** — оркестрация RAG: чтение PDF, построение индекса, запросы к векторному хранилищу
- **Claude API (Anthropic)** — LLM для генерации ответов (`llama-index-llms-anthropic`)
- **HuggingFace Embeddings** (`BAAI/bge-small-en-v1.5`) — построение эмбеддингов документов
- **Supabase (Postgres + pgvector)** — персистентное хранилище векторов и метаданных документов

## Требования

- Python 3.10+
- Аккаунт Anthropic с API-ключом
- Проект Supabase с включённым расширением `vecs`/pgvector

## Установка

1. Клонируйте репозиторий и перейдите в его директорию.
2. Создайте и активируйте виртуальное окружение:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Установите зависимости:

   ```bash
   pip install -r requirements.txt
   ```

4. Создайте файл `.env` в корне проекта со своими значениями (файл в `.gitignore`, в репозиторий не попадёт):

   ```
   ANTHROPIC_API_KEY=your-anthropic-api-key
   SUPABASE_CONNECTION=postgresql://user:password@host:port/dbname
   ```

## Запуск

```bash
streamlit run rag_app.py
```

Приложение откроется в браузере (по умолчанию `http://localhost:8501`). При первом запуске оно подключится к индексу в Supabase; новые документы можно добавить через раздел «➕ Загрузить новые документы».

## Тестирование

Тесты пишут напрямую в реальную Supabase (без моков) — fixture в `conftest.py` создаёт изолированные тестовые данные (объект, организации, при необходимости акт с подписантами) и автоматически удаляет их после каждого теста в правильном порядке (внешние ключи объявлены без `ON DELETE CASCADE`).

1. Установите dev-зависимости (включают `requirements.txt` + `pytest`):

   ```bash
   pip install -r requirements-dev.txt
   ```

2. Запустите тесты:

   ```bash
   pytest
   ```

## Структура проекта

- `rag_app.py` — точка входа: роутер `st.tabs()`, который собирает пять вкладок (UI каждой вынесен в отдельный `tab_*.py` ниже) и общую настройку страницы (CSS, заголовок)
- `shared.py` — общее для нескольких вкладок: метки вкладок и навигационный хелпер `go_to_object_tab()` для переключения на вкладку «Объект»
- `tab_object.py` — вкладка «🏗️ Объект»: выбор/создание рабочего объекта и организаций, реестры исполнительной документации, представители организаций
- `tab_journal.py` — вкладка «📓 Журнал работ»: общий журнал производства работ
- `tab_new_act.py` — вкладка «📝 Новый акт скрытых работ»: создание акта, подписанты, материалы, генерация .docx
- `tab_commission_acts.py` — вкладка «📋 Комиссионные акты»: создание комиссионных актов и состава комиссии
- `tab_chat.py` — вкладка «💬 Чат по документам»: RAG-чат, загрузка PDF, настройка LLM (`configure_llm_settings`)
- `db.py` — подключение к Supabase (`get_db_connection`, `SUPABASE_CONNECTION`)
- `objects.py` — объекты строительства (`get_objects`, `get_object_org_links`, `create_object`, `update_object_org_links`)
- `organizations.py` — организации (`get_organizations`, `get_all_organizations`, `create_organization`)
- `persons.py` — ответственные лица (`get_responsible_persons`, `create_responsible_person`)
- `acts.py` — акты скрытых работ, подписанты, материалы (`get_acts_for_object`, `create_act`, `create_act_signatory`, `get_materials_for_act`, `create_material`)
- `journal.py` — журнал производства работ (`get_work_journal_entries`, `get_work_journal_entries_for_period`, `create_work_journal_entry`)
- `commission_acts.py` — комиссионные акты и их подписанты (`create_commission_act`, `get_commission_acts_for_object`, `create_commission_act_signatory`, `get_commission_act_signatories`)
- `registries.py` — реестры исполнительной документации (`get_registries_for_object`, `get_registry_documents`)
- `documents.py` — список загруженных в базу документов для RAG-чата (`get_document_list`)
- `cache.py` — кэширующие обёртки (`@st.cache_data`) над читающими функциями из модулей выше; сами модули содержат только чистые функции работы с БД, без зависимости от Streamlit
- `generate_act_final.py` — генерация .docx актов по шаблону
- `conftest.py` — pytest-fixtures для тестов (изолированные тестовые данные в реальной Supabase + автоочистка)
- `test_acts.py` — тесты для `create_act`
- `test_generate_act.py` — smoke-тест для `generate_act`
- `templates/` — шаблоны документов (.docx)
- `requirements.txt` — зависимости проекта
- `requirements-dev.txt` — `requirements.txt` + `pytest`, для разработки и тестов
- `uploaded_docs/` — локально сохранённые загруженные PDF (не хранится в git)
