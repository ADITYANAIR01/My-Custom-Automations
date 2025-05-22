import os
import logging
import pdfplumber
import pytesseract
import pdf2image
import requests
import ollama
import json
import time

# Windows-specific: Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

def setup_logging():
    """Setup logging to file."""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "automation_log.txt")
    logging.basicConfig(filename=log_file, level=logging.INFO, 
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("Logging setup complete")

def download_pdf(pdf_url, temp_dir):
    """Download PDF from URL to temp directory."""
    temp_pdf_path = os.path.join(temp_dir, "temp_file.pdf")
    for attempt in range(3):
        try:
            response = requests.get(pdf_url, timeout=10)
            with open(temp_pdf_path, "wb") as f:
                f.write(response.content)
            logging.info("PDF downloaded successfully")
            return temp_pdf_path
        except Exception as e:
            logging.warning(f"Download attempt {attempt + 1} failed: {str(e)}")
            time.sleep(2)
    logging.error("Failed to download PDF after retries")
    return None

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using pdfplumber or OCR."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = "".join(page.extract_text() or "" for page in pdf.pages)
        if not text.strip():
            raise ValueError("No text extracted with pdfplumber")
        logging.info("Text extracted using pdfplumber")
    except Exception:
        logging.info("Falling back to OCR for text extraction")
        try:
            images = pdf2image.convert_from_path(pdf_path)
            text = "".join(pytesseract.image_to_string(image) for image in images)
            logging.info("Text extracted using OCR")
        except Exception as e:
            logging.error(f"Failed to extract text: {str(e)}")
            raise
    text = " ".join(text.split())
    logging.info(f"Extracted text: {text[:100]}...")
    return text

def parse_text_with_ollama(text, model):
    """Parse text using Ollama to extract fields."""
    try:
        prompt = (
            "Extract the following fields from this resume: First Name, Middle Name, Last Name, Gender, "
            "Date of Birth, Nationality, Maritial Status, Passport, Hobbies, Languages Known, Address, Landmark, "
            "City, State, Pin Code, Mobile, Email Id, SSC Result, SSC Board/University, SSC Passing Year, "
            "HSC Result, HSC Board/University, HSC Passing Year, Diploma, Graduation Degree, Graduation Result, "
            "Graduation University, Graduation Year, Post-Graduation Degree, Post-Graduation Result, "
            "Post-Graduation University, Post-Graduation Year, Highest Level of Education, Total Work Exp (Years), "
            "Total Work Exp (Month), Total Companies worked for, Last/Current Employer. "
            "Return the results in JSON format. If a field is missing, set its value to null."
        )
        response = ollama.chat(model=model, messages=[
            {"role": "user", "content": f"{prompt}\n\n{text}"}
        ])
        parsed_data = json.loads(response["message"]["content"])
        logging.info(f"Parsed data: {parsed_data}")
        return parsed_data
    except Exception as e:
        logging.error(f"Failed to parse text with Ollama: {str(e)}")
        return {
            "First Name": None, "Middle Name": None, "Last Name": None, "Gender": None,
            "Date of Birth": None, "Nationality": None, "Maritial Status": None, "Passport": None,
            "Hobbies": None, "Languages Known": None, "Address": None, "Landmark": None,
            "City": None, "State": None, "Pin Code": None, "Mobile": None, "Email Id": None,
            "SSC Result": None, "SSC Board/University": None, "SSC Passing Year": None,
            "HSC Result": None, "HSC Board/University": None, "HSC Passing Year": None,
            "Diploma": None, "Graduation Degree": None, "Graduation Result": None,
            "Graduation University": None, "Graduation Year": None, "Post-Graduation Degree": None,
            "Post-Graduation Result": None, "Post-Graduation University": None,
            "Post-Graduation Year": None, "Highest Level of Education": None,
            "Total Work Exp (Years)": None, "Total Work Exp (Month)": None,
            "Total Companies worked for": None, "Last/Current Employer": None
        }
