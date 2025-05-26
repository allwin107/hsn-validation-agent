const chatBox = document.getElementById("chatBox");
const userInput = document.getElementById("userInput");

// ✅ Append message to chat box
function appendMessage(sender, text) {
    const msg = document.createElement("div");
    msg.className = `message ${sender}`;
    const formattedText = text.replace(/\n/g, "<br>");
    msg.innerHTML = `<span class='bubble'>${formattedText}</span>`;
    chatBox.appendChild(msg);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// ✅ Show typing indicator
function showTyping() {
    const typing = document.createElement("div");
    typing.className = "message bot";
    typing.id = "typing";
    typing.innerHTML = "<span class='bubble typing'>Bot is typing...</span>";
    chatBox.appendChild(typing);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// ✅ Remove typing indicator
function removeTyping() {
    const typing = document.getElementById("typing");
    if (typing) typing.remove();
}

// ✅ Send message on button click
function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    appendMessage("user", message);
    userInput.value = "";

    showTyping();

    fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message })
    })
    .then(response => response.json())
    .then(data => {
        removeTyping();
        appendMessage("bot", data.reply);
        updateInvalidSidebar();  // ✅ update sidebar after response
    });
}

// ✅ Send message on Enter key press
userInput.addEventListener("keypress", function (e) {
    if (e.key === "Enter") sendMessage();
});

// ✅ Live refresh of invalids
function updateInvalidSidebar() {
    fetch("/admin/invalids_json")
        .then(res => res.json())
        .then(data => {
            const list = document.getElementById("invalidList");
            const seen = new Set();
            list.innerHTML = "";
            if (data.length === 0) {
                list.innerHTML = "<li>No invalids yet</li>";
            } else {
                data.forEach(([desc, count]) => {
                    if (!seen.has(desc)) {
                        seen.add(desc);
                        const li = document.createElement("li");
                        li.textContent = `${desc} — ${count}`;
                        list.appendChild(li);
                    }
                });
            }
        });
}

// 🔄 Initial load
updateInvalidSidebar();
// ✅ Initial chat messages
appendMessage("bot", "Hello! Enter any HSN code...");