import mysql.connector
import random
import re
from getpass import getpass

def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Atharv@123",
        database="banking_system"
    )

def initialize_database():
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Atharv@123"
    )
    cursor = db.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS banking_system")
    cursor.execute("USE banking_system")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            account_number VARCHAR(10) PRIMARY KEY,
            name VARCHAR(100),
            dob DATE,
            city VARCHAR(50),
            password VARCHAR(255),
            balance DECIMAL(10, 2) CHECK (balance >= 2000),
            contact_number VARCHAR(15),
            email VARCHAR(100),
            address TEXT,
            active BOOLEAN DEFAULT TRUE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            account_number VARCHAR(10),
            type ENUM('credit', 'debit', 'transfer'),
            amount DECIMAL(10, 2),
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_number) REFERENCES users(account_number)
        )
    """)
    db.close()

def validate_password(password):
    if len(password) < 8 or not re.search(r'[A-Za-z]', password) or not re.search(r'\d', password):
        return False
    return True

def validate_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def validate_contact(contact):
    return re.match(r"\d{10}", contact)

def generate_account_number():
    return str(random.randint(1000000000, 9999999999))

def add_user():
    db = connect_db()
    cursor = db.cursor()
    name = input("Enter Name: ")
    dob = input("Enter Date of Birth (YYYY-MM-DD): ")
    city = input("Enter City: ")
    address = input("Enter Address: ")
    contact_number = input("Enter Contact Number: ")
    if not validate_contact(contact_number):
        print("Invalid contact number! Must be 10 digits.")
        return
    email = input("Enter Email: ")
    if not validate_email(email):
        print("Invalid email format!")
        return
    password = getpass("Enter Password: ")
    if not validate_password(password):
        print("Password must be at least 8 characters, contain letters and numbers.")
        return
    balance = float(input("Enter Initial Balance (Minimum 2000): "))
    if balance < 2000:
        print("Initial balance must be at least 2000.")
        return
    account_number = generate_account_number()
    try:
        cursor.execute("""
            INSERT INTO users (account_number, name, dob, city, password, balance, contact_number, email, address)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (account_number, name, dob, city, password, balance, contact_number, email, address))
        db.commit()
        print(f"User created successfully! Account Number: {account_number}")
    except Exception as e:
        print("Error adding user:", e)
    finally:
        db.close()

def show_users():
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    print("\nUsers:")
    for user in users:
        print(user)
    db.close()

def login():
    db = connect_db()
    cursor = db.cursor()
    account_number = input("Enter Account Number: ")
    password = getpass("Enter Password: ")
    cursor.execute("""
        SELECT * FROM users WHERE account_number = %s AND password = %s AND active = TRUE
    """, (account_number, password))
    user = cursor.fetchone()
    if not user:
        print("Invalid login credentials or account is deactivated.")
        return
    print(f"Welcome, {user[1]}!")
    while True:
        print("""
        1. Show Balance
        2. Show Transactions
        3. Credit Amount
        4. Debit Amount
        5. Transfer Amount
        6. Activate/Deactivate Account
        7. Change Password
        8. Update Profile
        9. Logout
        """)
        choice = input("Enter your choice: ")
        if choice == "1":
            print(f"Your current balance is: {user[5]}")
        elif choice == "2":
            cursor.execute("""
                SELECT * FROM transactions WHERE account_number = %s
            """, (account_number,))
            transactions = cursor.fetchall()
            for transaction in transactions:
                print(transaction)
        elif choice == "3":
            amount = float(input("Enter amount to credit: "))
            cursor.execute("""
                UPDATE users SET balance = balance + %s WHERE account_number = %s
            """, (amount, account_number))
            cursor.execute("""
                INSERT INTO transactions (account_number, type, amount) VALUES (%s, 'credit', %s)
            """, (account_number, amount))
            db.commit()
            print("Amount credited successfully!")
        elif choice == "4":
            amount = float(input("Enter amount to debit: "))
            if user[5] < amount:
                print("Insufficient balance!")
            else:
                cursor.execute("""
                    UPDATE users SET balance = balance - %s WHERE account_number = %s
                """, (amount, account_number))
                cursor.execute("""
                    INSERT INTO transactions (account_number, type, amount) VALUES (%s, 'debit', %s)
                """, (account_number, amount))
                db.commit()
                print("Amount debited successfully!")
        elif choice == "5":
            target_account = input("Enter target account number: ")
            amount = float(input("Enter amount to transfer: "))
            if user[5] < amount:
                print("Insufficient balance!")
            else:
                cursor.execute("""
                    UPDATE users SET balance = balance - %s WHERE account_number = %s
                """, (amount, account_number))
                cursor.execute("""
                    UPDATE users SET balance = balance + %s WHERE account_number = %s
                """, (amount, target_account))
                cursor.execute("""
                    INSERT INTO transactions (account_number, type, amount) VALUES (%s, 'transfer', %s)
                """, (account_number, amount))
                db.commit()
                print("Amount transferred successfully!")
        elif choice == "6":
            status = input("Do you want to deactivate your account? (yes/no): ").lower()
            if status == "yes":
                cursor.execute("""
                    UPDATE users SET active = FALSE WHERE account_number = %s
                """, (account_number,))
                db.commit()
                print("Account deactivated successfully!")
                break
        elif choice == "7":
            new_password = getpass("Enter new password: ")
            if not validate_password(new_password):
                print("Password must be at least 8 characters, contain letters and numbers.")
            else:
                cursor.execute("""
                    UPDATE users SET password = %s WHERE account_number = %s
                """, (new_password, account_number))
                db.commit()
                print("Password updated successfully!")
        elif choice == "8":
            city = input("Enter new city: ")
            address = input("Enter new address: ")
            cursor.execute("""
                UPDATE users SET city = %s, address = %s WHERE account_number = %s
            """, (city, address, account_number))
            db.commit()
            print("Profile updated successfully!")
        elif choice == "9":
            print("Logged out successfully!")
            break
        else:
            print("Invalid choice! Try again.")
    db.close()

def main():
    initialize_database()
    while True:
        print("""
        BANKING SYSTEM
        1. Add User
        2. Show Users
        3. Login
        4. Exit
        """)
        choice = input("Enter your choice: ")
        if choice == "1":
            add_user()
        elif choice == "2":
            show_users()
        elif choice == "3":
            login()
        elif choice == "4":
            print("Exiting... Goodbye!")
            break
        else:
            print("Invalid choice! Try again.")

if __name__ == "__main__":
    main()