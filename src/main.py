import time
import os
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from config import LOGIN_URL, WORK_URL, USERNAME, PASSWORD, FORM_FIELDS, OLLAMA_MODEL
from utils import setup_logging, download_pdf, extract_text_from_pdf, parse_text_with_ollama

# Setup directories
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
TEMP_DIR = os.path.join(BASE_DIR, "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

# Setup logging
setup_logging()

# Initialize Selenium WebDriver
# Make sure chromedriver is in PATH
options = webdriver.ChromeOptions()
options.add_argument('--start-maximized')
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 10)

# Step 1: Logging into the Website
logging.info("Starting login process")
try:
    driver.get(LOGIN_URL)
    username_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
    password_field = wait.until(EC.presence_of_element_located((By.ID, "password")))
    username_field.send_keys(USERNAME)
    password_field.send_keys(PASSWORD)
    login_button = wait.until(EC.element_to_be_clickable((By.ID, "login_button")))
    login_button.click()
    wait.until(EC.url_contains("/dashboard"))
    logging.info("Login successful")
except Exception as e:
    logging.error(f"Login failed: {str(e)}")
    driver.quit()
    raise SystemExit("Login failed. Check credentials or website status.")

# Step 2: Navigating to the Work Section
logging.info("Navigating to Work section")
try:
    driver.get(WORK_URL)
    wait.until(EC.presence_of_element_located((By.XPATH, "//table")))
    logging.info("Successfully navigated to Work section")
except Exception as e:
    logging.error(f"Failed to navigate to Work section: {str(e)}")
    driver.quit()
    raise SystemExit("Navigation to Work section failed.")

# Step 3: Selecting a Job
logging.info("Selecting a job with pending files")
try:
    job_rows = driver.find_elements(By.XPATH, "//table/tbody/tr")
    job_selected = False
    for row in job_rows:
        submission_status = row.find_element(By.XPATH, "./td[4]").text
        if not submission_status:
            go_to_job_link = row.find_element(By.LINK_TEXT, "Go To Job")
            go_to_job_link.click()
            job_selected = True
            logging.info("Selected job with pending files")
            break
    if not job_selected:
        logging.warning("No jobs with pending files found")
        driver.quit()
        raise SystemExit("No pending jobs found.")
except Exception as e:
    logging.error(f"Failed to select a job: {str(e)}")
    driver.quit()
    raise SystemExit("Job selection failed.")

# Step 4 and Step 6: Accessing File List and Processing Files One by One
while True:
    logging.info("Accessing file list and selecting a pending file")
    try:
        file_rows = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//table/tbody/tr")))
        file_selected = False

        for row in file_rows:
            status = row.find_element(By.XPATH, "./td[4]").text
            if status.lower() == "pending":
                file_number = row.find_element(By.XPATH, "./td[1]").text
                logging.info(f"Selected File No. {file_number} with status Pending")
                go_to_work_link = row.find_element(By.LINK_TEXT, "Go To Work")
                go_to_work_link.click()
                file_selected = True
                break

        if not file_selected:
            try:
                next_button = driver.find_element(By.LINK_TEXT, "Next")
                if "disabled" not in next_button.get_attribute("class"):
                    next_button.click()
                    time.sleep(2)
                    continue
                else:
                    logging.info("No more pending files found")
                    break
            except NoSuchElementException:
                logging.info("No more pending files found")
                break

        # Sub-Step 5.1: Clicking "Go To Work" (already done above)

        # Sub-Step 5.2: Extracting the PDF URL
        logging.info("Extracting PDF URL")
        try:
            iframe = wait.until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
            pdf_url = iframe.get_attribute("src")
            logging.info(f"PDF URL extracted: {pdf_url}")
        except Exception as e:
            logging.error(f"Failed to extract PDF URL: {str(e)}")
            driver.back()
            continue

        # Sub-Step 5.3: Downloading the PDF
        logging.info("Downloading PDF")
        temp_pdf_path = download_pdf(pdf_url, TEMP_DIR)
        if not temp_pdf_path:
            driver.back()
            continue

        # Sub-Step 5.4: Extracting Text from the PDF
        logging.info("Extracting text from PDF")
        try:
            text = extract_text_from_pdf(temp_pdf_path)
        except Exception as e:
            logging.error(f"Failed to extract text: {str(e)}")
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)
            driver.back()
            continue

        # Sub-Step 5.5: Parsing Text with Ollama
        logging.info("Parsing text with Ollama")
        parsed_data = parse_text_with_ollama(text, OLLAMA_MODEL)

        # Sub-Step 5.6: Filling the Form with Missing Data Logic
        logging.info("Filling the form")
        try:
            for field_name, field_id in FORM_FIELDS.items():
                try:
                    value = parsed_data[field_name]
                    if value is None:
                        value = "NA"
                    logging.info(f"Setting {field_name} to {value}")

                    if field_name in ["Gender", "Maritial Status", "Highest Level of Education"]:
                        select_element = wait.until(EC.presence_of_element_located((By.ID, field_id)))
                        select = Select(select_element)
                        if value == "NA":
                            select.select_by_index(0)
                        else:
                            select.select_by_visible_text(value)
                    else:
                        input_field = wait.until(EC.presence_of_element_located((By.ID, field_id)))
                        input_field.clear()
                        input_field.send_keys(value)
                except Exception as e:
                    logging.warning(f"Failed to fill {field_name}: {str(e)}")
                    continue

        except Exception as e:
            logging.error(f"Failed to fill form: {str(e)}")
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)
            driver.back()
            continue

        # Sub-Step 5.7: Submitting the Form
        logging.info("Submitting the form")
        try:
            submit_button = wait.until(EC.element_to_be_clickable((By.ID, "submit_form_button")))
            submit_button.click()
            wait.until(EC.presence_of_element_located((By.XPATH, "//table")))
            logging.info("Form submitted successfully")
        except Exception as e:
            logging.error(f"Failed to submit form: {str(e)}")
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)
            driver.back()
            continue

        # Sub-Step 5.8: Returning to the File List
        logging.info("Returning to file list")
        try:
            pass  # Already navigated back after submission
        except Exception as e:
            logging.error(f"Failed to return to file list: {str(e)}")
            driver.back()

        # Clean up
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)
        time.sleep(2)

    except Exception as e:
        logging.error(f"Error processing file: {str(e)}")
        driver.back()
        continue

# Finalize
logging.info("Automation completed")
driver.quit()
