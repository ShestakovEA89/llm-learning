# Помощник инженера ПТО

Приложение для инженеров производственно-технического отдела (ПТО) в
строительстве — ведёт учёт исполнительной документации на объекте:
объекты и организации, журнал производства работ, акты скрытых работ,
комиссионные акты, реестры исполнительной документации (с AI-разбором
сырого текста реестра), трекер запросов к третьим сторонам. Отдельная
вкладка — RAG-чат по загруженным нормативным документам (СП, ГОСТы,
регламенты).

## Возможности

- **Объекты и организации** — учёт застройщика, подрядчика и других
  организаций по объекту, представители организаций с приказами
- **Журнал работ** — общий журнал производства работ по объекту
- **Акты скрытых работ** — создание акта, подписанты, материалы,
  генерация .docx по шаблону
- **Комиссионные акты** — создание комиссионных актов и состава комиссии
- **Реестры исполнительной документации** — ручное ведение реестра,
  либо разбор сырого текста реестра (скопированного из Word/Excel/PDF)
  через Claude API в структурированные строки
- **Трекер запросов** — что ещё нужно запросить у кого по объекту
  (форма акта у заказчика, приказы на ответственных лиц, паспорта на
  материалы у поставщиков) со статусами «ожидает»/«получено»
- **Чат по документам (RAG)** — загрузка PDF нормативных документов,
  вопросы на естественном языке с ответами со ссылками на источники
  (имя файла, релевантность, цитата фрагмента)

## Стек технологий

- **Python** — основной язык
- **Streamlit** — веб-интерфейс
- **Supabase (PostgreSQL)** — основное хранилище данных (объекты, акты,
  журнал, реестры и т.д.), доступ через пул соединений (`psycopg2.pool`)
- **LlamaIndex** — оркестрация RAG для вкладки «Чат по документам»:
  чтение PDF, построение индекса, запросы к векторному хранилищу
- **Claude API (Anthropic)** — LLM для генерации ответов в чате и для
  AI-разбора текста реестра (`parse_registry_text`)
- **HuggingFace Embeddings** (`BAAI/bge-small-en-v1.5`) — построение
  эмбеддингов документов для RAG
- **Supabase (Postgres + pgvector)** — персистентное хранилище векторов
  и метаданных документов для RAG-чата
- **docxtpl / python-docx** — генерация .docx актов по шаблону
- **pytest** — тесты на изолированной тестовой Supabase-БД

## Требования

- Python 3.10+
- Аккаунт Anthropic с API-ключом
- Проект Supabase с включённым расширением `vecs`/pgvector
- Отдельный (второй) проект Supabase для тестов — см. раздел
  «Тестирование»

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

4. Создайте файл `.env` в корне проекта со своими значениями (файл в
   `.gitignore`, в репозиторий не попадёт):

   ```
   ANTHROPIC_API_KEY=your-anthropic-api-key
   SUPABASE_CONNECTION=postgresql://user:password@host:port/dbname
   SUPABASE_CONNECTION_TEST=postgresql://user:password@host:port/dbname
   ```

   `SUPABASE_CONNECTION` — боевой проект Supabase. `SUPABASE_CONNECTION_TEST`
   — отдельный тестовый проект (см. «Тестирование») — обязателен для
   запуска `pytest`, тесты откажутся стартовать без него, чтобы не
   допустить случайной записи в боевую БД.

## Запуск

```bash
streamlit run rag_app.py
```

Приложение откроется в браузере (по умолчанию `http://localhost:8501`).
При первом запуске оно подключится к Supabase, прогреет пул соединений
к БД и подключится к индексу для RAG-чата; новые документы для чата
можно добавить через вкладку «💬 Чат по документам».

## Тестирование

Тесты пишут в **отдельный, изолированный** Supabase-проект — не в
боевую БД. `conftest.py` содержит session-scoped fixture, которая
явно проверяет, что `SUPABASE_CONNECTION_TEST` задан и отличается от
`SUPABASE_CONNECTION`, и переключает подключение на тестовый проект
до создания любых тестовых данных. Тестовые данные (объект,
организации, при необходимости акт с подписантами) создаются и
автоматически удаляются после каждого теста в правильном порядке
(внешние ключи объявлены без `ON DELETE CASCADE`).

