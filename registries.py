import json
import re
import anthropic
from db import get_db_connection


def get_registries_for_object(object_id):
    with get_db_connection() as cur:
        cur.execute(
            """
            SELECT id, work_section_name, project_marks
            FROM registries
            WHERE object_id = %s
            ORDER BY id;
            """,
            (object_id,),
        )
        return cur.fetchall()


def create_registry(object_id, work_section_name, project_marks=None):
    with get_db_connection() as cur:
        cur.execute(
            """
            INSERT INTO registries (object_id, work_section_name, project_marks)
            VALUES (%s, %s, %s)
            RETURNING id;
            """,
            (object_id, work_section_name, project_marks),
        )
        return cur.fetchone()[0]


def get_registry_documents(registry_id):
    with get_db_connection() as cur:
        cur.execute(
            """
            SELECT id, seq_number, is_category_header, document_name, document_number_date,
                   issuing_org, page_count, note
            FROM registry_documents
            WHERE registry_id = %s
            ORDER BY id;
            """,
            (registry_id,),
        )
        return cur.fetchall()


def create_registry_documents_bulk(registry_id, rows):
    with get_db_connection() as cur:
        for row in rows:
            cur.execute(
                """
                INSERT INTO registry_documents
                    (registry_id, seq_number, is_category_header, document_name,
                     document_number_date, issuing_org, page_count, note)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                """,
                (
                    registry_id,
                    row.get("seq_number"),
                    bool(row.get("is_category_header", False)),
                    row.get("document_name"),
                    row.get("document_number_date"),
                    row.get("issuing_org"),
                    row.get("page_count"),
                    row.get("note"),
                ),
            )


REGISTRY_PARSE_PROMPT = """Ты помощник инженера, который разбирает списки исполнительной документации
(реестры документов на строительном объекте).

Тебе дан сырой текст реестра — он мог быть скопирован из Word, Excel или PDF,
поэтому форматирование может быть сбитым: съехавшие колонки, лишние пробелы,
перенос строк внутри одной записи и т.п.

Разбери текст построчно и извлеки записи в виде JSON-массива объектов
СТРОГО со следующими полями у каждого объекта:

- seq_number: строка — номер по порядку, как он написан в реестре
  (например "1", "5", "8", "2.1"). В реальных реестрах нумерация обычно
  сквозная и включает не только документы, но и строки-заголовки разделов —
  заголовок раздела может иметь свой номер по порядку наравне с документами.
  Извлекай этот номер и для заголовков, если он есть в тексте. Ставь null,
  только если номера нет вообще ни у документа, ни у заголовка.
- is_category_header: boolean — true, если строка не документ, а заголовок
  раздела/группы документов (например "5. Общие журналы работ"),
  иначе false.
- document_name: строка — наименование документа (или текст заголовка,
  если is_category_header = true).
- document_number_date: строка — номер и/или дата документа как есть в
  тексте (например "№ 12 от 03.02.2026"), или null.
- issuing_org: строка — кем выдан/составлен документ, или null.
- page_count: число — количество листов, или null, если не указано.
- note: строка — примечание, или null.

Правила:
1. Для строк-заголовков разделов (is_category_header = true) поля
   document_number_date, issuing_org, page_count обычно null. Поле
   seq_number для заголовков заполняй по общей сквозной нумерации текста
   (см. описание поля seq_number выше) — не ставь null, если у заголовка
   есть номер по порядку в исходном тексте.
2. Ничего не придумывай. Если значение поля нельзя определить из текста —
   ставь null.
3. Сохраняй порядок строк как в исходном тексте.
4. Ответ — ТОЛЬКО валидный JSON-массив объектов, без пояснений, без
   преамбулы, без markdown-блоков вида ```json. Ответ должен начинаться
   с символа [ и заканчиваться символом ].

Текст реестра:
<raw_text>
{raw_text}
</raw_text>
"""


def _extract_json_array(text):
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    fence_match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1))
        except json.JSONDecodeError:
            pass

    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Не удалось извлечь валидный JSON-массив из ответа Claude: {text[:500]!r}")


def parse_registry_text(raw_text):
    client = anthropic.Anthropic()
    with client.messages.stream(
        model="claude-sonnet-5",
        max_tokens=16000,
        messages=[
            {"role": "user", "content": REGISTRY_PARSE_PROMPT.format(raw_text=raw_text)}
        ],
    ) as stream:
        response = stream.get_final_message()

    response_text = next(block.text for block in response.content if block.type == "text")
    return _extract_json_array(response_text)
