USE ar_dashboard;

------------------------------------------------------------
-- 1. Insert Customers (must be first)
------------------------------------------------------------
INSERT INTO customers (name, email, phone) VALUES
('Alice Johnson', 'alice@example.com', '123-456-7890'),
('Bob Smith', 'bob@example.com', '987-654-3210'),
('Charlie Davis', 'charlie@example.com', '555-222-3333'),
('Diana Prince', 'diana@example.com', '444-555-6666'),
('Edward King', 'edward@example.com', '222-111-9999'),
('Fiona Clark', 'fiona@example.com', '888-777-6666'),
('George White', 'george@example.com', '999-888-5555'),
('Helen Brown', 'helen@example.com', '777-666-4444');

-- Now customer_id 1 → Alice, 2 → Bob, 3 → Charlie, … up to 8 → Helen

------------------------------------------------------------
-- 2. Insert Invoices (must come after customers)
------------------------------------------------------------
INSERT INTO invoices (customer_id, invoice_date, due_date, amount, status) VALUES
(1, '2025-01-01', '2025-01-15', 500.00, 'Pending'),
(2, '2025-01-05', '2025-01-20', 750.00, 'Paid'),
(3, '2025-01-10', '2025-01-25', 300.00, 'Overdue'),
(4, '2025-02-01', '2025-02-15', 1200.00, 'Pending'),
(5, '2025-02-10', '2025-02-28', 950.00, 'Paid'),
(6, '2025-03-01', '2025-03-15', 450.00, 'Pending'),
(7, '2025-03-05', '2025-03-20', 1350.00, 'Overdue'),
(8, '2025-03-15', '2025-03-30', 700.00, 'Pending'),
(1, '2025-04-10', '2025-04-25', 650.00, 'Overdue'),
(2, '2025-05-01', '2025-05-15', 900.00, 'Pending'),
(3, '2025-05-05', '2025-05-20', 500.00, 'Overdue');

-- These will automatically get invoice_id = 1, 2, 3, 4, ...

------------------------------------------------------------
-- 3. Insert Payments (must come after invoices)
------------------------------------------------------------

ALTER TABLE payments 
MODIFY method ENUM('Cash', 'Credit Card', 'Bank Transfer', 'UPI') NOT NULL;

INSERT INTO payments (invoice_id, payment_date, amount, method) VALUES
(2, '2025-01-10', 750.00, 'Credit Card'), -- full payment for Bob’s first invoice
(3, '2025-02-01', 100.00, 'Bank Transfer'), -- partial for Charlie
(5, '2025-02-15', 950.00, 'Cash'),           -- full payment
(7, '2025-03-25', 500.00, 'Credit Card'),    -- partial
(9, '2025-04-15', 300.00, 'Cash'),           -- partial for Alice’s 2nd invoice
(10, '2025-05-10', 400.00, 'UPI');           -- partial for Bob’s 2nd invoice

