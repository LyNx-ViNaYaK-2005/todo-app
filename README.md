# 📝 Timestamped To-Do Mapper
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Netlify](https://img.shields.io/badge/Netlify-00C7B7?style=for-the-badge&logo=netlify&logoColor=white)
![Render](https://img.shields.io/badge/Render-46E3B7?style=for-the-badge&logo=render&logoColor=black)


A full-stack task management application featuring user authentication, role-based access control (Admin route), and automatic task creation & completion timestamps.

🚀 **Live Frontend:** [https://todomapper.netlify.app](https://todomapper.netlify.app)  
⚡ **Live API Base:** `https://todo-app-vuzd.onrender.com/api/v1`

---

## ✨ Features

- **User Authentication:** Secure Registration and Login powered by JWT (JSON Web Tokens) and Argon2 password hashing.
- **Timestamp Tracking:** Automatically records exact creation and completion dates/times for each task.
- **Admin Access:** Role-restricted endpoint (`GET /api/v1/admin/users`) allowing admin users to view registered accounts.
- **Persistent Storage:** Cloud PostgreSQL instance ensuring data persistence across deployments.
- **CORS Enabled:** Cross-Origin Resource Sharing configured for seamless Netlify-to-Render communication.

---

## 🛠️ Tech Stack

**Backend:**
- Python 3.12+
- FastAPI
- SQLAlchemy (ORM)
- PostgreSQL (Production) / SQLite (Development)
- PyJWT & Argon2 (Security)
- Render (Backend Hosting)

**Frontend:**
- HTML5, CSS3, JavaScript (ES6+)
- Fetch API
- Netlify (Frontend Hosting)

---

## 🔌 API Endpoints

### 🔑 Authentication
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | Register a new user |
| `POST` | `/api/v1/auth/login` | Login and obtain Bearer access token |

### 📋 To-Dos (Authenticated)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/todos` | Fetch all tasks for current user |
| `POST` | `/api/v1/todos` | Create a new task |
| `PATCH` | `/api/v1/todos/{id}` | Update task status/title (sets completion timestamp) |
| `DELETE` | `/api/v1/todos/{id}` | Delete a task |

### 🛡️ Admin
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/admin/users` | Retrieve list of all users *(Admin only)* |
