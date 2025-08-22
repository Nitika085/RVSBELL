# Accounts Receivable Dashboard

This project is a simple **Accounts Receivable (AR) Dashboard** built with **Flask (Python)** and **MySQL**. The main goal is to help track customers, invoices, and payments in a structured way. It provides REST API endpoints that allow you to interact with the data easily.

The system revolves around three key parts:

1. **Customers** People or companies who buy services/products.
2. **Invoices** Bills raised for customers.
3. **Payments** Records of money received against invoices.

By combining these, the dashboard helps monitor pending, paid, and overdue invoices.

---

## How the Project Works

1. **Database Setup**

   - The project uses a MySQL database named `ar_dashboard`.
   - It has three main tables:
     - `customers` â†’ Stores customer info like name, email, and phone.
     - `invoices` â†’ Stores invoice details like amount, due date, and status.
     - `payments` â†’ Tracks payments received for invoices.
   - Foreign key relationships ensure that invoices link to customers, and payments link to invoices.

2. **Flask Backend**

   - A Flask server is used to provide API routes.
   - When you hit a route, Flask connects to MySQL using `mysql.connector` and fetches or inserts data.
   - Responses are returned in **JSON** format.

3. **Purpose**
   - Helps businesses keep track of:
     - Who owes them money (Pending invoices)
     - Which invoices are overdue
     - Which customers have paid
     - How much payment has been received

---

## API Routes

Here are the main routes available:
-main page
![Dashboard Screenshot](ist.png)

### 1. Customers

- **`/customers`** (GET) Returns a list of all customers with their IDs and names.
- Example Response:
  ```json
  [
    { "customer_id": 1, "name": "Alice Johnson" },
    { "customer_id": 2, "name": "Bob Smith" }
  ]
  ```
  ![Dashboard Screenshot](4th.png)

### 2. Invoices

- **`/invoices`** (GET) Returns all invoices with details such as amount, status, and due date.
- Example Response:
  ```json
  [
    { "invoice_id": 1, "customer_id": 1, "amount": 500.0, "status": "Pending" },
    { "invoice_id": 2, "customer_id": 2, "amount": 750.0, "status": "Paid" }
  ]
  ```
  ![Dashboard Screenshot](3rd.png)

### 3. top5

- **`/top5`** (GET) Returns all top5 payments that have been recorded against invoices.
- Example Response:
  ```json
  [
    {
      "payment_id": 1,
      "invoice_id": 2,
      "amount": 750.0,
      "method": "Credit Card"
    },
    {
      "payment_id": 2,
      "invoice_id": 3,
      "amount": 100.0,
      "method": "Bank Transfer"
    }
  ]
  ```
  ![Dashboard Screenshot](5th.png)

### 4. kpis

- **`/kpis`** (GET) Returns KPI metrics (e.g., totals, overdue amounts, etc.)..
  ![Dashboard Screenshot](2nd.png)

---

## How Routes Work

- When you send a request to `/customers`, Flask runs a SQL query like:

  ```sql
  SELECT customer_id, name FROM customers ORDER BY name;
  ```

  and sends back the result as JSON.

- For `/invoices`, it pulls all invoice rows and shows customer linkage.

- For `/top5`, it fetches all payments and shows top5 customers.

This way, the API serves as a bridge between the MySQL database and any frontend/dashboard you want to build on top of it.

---

## Running the Project

1. Install dependencies:

   ```bash
   pip install flask flask-cors mysql-connector-python python-dotenv
   ```

2. Make sure MySQL is running and youâ€™ve created the database:

   ```sql
   CREATE DATABASE ar_dashboard;
   ```

3. Run the Flask app:

   ```bash
   python app.py
   ```

4. Visit the API in your browser or use a tool like Postman:
   - `http://127.0.0.1:5000/customers`
   - `http://127.0.0.1:5000/invoices`
   - `http://127.0.0.1:5000/payments`

---

## Summary

This project is a **mini accounting backend**. It keeps track of customers, invoices, and payments. The Flask APIs let you query this data easily, so it can be used to build dashboards or reports.
