const API_BASE = "https://todo-app-vuzd.onrender.com/api/v1";
let currentMode = "login";
let token = localStorage.getItem("access_token");

// Initialize state
if (token) showTodos();

function switchTab(mode) {
    currentMode = mode;
    document.getElementById("auth-error").innerText = "";
    document.getElementById("login-tab").classList.toggle("active", mode === "login");
    document.getElementById("register-tab").classList.toggle("active", mode === "register");
    document.getElementById("auth-submit-btn").innerText = mode === "login" ? "Login" : "Register";
}

async function handleAuth(event) {
    event.preventDefault();
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
    const errorElement = document.getElementById("auth-error");
    errorElement.innerText = "";

    if (currentMode === "register") {
        const res = await fetch(`${API_BASE}/auth/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });
        if (res.ok) {
            alert("Account created successfully! Please log in.");
            switchTab("login");
        } else {
            const data = await res.json();
            errorElement.innerText = data.detail || "Registration failed.";
        }
    } else {
        const formData = new URLSearchParams();
        formData.append("username", username);
        formData.append("password", password);

        const res = await fetch(`${API_BASE}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: formData
        });

        if (res.ok) {
            const data = await res.json();
            token = data.access_token;
            localStorage.setItem("access_token", token);
            showTodos();
        } else {
            errorElement.innerText = "Invalid username or password.";
        }
    }
}

async function showTodos() {
    document.getElementById("auth-section").classList.add("hidden");
    document.getElementById("todo-section").classList.remove("hidden");
    fetchTodos();
}

function logout() {
    localStorage.removeItem("access_token");
    token = null;
    document.getElementById("auth-section").classList.remove("hidden");
    document.getElementById("todo-section").classList.add("hidden");
}

function formatDate(isoString) {
    if (!isoString) return "";

    // Ensure JavaScript knows the string from SQLite is in UTC
    const utcString = (isoString.endsWith('Z') || isoString.includes('+'))
        ? isoString
        : isoString + 'Z';

    return new Date(utcString).toLocaleString('en-IN', {
        dateStyle: 'short',
        timeStyle: 'short',
        hour12: true,
        timeZone: 'Asia/Kolkata'
    });
}

let allTodos = [];

// Returns the todo's created date as YYYY-MM-DD in Asia/Kolkata, for comparing against the date filter
function getDateOnly(isoString) {
    if (!isoString) return "";
    const utcString = (isoString.endsWith('Z') || isoString.includes('+'))
        ? isoString
        : isoString + 'Z';
    return new Date(utcString).toLocaleDateString('en-CA', { timeZone: 'Asia/Kolkata' });
}

function applyDateFilter() {
    renderTodos();
}

function clearDateFilter() {
    document.getElementById("date-filter").value = "";
    renderTodos();
}

async function fetchTodos() {
    const res = await fetch(`${API_BASE}/todos`, {
        headers: { "Authorization": `Bearer ${token}` }
    });

    if (res.status === 401) { logout(); return; }

    allTodos = await res.json();
    renderTodos();
}

function renderTodos() {
    const listElement = document.getElementById("todo-list");
    const emptyMsg = document.getElementById("empty-msg");
    listElement.innerHTML = "";

    const filterDate = document.getElementById("date-filter").value;
    const todos = filterDate
        ? allTodos.filter(todo => getDateOnly(todo.created_at) === filterDate)
        : allTodos;

    emptyMsg.classList.toggle("hidden", todos.length !== 0);

    todos.forEach(todo => {
        const li = document.createElement("li");
        li.className = `todo-item ${todo.completed ? "completed" : ""}`;

        const createdText = formatDate(todo.created_at);
        const completedText = todo.completed_at ? ` | Done: ${formatDate(todo.completed_at)}` : "";

        li.innerHTML = `
            <div class="todo-info">
                <span class="todo-title ${todo.completed ? 'done' : ''}">${todo.title}</span>
                <span class="todo-timestamps">Created: ${createdText}${completedText}</span>
            </div>
            <div class="actions">
                <input type="checkbox" ${todo.completed ? 'checked' : ''} onchange="toggleTodo(${todo.id}, this.checked)">
                <button class="delete-btn" onclick="deleteTodo(${todo.id})">&times;</button>
            </div>
        `;
        listElement.appendChild(li);
    });
}

async function createTodo(event) {
    event.preventDefault();
    const input = document.getElementById("new-todo-title");
    const title = input.value;

    const res = await fetch(`${API_BASE}/todos`, {
        method: "POST",
        headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ title })
    });

    if (res.ok) {
        input.value = "";
        fetchTodos();
    }
}

async function toggleTodo(id, completed) {
    await fetch(`${API_BASE}/todos/${id}`, {
        method: "PATCH",
        headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ completed })
    });
    fetchTodos();
}

async function deleteTodo(id) {
    await fetch(`${API_BASE}/todos/${id}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
    });
    fetchTodos();
}
