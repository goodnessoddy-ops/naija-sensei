import ollama

# This list remembers the whole conversation so Gemma has context
conversation = [
    {
        "role": "system",
        "content": (
            "You are Tutorly, an offline tutor for Nigerian secondary school students. "
            "You explain things in simple, encouraging language. "
            "Respond in the same language the student uses — "
            "English, Nigerian Pidgin, Yoruba, Igbo, or Hausa. "
            "Keep answers short unless the student asks for detail."
        ),
    }
]

print("Tutorly is ready. Type your question, or 'quit' to exit.\n")

while True:
    # Get the user's next question
    user_message = input("You: ").strip()

    # Check if they want to exit
    if user_message.lower() in ("quit", "exit", "bye"):
        print("Bye!")
        break

    # Skip empty input
    if not user_message:
        continue

    # Add the user's message to the conversation
    conversation.append({"role": "user", "content": user_message})

    # Ask Gemma, passing the WHOLE conversation history so it has memory
    print("Tutorly: ", end="", flush=True)
    reply = ""
    for chunk in ollama.chat(model="gemma4:e4b", messages=conversation, stream=True):
        piece = chunk["message"]["content"]
        print(piece, end="", flush=True)  # print each piece as it arrives
        reply += piece
    print("\n")

    # Remember Gemma's reply so the next question has context
    conversation.append({"role": "assistant", "content": reply})