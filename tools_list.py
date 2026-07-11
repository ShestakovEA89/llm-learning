tools = [
    {
        "name": "Google Colab",
        "url": "https://colab.research.google.com",
        "is_free": True
    },
    {
        "name": "Cursor",
        "url": "https://www.cursor.com",
        "is_free": False
    },
    {
        "name": "Kaggle",
        "url": "https://www.kaggle.com",
        "is_free": True
    }
]

for tool in tools:
    if tool["is_free"]:
        print(tool["name"])