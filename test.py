import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
import re


# Database setup
def setup_db():
    conn = sqlite3.connect('customer_records.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    contact_number TEXT,
                    device_type TEXT,
                    description TEXT,
                    issue TEXT,
                    quote TEXT
                )''')

    conn.commit()
    conn.close()


# Add record to the database
def add_record(name, contact_number, device_type, description, issue, quote):
    conn = sqlite3.connect('customer_records.db')
    c = conn.cursor()

    try:
        c.execute(
            'INSERT INTO customers (name, contact_number, device_type, description, issue, quote) VALUES (?, ?, ?, ?, ?, ?)',
            (name, contact_number, device_type, description, issue, quote))
        conn.commit()
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"An error occurred: {e}")
    finally:
        conn.close()


# Load customer record list
def load_customer_list():
    conn = sqlite3.connect('customer_records.db')
    c = conn.cursor()
    c.execute('SELECT id, name FROM customers ORDER BY id')
    records = c.fetchall()
    conn.close()

    # Prompt user to select a customer
    customer_list_window = tk.Toplevel(root)
    customer_list_window.title("Select Customer")

    tk.Label(customer_list_window, text="Select a Customer:").pack(pady=10)

    customer_dropdown = ttk.Combobox(customer_list_window, values=[f"ID {row[0]}: {row[1]}" for row in records])
    customer_dropdown.pack(pady=10)

    def load_selected_record():
        selected_text = customer_dropdown.get()
        if selected_text:
            customer_id = int(selected_text.split(":")[0].split()[1])
            conn = sqlite3.connect('customer_records.db')
            c = conn.cursor()
            c.execute('SELECT name, contact_number, device_type, description, issue, quote FROM customers WHERE id = ?',
                      (customer_id,))
            record = c.fetchone()
            conn.close()

            if record:
                name_entry.config(state=tk.NORMAL)
                name_entry.delete(0, tk.END)
                name_entry.insert(0, record[0])
                name_entry.config(state='readonly')

                contact_number_entry.config(state=tk.NORMAL)
                contact_number_entry.delete(0, tk.END)
                contact_number_entry.insert(0, record[1])
                contact_number_entry.config(state='readonly')

                device_type_dropdown.set(record[2])
                device_type_dropdown.config(state='disabled')  # Grey out Device Type Dropdown

                description_entry.config(state=tk.NORMAL)
                description_entry.delete(0, tk.END)
                description_entry.insert(0, record[3])
                description_entry.config(state='readonly')

                issue_entry.config(state=tk.NORMAL)
                issue_entry.delete(0, tk.END)
                issue_entry.insert(0, record[4])
                issue_entry.config(state='readonly')

                # Ensure that the quote is displayed with the $ symbol
                quote_entry.config(state=tk.NORMAL)
                quote_entry.delete(0, tk.END)
                quote_entry.insert(0, f"${record[5]}")
                quote_entry.config(state='readonly')

            customer_list_window.destroy()

    tk.Button(customer_list_window, text="Load Record", command=load_selected_record).pack(pady=10)


# Validation functions
def validate_alphabetic_input(char):
    return bool(re.match("^[a-zA-Z\s]*$", char))  # Allows alphabetic characters and spaces


def validate_numeric_input(char):
    return bool(re.match("^[0-9]*$", char))


def validate_submit():
    name = name_entry.get()
    contact_number = contact_number_entry.get()
    device_type = device_type_dropdown.get()
    description = description_entry.get()
    issue = issue_entry.get()
    quote = quote_entry.get()

    if not all([name, contact_number, device_type, description, issue, quote]):
        messagebox.showwarning("Input Error", "All fields must be filled.")
        return False

    if not validate_alphabetic_input(name) or not validate_alphabetic_input(
            description) or not validate_alphabetic_input(issue):
        messagebox.showwarning("Input Error",
                               "Name, Description, and Issue fields must contain only alphabetic characters and spaces.")
        return False

    if not validate_numeric_input(contact_number) or not validate_numeric_input(quote.replace("$", "")):
        messagebox.showwarning("Input Error", "Contact Number and Quote fields must contain only numeric characters.")
        return False

    return True


# Submit button action
def submit():
    if validate_submit():
        name = name_entry.get()
        contact_number = contact_number_entry.get()
        device_type = device_type_dropdown.get()
        description = description_entry.get()
        issue = issue_entry.get()
        quote = quote_entry.get().replace("$", "")  # Remove $ symbol for storage

        add_record(name, contact_number, device_type, description, issue, quote)
        messagebox.showinfo("Success", "Record added successfully!")
        clear_form()


# Clear button action
def clear_form():
    name_entry.config(state=tk.NORMAL)
    name_entry.delete(0, tk.END)
    contact_number_entry.config(state=tk.NORMAL)
    contact_number_entry.delete(0, tk.END)
    device_type_dropdown.config(state=tk.NORMAL)
    device_type_dropdown.set("Select Device")
    description_entry.config(state=tk.NORMAL)
    description_entry.delete(0, tk.END)
    issue_entry.config(state=tk.NORMAL)
    issue_entry.delete(0, tk.END)
    quote_entry.config(state=tk.NORMAL)
    quote_entry.delete(0, tk.END)
    quote_entry.insert(0, "$")
    customer_list_button.config(state=tk.NORMAL)


# Setup the database
setup_db()

# Create the main window
root = tk.Tk()
root.title("Customer Record System")

# Create and place labels and entries
tk.Label(root, text="Name").grid(row=0, column=0, padx=10, pady=5)
name_entry = tk.Entry(root, validate="key")
name_entry.grid(row=0, column=1, padx=10, pady=5)
name_entry['validatecommand'] = (root.register(validate_alphabetic_input), '%S')

tk.Label(root, text="Contact Number").grid(row=1, column=0, padx=10, pady=5)
contact_number_entry = tk.Entry(root, validate="key")
contact_number_entry.grid(row=1, column=1, padx=10, pady=5)
contact_number_entry['validatecommand'] = (root.register(validate_numeric_input), '%S')

# Device Type Dropdown
tk.Label(root, text="Device Type").grid(row=2, column=0, padx=10, pady=5)
device_type_dropdown = ttk.Combobox(root, values=["Phone", "IPAD", "Computer"], state="readonly")
device_type_dropdown.grid(row=2, column=1, padx=10, pady=5)

tk.Label(root, text="Description").grid(row=3, column=0, padx=10, pady=5)
description_entry = tk.Entry(root, validate="key")
description_entry.grid(row=3, column=1, padx=10, pady=5)
description_entry['validatecommand'] = (root.register(validate_alphabetic_input), '%S')

tk.Label(root, text="Issue").grid(row=4, column=0, padx=10, pady=5)
issue_entry = tk.Entry(root, validate="key")
issue_entry.grid(row=4, column=1, padx=10, pady=5)
issue_entry['validatecommand'] = (root.register(validate_alphabetic_input), '%S')

tk.Label(root, text="Quote").grid(row=5, column=0, padx=10, pady=5)
quote_entry = tk.Entry(root, validate="key")
quote_entry.grid(row=5, column=1, padx=10, pady=5)
quote_entry.insert(0, "$")
quote_entry['validatecommand'] = (root.register(validate_numeric_input), '%S')

# Create and place the "Previous Records" button
customer_list_button = tk.Button(root, text="Previous Records", command=load_customer_list)
customer_list_button.grid(row=6, column=0, columnspan=2, padx=10, pady=10)

# Create and place buttons
submit_button = tk.Button(root, text="Submit", command=submit)
submit_button.grid(row=7, column=0, padx=10, pady=10)

clear_button = tk.Button(root, text="Clear", command=clear_form)
clear_button.grid(row=7, column=1, padx=10, pady=10)

root.mainloop()