Схема тестового проекта переносится из боевого через:
```bash
pg_dump --schema-only --no-owner --no-privileges --schema=public "БОЕВАЯ_СТРОКА" > schema.sql
psql "ТЕСТОВАЯ_СТРОКА" < schema.sql
```
(`--schema=public` обязателен — без него дамп тащит системные схемы
Supabase (`auth`, `storage`, `realtime` и т.п.), которые уже существуют
в новом проекте и конфликтуют при накатке.)

1. Установите dev-зависимости (включают `requirements.txt` + `pytest`):

   ```bash
   pip install -r requirements-dev.txt
   ```

2. Запустите тесты:

   ```bash
   pytest
   ```

## Структура проекта

- `rag_app.py` — точка входа: роутер `st.tabs()`, который собирает пять
  вкладок (UI каждой вынесен в отдельный `tab_*.py` ниже), настройку
  страницы (CSS, заголовок) и явный прогрев пула соединений к БД
  (`warm_up_pool()`) при старте
- `shared.py` — общее для нескольких вкладок: метки вкладок и
  навигационный хелпер `go_to_object_tab()` для переключения на вкладку
  «Объект»
- `tab_object.py` — вкладка «🏗️ Объект»: выбор/создание рабочего объекта
  и организаций, реестры исполнительной документации, представители
  организаций, открытые запросы к третьим сторонам
- `tab_journal.py` — вкладка «📓 Журнал работ»: общий журнал производства
  работ
- `tab_new_act.py` — вкладка «📝 Новый акт скрытых работ»: создание акта,
  подписанты, материалы, генерация .docx
- `tab_commission_acts.py` — вкладка «📋 Комиссионные акты»: создание
  комиссионных актов и состава комиссии
- `tab_chat.py` — вкладка «💬 Чат по документам»: RAG-чат, загрузка PDF,
  настройка LLM (`configure_llm_settings`)
- `db.py` — подключение к Supabase через пул соединений
  (`get_db_connection`, `get_connection_string`, `warm_up_pool`)
- `objects.py` — объекты строительства (`get_objects`,
  `get_object_org_links`, `create_object`, `update_object_org_links`)
- `organizations.py` — организации (`get_organizations`,
  `get_all_organizations`, `create_organization`)
- `persons.py` — ответственные лица (`get_responsible_persons`,
  `create_responsible_person`)
- `acts.py` — акты скрытых работ, подписанты, материалы
  (`get_acts_for_object`, `create_act`, `create_act_signatory`,
  `get_materials_for_act`, `create_material`)
- `journal.py` — журнал производства работ (`get_work_journal_entries`,
  `get_work_journal_entries_for_period`, `create_work_journal_entry`)
- `commission_acts.py` — комиссионные акты и их подписанты
  (`create_commission_act`, `get_commission_acts_for_object`,
  `create_commission_act_signatory`, `get_commission_act_signatories`)
- `registries.py` — реестры исполнительной документации, включая
  AI-разбор сырого текста реестра (`get_registries_for_object`,
  `get_registry_documents`, `create_registry_documents_bulk`,
  `parse_registry_text`)
- `pending_requests.py` — трекер запросов по объекту
  (`get_pending_requests`, `create_pending_request`,
  `mark_request_completed`)
- `documents.py` — список загруженных в базу документов для RAG-чата
  (`get_document_list`)
- `cache.py` — кэширующие обёртки (`@st.cache_data`) над читающими
  функциями из модулей выше; сами модули содержат только чистые функции
  работы с БД, без зависимости от Streamlit
- `session_cleanup.py` — механизм отмены тестовой сессии
  (`track_created()` + `delete_tracked_rows()` с батч-удалением по
  таблицам, соблюдая порядок FK)
- `generate_act_final.py` — генерация .docx актов по шаблону
- `conftest.py` — pytest-fixtures для тестов (изолированная тестовая
  Supabase-БД + автоочистка)
- `test_acts.py` — тесты для `create_act`
- `test_pending_requests.py` — тесты для `create_pending_request`/
  `mark_request_completed`
- `test_generate_act.py` — smoke-тест для `generate_act`
- `test_session_cleanup.py` — проверяет `TABLE_DELETE_ORDER` против
  реальных FK-зависимостей через `information_schema`
- `templates/` — шаблоны документов (.docx)
- `requirements.txt` — зависимости проекта
- `requirements-dev.txt` — `requirements.txt` + `pytest`, для разработки
  и тестов
- `uploaded_docs/` — локально сохранённые загруженные PDF (не хранится
  в git)
