import os
import pytesseract
from PIL import Image
import fitz
import time
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import simpledialog

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def load_resumes(resume_dir):
    resumes = {}
    for filename in os.listdir(resume_dir):
        file_path = os.path.join(resume_dir, filename) 
        if filename.endswith('.txt'):
            with open(file_path, 'r') as file:
                resumes[filename] = file.read()
        elif filename.endswith(('.pdf', '.jpg', '.png')):
            resumes[filename] = extract_text_from_file(file_path)
    return resumes

def extract_text_from_file(file_path):
    if file_path.endswith('.pdf'):
        text = ''
        with fitz.open(file_path) as doc:
            for page in doc:
                page_text = page.get_text()
                if page_text.strip():  # Check if there's selectable text
                    text += page_text
                else:  # If no selectable text, use OCR on the page image
                    pix = page.get_pixmap()
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    text += pytesseract.image_to_string(img)
        return text
    elif file_path.endswith(('.jpg', '.png')):
        img = Image.open(file_path)
        return pytesseract.image_to_string(img)
    return ''

def calculate_matching_rate(resume_text, requirements):
    resume_words = set(resume_text.lower().split())
    requirements_words = set(requirements.lower().split())
    
    matches = resume_words.intersection(requirements_words)
    matching_rate = len(matches) / len(requirements_words) * 100  # percentage
    return matching_rate

def analyze_resumes(resumes, requirements):
    matching_rates = {}
    for filename, resume_text in resumes.items():
        rate = calculate_matching_rate(resume_text, requirements)
        matching_rates[filename] = rate
    return matching_rates

def upload_resume():
    file_path = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf"), ("Image files", "*.jpg;*.png"), ("Text files", "*.txt")])
    if file_path:
        # Save file to the "resumes" folder
        resume_dir = './resumes'
        os.makedirs(resume_dir, exist_ok=True)
        filename = os.path.basename(file_path)
        new_path = os.path.join(resume_dir, filename)
        with open(file_path, 'rb') as f:
            with open(new_path, 'wb') as new_f:
                new_f.write(f.read())
        messagebox.showinfo("Success", f"Resume {filename} uploaded successfully.")

def add_requirement():
    new_requirement = simpledialog.askstring("Add Requirement", "Enter a new requirement:")
    if new_requirement:
        current_requirements.set(current_requirements.get() + ", " + new_requirement)
        messagebox.showinfo("Requirement Added", f"New requirement '{new_requirement}' added.")

def run_analysis():
    global start_time
    start_time = time.time()  # Start the execution timer

    requirements = current_requirements.get()
    resume_dir = './resumes'

    load_start = time.time()
    resumes = load_resumes(resume_dir)
    load_end = time.time()
    load_time = load_end - load_start
    
    analyze_start = time.time()
    matching_rates = analyze_resumes(resumes, requirements)
    analyze_end = time.time()
    analyze_time = analyze_end - analyze_start

    total_time = analyze_end - start_time

    # Display results in the console
    print("\n--- Analysis Results ---")
    for filename, rate in matching_rates.items():
        print(f"{filename}: {rate:.2f}% matching rate")

    max_rate = max(matching_rates.values())
    best_matches = [filename for filename, rate in matching_rates.items() if rate == max_rate]
    print(f"\nBest candidate(s) with a matching rate of {max_rate:.2f}%:")
    for match in best_matches:
        print(f"- {match}")

    # Display statistics in the console
    print("\n--- Execution Statistics ---")
    print(f"Loading Time: {load_time:.2f} seconds")
    print(f"Analysis Time: {analyze_time:.2f} seconds")
    print(f"Total Execution Time: {total_time:.2f} seconds")

    # Display results in the GUI
    result_text.set("")
    for filename, rate in matching_rates.items():
        result_text.set(result_text.get() + f"{filename}: {rate:.2f}% matching rate\n")

    max_rate = max(matching_rates.values())
    best_matches = [filename for filename, rate in matching_rates.items() if rate == max_rate]
    result_text.set(result_text.get() + f"\nBest candidate(s) with a matching rate of {max_rate:.2f}%:\n")
    for match in best_matches:
        result_text.set(result_text.get() + f"- {match}\n")

    # Display execution times in the GUI
    stats_text.set(f"Loading Time: {load_time:.2f} seconds\n"
                   f"Analysis Time: {analyze_time:.2f} seconds\n"
                   f"Total Execution Time: {total_time:.2f} seconds")

# Create the GUI window
root = tk.Tk()
root.title("Resume Analyzer")
root.geometry("600x600")
root.config(bg="#f4f4f9")

# Current requirements variable
current_requirements = tk.StringVar()
current_requirements.set("python, data analysis, machine learning, teamwork")

# Main Frame
main_frame = tk.Frame(root, bg="#f4f4f9")
main_frame.pack(padx=20, pady=20, fill="both", expand=True)

# Add title label
title_label = tk.Label(main_frame, text="Resume Analyzer", font=("Helvetica", 24, "bold"), fg="#4A90E2", bg="#f4f4f9")
title_label.pack(pady=10)

# Add a label for current requirements
tk.Label(main_frame, text="Current Requirements:", font=("Helvetica", 12), fg="#333", bg="#f4f4f9").pack(padx=10, pady=5)
tk.Label(main_frame, textvariable=current_requirements, wraplength=500, font=("Helvetica", 10), fg="#333", bg="#f4f4f9").pack(padx=10, pady=5)

# Buttons frame
button_frame = tk.Frame(main_frame, bg="#f4f4f9")
button_frame.pack(pady=20)

# Add a button to upload resumes
upload_button = tk.Button(button_frame, text="Upload Resume", command=upload_resume, width=20, height=2, font=("Helvetica", 12), bg="#4CAF50", fg="white", relief="raised", bd=2)
upload_button.grid(row=0, column=0, padx=10, pady=5)

# Add a button to add a requirement
add_req_button = tk.Button(button_frame, text="Add Requirement", command=add_requirement, width=20, height=2, font=("Helvetica", 12), bg="#FFA500", fg="white", relief="raised", bd=2)
add_req_button.grid(row=0, column=1, padx=10, pady=5)

# Add a button to run the analysis
run_button = tk.Button(button_frame, text="Run Analysis", command=run_analysis, width=20, height=2, font=("Helvetica", 12), bg="#4A90E2", fg="white", relief="raised", bd=2)
run_button.grid(row=1, column=0, columnspan=2, pady=10)

# Add a label for the analysis results
result_text = tk.StringVar()
result_output = tk.Label(main_frame, textvariable=result_text, anchor="w", justify="left", font=("Helvetica", 10), fg="#333", bg="#f4f4f9", relief="solid", padx=10, pady=10, width=60, height=10)
result_output.pack(padx=10, pady=10)

# Add a frame for statistics
stats_frame = tk.Frame(main_frame, bg="#f4f4f9", pady=10)
stats_frame.pack(fill="x")

# Add a label for the statistics
stats_text = tk.StringVar()
stats_label = tk.Label(stats_frame, textvariable=stats_text, font=("Helvetica", 10), fg="#333", bg="#f4f4f9", anchor="w", justify="left")
stats_label.pack(padx=10)

# Run the GUI main loop
root.mainloop()
