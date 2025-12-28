async function sendMessage() {
    const input = document.getElementById("userInput");
    const message = input.value;
    if (!message) return;

    addMessage(message, "user");
    input.value = "";

    const response = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: message }),
    });

    const data = await response.json();
    addMessage(data.response, "bot");
}

function addMessage(text, sender) {
    const chatBox = document.getElementById("chatBox");
    const msgDiv = document.createElement("div");
    msgDiv.classList.add("message", sender);
    msgDiv.innerText = text;
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}
