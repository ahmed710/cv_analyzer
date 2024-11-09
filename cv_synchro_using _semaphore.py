import os
import pytesseract
from PIL import Image
import fitz
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from multiprocessing import Semaphore

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# OCR function for images
def extract_text_from_image(img):
    return pytesseract.image_to_string(img)

# Function to extract text from a PDF using OCR if necessary
def extract_text_from_pdf(file_path):
    text = ''
    with fitz.open(file_path) as doc:
        for page in doc:
            page_text = page.get_text()
            if page_text.strip():  # Check if there's selectable text
                text += page_text
            else:  # If no selectable text, use OCR on the page image
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                text += extract_text_from_image(img)
    return text

# Function to load a resume and process it based on its type
def load_resume(file_path, semaphore):
    """Loads a single resume, using OCR only if necessary."""
    with semaphore:  # Ensure that only a limited number of threads access this block at once
        filename = os.path.basename(file_path)
        if filename.endswith('.txt'):
            with open(file_path, 'r') as file:
                return filename, file.read()
        elif filename.endswith(('.pdf', '.jpg', '.png')):
            if filename.endswith('.pdf'):
                return filename, extract_text_from_pdf(file_path)
            else:
                img = Image.open(file_path)
                return filename, extract_text_from_image(img)
        return filename, ''

# Function to calculate matching rate for a resume
def calculate_matching_rate_for_resume(filename, resume_text, requirements):
    """Calculate matching rate for a resume."""
    resume_words = set(resume_text.lower().split())
    requirements_words = set(requirements.lower().split())
    matches = resume_words.intersection(requirements_words)
    matching_rate = len(matches) / len(requirements_words) * 100  # percentage
    return filename, matching_rate

def main():
    start_time = time.time()
    
    print('Entered the model')
    resume_dir = './resumes'  
    requirements = "python, data analysis, machine learning, teamwork"  
    
    files = [os.path.join(resume_dir, f) for f in os.listdir(resume_dir)]
    
    # Create a semaphore to limit access to critical sections in threads
    semaphore = Semaphore(2)  # Limit to 2 concurrent threads for I/O-bound tasks
    resumes = {}

    load_start = time.time()
    
    # Using ThreadPoolExecutor to load files in parallel (I/O bound task)
    with ThreadPoolExecutor() as executor:
        future_to_file = {executor.submit(load_resume, file, semaphore): file for file in files}
        for future in as_completed(future_to_file):
            filename, content = future.result()
            resumes[filename] = content
    load_end = time.time()
    print(f"Loading resumes took {load_end - load_start:.2f} seconds")

    analyze_start = time.time()
    matching_rates = {}

    # Using ProcessPoolExecutor to calculate matching rates in parallel (CPU bound task)
    with ProcessPoolExecutor() as executor:
        future_to_resume = {executor.submit(calculate_matching_rate_for_resume, filename, resume_text, requirements): filename 
                            for filename, resume_text in resumes.items()}
        for future in as_completed(future_to_resume):
            filename, rate = future.result()
            matching_rates[filename] = rate
    analyze_end = time.time()
    print(f"Analyzing resumes took {analyze_end - analyze_start:.2f} seconds")

    # Display the matching rates in the console
    for filename, rate in matching_rates.items():
        print(f"{filename}: {rate:.2f}% matching rate")

    max_rate = max(matching_rates.values())
    best_matches = [filename for filename, rate in matching_rates.items() if rate == max_rate]

    print(f"\nBest candidate(s) with a matching rate of {max_rate:.2f}%:")
    for match in best_matches:
        print(f"- {match}")
    
    end_time = time.time()
    total_time = end_time - start_time
    print(f"\nTotal execution time: {total_time:.2f} seconds")

if __name__ == "__main__":
    main()
