import tkinter as tk
from tkinter import ttk
import json
from utils import *

def save_data():
    # Get the input data from the text entry fields
    data = {}
    for key, entry in entry_widgets.items():
        value = entry.get()
        data[key] = [value]

    # Save the data to a file
    with open('da.json', 'w') as file:
        json.dump(data, file)

    print("Data saved successfully.")

def add_key_value():
    # Get the number of existing key-value pairs
    num_pairs = len(entry_widgets)

    # Create label and entry widgets for the new key-value pair
    new_key = num_pairs + 1

    label = ttk.Label(scrollable_frame, text=f"Câu {new_key}:")
    label.pack()

    entry = ttk.Entry(scrollable_frame)
    entry.pack()

    # Store the entry widget in the dictionary
    entry_widgets[new_key] = entry

    # Update the scroll region
    canvas.update_idletasks()
    canvas.configure(scrollregion=canvas.bbox("all"))

# Create a Tkinter window
window = tk.Tk()
window.title("Input Data")
window.geometry("300x300")

# Create a topbar frame
topbar_frame = ttk.Frame(window)
topbar_frame.pack(side=tk.TOP, fill=tk.X)

# Create a button to add a new key-value pair
add_button = ttk.Button(topbar_frame, text="Add Key-Value", command=add_key_value)
add_button.pack(side=tk.LEFT)

# Create a button to save the data
save_button = ttk.Button(topbar_frame, text="Save Data", command=save_data)
save_button.pack(side=tk.LEFT)

# Create a scrollable frame to hold the key-value pairs
canvas = tk.Canvas(window, height=250)
canvas.pack(fill=tk.BOTH, expand=True)

scrollbar = ttk.Scrollbar(window, orient=tk.VERTICAL, command=canvas.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

canvas.configure(yscrollcommand=scrollbar.set)
canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

scrollable_frame = ttk.Frame(canvas)
canvas.create_window((0, 0), window=scrollable_frame, anchor=tk.NW)

# Create a dictionary to hold the entry widgets
entry_widgets = {}

da = read_da_from_file('da.json')

if(da):
    # Create label and entry widgets for each key-value pair in 'da'
    for key, value in da.items():
        label = ttk.Label(scrollable_frame, text=f"Câu {key}:")
        label.pack()

        entry = ttk.Entry(scrollable_frame)
        entry.pack()

        # If the 'da' variable already has a value, set it as the default value in the entry widget
        if len(value) > 0:
            entry.insert(tk.END, value[0])

        # Store the entry widget in the dictionary
        entry_widgets[key] = entry

# Enable mouse wheel scrolling
def on_mousewheel(event):
    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

canvas.bind_all("<MouseWheel>", on_mousewheel)

# Start the Tkinter event loop
window.mainloop()