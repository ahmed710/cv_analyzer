import os
import pytesseract
from PIL import Image
import fitz
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from queue import Queue
from threading import Thread

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# OCR function for images
def extract_text_from_image(img):
    print(f"[INFO] Performing OCR on an image.")
    return pytesseract.image_to_string(img)

# Function to extract text from a PDF using OCR if necessary
def extract_text_from_pdf(file_path):
    print(f"[INFO] Extracting text from PDF: {file_path}")
    text = ''
    with fitz.open(file_path) as doc:
        for page_num, page in enumerate(doc, start=1):
            page_text = page.get_text()
            if page_text.strip():  # Check if there's selectable text
                print(f"[INFO] Found text on page {page_num} of {file_path}")
                text += page_text
            else:  # If no selectable text, use OCR on the page image
                print(f"[INFO] No text found on page {page_num}, using OCR.")
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                text += extract_text_from_image(img)
    return text

# Function to load a resume and process it based on its type
def load_resume(file_path):
    filename = os.path.basename(file_path)
    print(f"[INFO] Loading resume: {filename}")
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
def calculate_matching_rate(resumes_batch, requirements):
    print(f"[INFO] Calculating matching rates for a batch of {len(resumes_batch)} resumes.")
    results = {}
    requirements_words = set(requirements.lower().split())
    
    for filename, resume_text in resumes_batch:
        resume_words = set(resume_text.lower().split())
        matches = resume_words.intersection(requirements_words)
        matching_rate = len(matches) / len(requirements_words) * 100  # percentage
        results[filename] = matching_rate
        print(f"[INFO] Matching rate for {filename}: {matching_rate:.2f}%")
    
    return results

def producer(queue, files, max_batch_size=10):
    """Producer function to load resumes and add them in batches to the queue."""
    batch = []
    for file in files:
        filename, content = load_resume(file)
        batch.append((filename, content))
        print(f"[INFO] Loaded {filename}. Adding to batch.")
        if len(batch) >= max_batch_size:
            print(f"[INFO] Batch of {max_batch_size} resumes ready. Adding to queue.")
            queue.put(batch)
            batch = []
    
    if batch:  # Put any remaining files in the queue
        print(f"[INFO] Final batch of {len(batch)} resumes added to queue.")
        queue.put(batch)
    
    print("[INFO] Producer finished loading all resumes.")
    queue.put(None)  # Signal completion to consumers

def consumer(queue, requirements, results):
    """Consumer function to calculate matching rates for batches of resumes."""
    while True:
        batch = queue.get()
        if batch is None:
            print("[INFO] Consumer received stop signal.")
            queue.put(None)  # Signal other consumers to stop
            break
        print(f"[INFO] Consumer processing a batch of {len(batch)} resumes.")
        batch_result = calculate_matching_rate(batch, requirements)
        results.update(batch_result)  # Store results
        queue.task_done()

def main():
    start_time = time.time()
    
    resume_dir = './resumes'
    requirements = "python, data analysis, machine learning, teamwork"
    
    files = [os.path.join(resume_dir, f) for f in os.listdir(resume_dir)]
    
    # Initialize the queue and results dictionary
    queue = Queue(maxsize=10)  # Limit queue size for memory efficiency
    results = {}

    # Start the producer thread
    print("[INFO] Starting producer thread.")
    producer_thread = Thread(target=producer, args=(queue, files))
    producer_thread.start()

    # Start consumer processes
    print("[INFO] Starting consumer processes.")
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(consumer, queue, requirements, results) for _ in range(4)]

    # Wait for the producer thread to finish
    producer_thread.join()

    # Wait for all items in the queue to be processed
    queue.join()

    # Display results
    max_rate = max(results.values())
    best_matches = [filename for filename, rate in results.items() if rate == max_rate]

    print("\nMatching rates:")
    for filename, rate in results.items():
        print(f"{filename}: {rate:.2f}% matching rate")

    print(f"\nBest candidate(s) with a matching rate of {max_rate:.2f}%:")
    for match in best_matches:
        print(f"- {match}")

    end_time = time.time()
    print(f"\nTotal execution time: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    main()
