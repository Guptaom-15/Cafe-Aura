🍽️ Café Aura – POS System (Python + Tkinter + MongoDB)

Café Aura ek Python-based Point of Sale (POS) desktop application hai jo cafés, restaurants, aur fast-food outlets ke liye design kiya gaya hai.
Yeh application Tkinter ka use karke GUI provide karta hai aur orders ko MongoDB me save karta hai for future reference.

✨ Key Features
1. Category-wise Menu Display

Pre-defined menu categories:

Pizza

Maggie

Burger

Sandwich

Drinks

Desserts

Coffee & Shakes

Fries & Sides

Pasta

Har category ke items ke sath price aur quantity selector.

2. Cart Management

Items add/remove karne ka option

Same item multiple times add karne par quantity auto-update hoti hai

"Clear Cart" option to reset order instantly

3. Automatic Tax Calculation

SGST (9%) & CGST (9%) auto-calculated

Configurable in the code for different tax rates

4. Billing & Receipt

Professional receipt format with:

Order ID

Date/Time

Customer Name & Phone

Itemized list with price & quantity

Subtotal, Taxes, and Grand Total

Option to save receipt as .txt file

5. MongoDB Integration

All orders automatically stored in a MongoDB collection

Orders can be retrieved later using View Old Orders option

Double-click on order to view complete details

6. Order History Viewer

Displays last 500 orders in a table view

Includes search & sorting by Order ID, Date, Customer, etc.

🛠️ Tech Stack

Programming Language: Python 3.x

GUI Framework: Tkinter

Database: MongoDB

🖼️ Screenshots

1️⃣ Order Screen (POS Interface)
<img width="1435" height="933" alt="Screenshot 2025-08-16 002133" src="https://github.com/user-attachments/assets/b988e0ca-9399-4f71-b44b-5ca1e2c4b516" />

2️⃣ Generated Bill (Receipt Window)
<img width="889" height="743" alt="Screenshot 2025-08-16 002150" src="https://github.com/user-attachments/assets/3b32f7c2-6900-43db-910a-56ba07ba141b" />

3️⃣ Orders in MongoDB
<img width="1767" height="1035" alt="Screenshot 2025-08-16 002248" src="https://github.com/user-attachments/assets/753de5fa-df51-4cee-a88c-00aa5e07e406" />
