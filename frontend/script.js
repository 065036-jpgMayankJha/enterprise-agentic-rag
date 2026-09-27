const API_URL = window.RAG_API_URL || "https://enterprise-agentic-rag-65pb.onrender.com/query";

const input = document.getElementById("questionInput");
const sendBtn = document.getElementById("sendBtn");
const chat = document.getElementById("chatContainer");
const welcome = document.getElementById("welcome");
const newChatBtn = document.getElementById("newChatBtn");
const apiStatus = document.getElementById("apiStatus");

let selectedDepartment = "All";

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function addUserMessage(text) {
  if (welcome) welcome.remove();

  const el = document.createElement("div");
  el.className = "message user";
  el.innerHTML = `
    <div class="avatar">YOU</div>
    <div class="message-body">${escapeHtml(text).replace(/\n/g, "<br>")}</div>
  `;
  chat.appendChild(el);
  scrollToBottom();
}

function addTyping() {
  const el = document.createElement("div");
  el.className = "message assistant";
  el.id = "typingMessage";
  el.innerHTML = `
    <div class="avatar">ER</div>
    <div class="message-body"><div class="typing">Thinking<span id="dots">...</span></div></div>
  `;
  chat.appendChild(el);
  scrollToBottom();
}

function removeTyping() {
  document.getElementById("typingMessage")?.remove();
}

function addAssistantMessage(data) {
  removeTyping();

  const answer = data.answer || "I couldn't generate an answer.";
  const department = data.department || "Unknown";
  const sources = Array.isArray(data.sources) ? data.sources : [];

  const sourceHtml = sources.length
    ? `<details class="sources">
        <summary>📚 ${sources.length} source${sources.length === 1 ? "" : "s"}</summary>
        <div class="source-list">
          ${sources.map(s => `<div class="source-item">• ${escapeHtml(s)}</div>`).join("")}
        </div>
      </details>`
    : "";

  const el = document.createElement("div");
  el.className = "message assistant";
  el.innerHTML = `
    <div class="avatar">ER</div>
    <div class="message-body">
      <div class="answer">${window.marked ? marked.parse(answer) : escapeHtml(answer).replace(/\n/g, "<br>")}</div>
      <div class="meta">
        <span class="badge">Department: ${escapeHtml(department)}</span>
      </div>
      ${sourceHtml}
    </div>
  `;

  chat.appendChild(el);
  scrollToBottom();
}

function addError(message) {
  removeTyping();

  const el = document.createElement("div");
  el.className = "message assistant";
  el.innerHTML = `
    <div class="avatar">ER</div>
    <div class="message-body">
      <div class="answer">
        <strong>Something went wrong.</strong><br>${escapeHtml(message)}
      </div>
    </div>
  `;
  chat.appendChild(el);
  scrollToBottom();
}

async function sendQuestion(question) {
  const q = (question || input.value).trim();
  if (!q || sendBtn.disabled) return;

  input.value = "";
  input.style.height = "auto";
  addUserMessage(q);
  addTyping();

  sendBtn.disabled = true;
  apiStatus.textContent = "Processing";

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: q })
    });

    if (!response.ok) {
      throw new Error(`API returned HTTP ${response.status}`);
    }

    const data = await response.json();
    addAssistantMessage(data);
    apiStatus.textContent = "Connected";
  } catch (error) {
    apiStatus.textContent = "Connection issue";
    addError(error.message || "Unable to reach the RAG API.");
  } finally {
    sendBtn.disabled = false;
    input.focus();
  }
}

function scrollToBottom() {
  requestAnimationFrame(() => {
    chat.scrollTop = chat.scrollHeight;
  });
}

input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 140) + "px";
});

input.addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendQuestion();
  }
});

sendBtn.addEventListener("click", () => sendQuestion());

document.querySelectorAll(".suggestion").forEach(btn => {
  btn.addEventListener("click", () => sendQuestion(btn.dataset.question));
});

document.querySelectorAll(".department").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".department").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    selectedDepartment = btn.dataset.dept;
  });
});

newChatBtn.addEventListener("click", () => {
  chat.innerHTML = "";
  window.location.reload();
});
