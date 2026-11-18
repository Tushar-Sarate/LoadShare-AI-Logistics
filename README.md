# 🚚 LoadShare AI Logistics

### AI-Powered Food Delivery & Logistics Management Platform

LoadShare AI Logistics is a full-stack food delivery and logistics management application designed to manage customers, restaurants, delivery partners, orders, and administrative operations through a centralized platform.

The project combines backend API development, database management, AI-powered capabilities, machine learning components, and an interactive web interface.

---

## 🚀 Key Features

### 👤 Customer Module
- Customer registration and login.
- Browse restaurants and food items.
- Search and filter restaurants.
- Place and manage food orders.
- Track order status.
- Submit complaints and receive email responses.

### 🛵 Delivery Partner Module
- Delivery partner authentication.
- View assigned delivery orders.
- Accept and manage deliveries.
- Update delivery status.
- GPS location sharing and demo trip simulation.
- Delivery history and earnings dashboard.

### 🛠️ Admin Dashboard
- Centralized order management.
- Restaurant management.
- Delivery partner management.
- Customer complaint management.
- Revenue and order analytics.
- Demand forecasting dashboard.

### 🤖 AI & Machine Learning
- AI-powered logistics capabilities.
- Retrieval-Augmented Generation (RAG).
- Document-based question answering.
- Machine learning components.
- LangGraph-based workflow implementation.

### 📍 Logistics Management
- Pincode-based delivery validation.
- City and service-area validation.
- Delivery partner assignment.
- Order status management.
- Delivery tracking.

### 📧 Email Notifications
- Email notifications.
- Complaint-related email communication.
- Admin response notifications.

---

## 🧰 Technology Stack

| Category | Technologies |
|---|---|
| Backend | Python, FastAPI |
| Frontend | HTML, CSS, JavaScript |
| Database | SQLAlchemy, SQLite/PostgreSQL (as configured) |
| Database Migration | Alembic |
| AI / LLM | LangChain, LangGraph, Groq |
| Vector Database | ChromaDB |
| Machine Learning | Python, Scikit-learn |
| Testing | Pytest |
| Environment | uv, Python Virtual Environment |
| API Documentation | Swagger UI |

---

## 📂 Project Structure

```text
LoadShare_AI_Logistics/
│
├── alembic/
├── app/
│   ├── models/
│   ├── routes/
│   ├── schemas/
│   └── services/
│
├── documents/
├── evaluation/
├── frontend/
├── ml/
├── tests/
├── logs/
├── chroma_db/
│
├── create_admin.py
├── seed_demo.py
├── seed_food.py
├── reset_db.py
├── requirements.txt
├── pyproject.toml
├── alembic.ini
├── .gitignore
└── README.md
```

---

## ⚙️ Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/Tushar-Sarate/LoadShare-AI-Logistics.git
```

### 2. Navigate to the project directory

```bash
cd LoadShare-AI-Logistics
```

### 3. Create a virtual environment

```bash
python -m venv .venv
```

### 4. Activate the environment

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure environment variables

Create a `.env` file in the project root and configure the required database credentials, secret keys, email settings, and API keys.

Never share your actual credentials publicly.

### 7. Run the application

Use the FastAPI application entry point configured in the project.

Example:

```bash
uvicorn app.main:app --reload
```

### 8. Open API documentation

```text
http://127.0.0.1:8000/docs
```

---

## 🧪 Testing

Run the test suite using:

```bash
pytest -v
```

---

## 📊 Admin Dashboard

The admin dashboard provides a centralized view of:

- Total orders and revenue.
- Delivered and pending orders.
- Orders waiting for delivery partners.
- Open customer complaints.
- Restaurant performance.
- Most ordered food items.
- Demand forecasting.

---

## 🎯 Project Objective

The objective of LoadShare AI Logistics is to develop an integrated food delivery and logistics management platform that combines automation, data-driven insights, AI capabilities, and efficient delivery operations.

---

## 👨‍💻 Developer

**Tushar Sarate**

MBA – Business Analytics

GitHub: [Tushar-Sarate](https://github.com/Tushar-Sarate)

---

⭐ If you find this project interesting, feel free to explore the repository!
