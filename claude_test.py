import anthropic

load_dotenv()

client = anthropic.Anthropic()

history = []

while True:
    user_input = input("Ты: ")
    if user_input == "выход":
        break
    
    history.append({"role": "user", "content": user_input})
    
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=history
    )
    
    response = message.content[0].text
    print(f"Claude: {response}\n")
    
    history.append({"role": "assistant", "content": response})