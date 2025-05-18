
🍽️ OrderByte - Smart Food Ordering System

OrderByte is a web-based food ordering platform that provides a smooth and intuitive interface for both users and administrators. It supports menu management, ordering, invoicing, complaint handling, and Razorpay integration.

---

🚀 Features

👤 User
- Sign up / Sign in / Password reset
- Browse today's menu with categories
- Add items to cart and place orders
- Razorpay integration for secure payment
- Generate and download invoice
- View order history and cancel orders
- File complaints to the admin
- View profile and update contact info
- Search menu with filters

🛠️ Admin
- Admin-only login
- Add/Edit/Delete menu items
- Publish today's menu
- Track orders placed by users
- Respond to complaints
- Manage stock and discounts
- Admin profile page

🔐 Authentication
- Firebase Authentication for users and admin
- Email and password based sign-in

💾 Backend
- Flask (Python)
- Firebase Realtime Database

---

⚙️ Installation & Setup

1. Clone the Repository
   git clone https://github.com/Merlyn2004/OrderByte.git
   cd OrderByte

2. Create & Activate a Virtual Environment
   python -m venv venv
   source venv/bin/activate  

3. Install Dependencies
   pip install -r requirements.txt

4. Setup Firebase
   Place your Firebase credentials JSON file as:
   /serviceAccountKey.json

5. Create .env File
   In the root folder, create a file named `.env` with the following keys:

   SECRET_KEY=your_secret_key
  EMAIL_USER=your_email_user
  EMAIL_PASSWORD=your_email_password
  ADMIN_EMAIL=your_admin_email
  ADMIN_PASSWORD=your_admin_password
  FIREBASE_API_KEY=your_firebase_api_key
  FIREBASE_AUTH_DOMAIN=your_project_id.firebaseapp.com
  FIREBASE_DATABASE_URL=https://your_project_id.firebaseio.com
  FIREBASE_PROJECT_ID=your_project_id
  FIREBASE_STORAGE_BUCKET=your_project_id.appspot.com
  FIREBASE_MESSAGING_SENDER_ID=your_sender_id
  FIREBASE_APP_ID=your_app_id
  RAZORPAY_KEY_ID=your_test_key_id
  RAZORPAY_KEY_SECRET=your_test_key_secret
  EMAIL_HOST=your_email_host
  EMAIL_PORT=your_email_port
  NOTIFICATION_EMAIL=your_notification_email
  FIREBASE_PRIVATE_KEY=your_firebase_private_key
  FIREBASE_CLIENT_EMAIL=your_firebase_client_email

6. Run the App
   python app.py

---

📸 Screenshots

Created a screenshots folder you can refer that.
---

📦 Technologies Used

- Python (Flask)
- HTML, CSS, JavaScript
- Firebase (Auth + Realtime DB)
- Razorpay Payment Gateway
- Email SMTP 

---

✍️ Authors

Merlyn,Rinny,Shalin,Sneha
BTech 3rd Year Students
Mini Project: OrderByte

---

📝 License

This project is for educational/demo purposes only. All rights reserved.
