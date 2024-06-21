import time
import requests
import smtplib
from bs4 import BeautifulSoup
from requests.exceptions import RequestException, ConnectTimeout
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import socket

computer_name = socket.gethostname()
start = 0
error_state = 0
statupdate = False
check_url = "https://www.google.com"
url = ""
search_text = "In stock"
alt_search_text = "Low stock"
osc = 0
isc = 0
last_email_time = None
response = None


def is_website_available(url):
    global response
    try:
        response = requests.get(url, timeout=10)
        return response.status_code == 200
    except RequestException:
        return False


def send_email_notification(subject, body, sender_email, receiver_email, app_password):
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject
    msg["Importance"] = "High"  # Set the importance level to High
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, app_password)
        server.send_message(msg)


def get_main_header(url):
    try:
        response = requests.get(url, timeout=16000)  # Set a timeout for the request
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        main_header = soup.find("h1").text.strip()
        return main_header
    except (requests.exceptions.RequestException, ConnectTimeout) as e:
        print("Error Occurred: Line 57")
        raise RuntimeError(f"An error occurred while fetching the main header: {e}")


def check_midnight(sender_email, receiver_email, app_password, last_email_time):
    global osc
    global isc
    global statupdate
    current_time = time.strftime("%H:%M:%S", time.localtime())
    current_hour, current_minute, _ = current_time.split(":")

    if current_hour == "00" and current_minute == "00" and statupdate is False:
        if last_email_time is None or time.time() - last_email_time >= 60:
            print("Sending Review")
            statupdate = True
            send_email_notification(f"PRODUCT STATS: {main_header}",
                                    f"The {main_header} has been out of stock {osc} time(s) and in stock {isc} time(s) today!",
                                    sender_email, receiver_email, app_password)
            osc = 0
            isc = 0
            last_email_time = time.time()
    elif statupdate is True and current_hour == "00" and current_minute > "00":
        statupdate = False

    # else:
    # print("Not Time")
    return osc, isc, last_email_time


def purchase_product(url, main_header, sender_email, receiver_email, app_password):
    # Configure Selenium options
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Set path to the ChromeDriver executable
    chrome_driver_path = r"C:/" # ADD PATH HERE

    # Start the ChromeDriver service
    service = Service(chrome_driver_path)

    try:
        with webdriver.Chrome(service=service, options=chrome_options) as driver:
            while True:
                driver.get(url)
                # Find and click the "Add to cart" button
                add_to_cart_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "ProductSubmitButton-template--18053363401026__main"))
                )
                add_to_cart_button.click()
                # Find and click the "Check out" button
                try:
                    checkout_button = WebDriverWait(driver, 30).until(
                        EC.element_to_be_clickable((By.CLASS_NAME, "button--primary"))
                    )
                    checkout_button.click()

                    # Fill in the form fields
                    email_field = driver.find_element(By.ID, "email")
                    email_field.clear()
                    email_field.send_keys("example@example.com") #INSERT EMAIL HERE
                    first_name_field = driver.find_element(By.ID, "TextField0")
                    first_name_field.clear()
                    first_name_field.send_keys("First Name") #INSERT LAST NAME
                    last_name_field = driver.find_element(By.ID, "TextField1")
                    last_name_field.clear()
                    last_name_field.send_keys("Last Name") #INSERT LAST NAME
                    address_field = driver.find_element(By.ID, "address1")
                    address_field.clear()
                    address_field.send_keys("Shipping Address") #INSERT SHIPPING ADDRESS
                    city_field = driver.find_element(By.ID, "TextField4")
                    city_field.clear()
                    city_field.send_keys("Town") #INSERT SHIPPING TOWN
                    state_dropdown = WebDriverWait(driver, 30).until(
                        EC.element_to_be_clickable((By.ID, "Select1"))
                    )
                    select_state = Select(state_dropdown)
                    select_state.select_by_value("State") #INSERT SHIPPING STATE
                    zip_code_field = driver.find_element(By.ID, "TextField5")
                    zip_code_field.clear()
                    zip_code_field.send_keys("Zip Code") #INSERT SHIPPING ZIP CODE

                    # Submit the form
                    submit_button = driver.find_element(By.XPATH,
                                                        "//button[contains(@class, 'QT4by rqC98 hodFu VDIfJ j6D1f janiy')]")
                    submit_button.click()
                except:
                    print("Timeout while waiting for the Check out button.")

                # Execute JavaScript to trigger necessary events
                driver.execute_script("arguments[0].click();", submit_button)

                # Find and click the "Continue to payment" button
                try:
                    continue_to_payment_button = WebDriverWait(driver, 30).until(
                        EC.element_to_be_clickable((By.XPATH,
                                                    "//div[contains(@class, 'oQEAZ')]//button[contains(., 'Continue to payment')]"))
                    )
                    continue_to_payment_button.click()
                except:
                    print("Timeout while waiting for the Continue to payment button")
                # CC Number
                try:
                    iframe_locator = (By.XPATH, '//iframe[@title="Field container for: Card number"]')
                    iframe = WebDriverWait(driver, 10).until(EC.presence_of_element_located(iframe_locator))
                    driver.switch_to.frame(iframe)
                    print("Starting to input cc info")
                    ccNumberInput = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, 'number'))
                    )
                    print("Element located:", ccNumberInput)
                    if ccNumberInput.is_displayed():
                        ccNumberInput.clear()  # Clear the input field
                        print("Field cleared.")
                    else:
                        print("Element is not visible.")
                    print("Getting placeholder text")
                    placeholder_text = ccNumberInput.get_attribute("placeholder")
                    print("Placeholder text:", placeholder_text)
                    ccNumber = 'Raw Card Number' #INSERT CC NUMBER
                    action_chains = ActionChains(driver)
                    for digit in ccNumber:
                        action_chains.send_keys_to_element(ccNumberInput, digit).perform()
                        time.sleep(0.05)  # Adjust the sleep time if necessary
                    driver.switch_to.default_content()
                except Exception as e:
                    print("An exception occurred:", e)
                # CC Name
                try:
                    iframe_locator = (By.XPATH, '//iframe[@title="Field container for: Name on card"]')
                    iframe = WebDriverWait(driver, 10).until(EC.presence_of_element_located(iframe_locator))
                    driver.switch_to.frame(iframe)
                    print("Starting to input name")
                    ccNameInput = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, 'name'))
                    )
                    print("Element located:", ccNameInput)
                    if ccNameInput.is_displayed():
                        ccNameInput.clear()  # Clear the input field
                        print("Field cleared.")
                    else:
                        print("Element is not visible.")
                    print("Getting placeholder text")
                    placeholder_text = ccNameInput.get_attribute("placeholder")
                    print("Placeholder text:", placeholder_text)
                    ccNameInput.send_keys('Card Full Name') # CHANGE THIS TO THE NAME ON THE PAYMENT CARD
                    time.sleep(0.1)  # Adjust the sleep time if necessary
                    driver.switch_to.default_content()
                except Exception as e:
                    print("An exception occurred:", e)

                # CC Exp
                try:
                    iframe_locator = (By.XPATH, '//iframe[@title="Field container for: Expiration date (MM / YY)"]')
                    iframe = WebDriverWait(driver, 10).until(EC.presence_of_element_located(iframe_locator))
                    driver.switch_to.frame(iframe)
                    print("Starting to input exp")
                    ccExpInput = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, 'expiry'))
                    )
                    print("Element located:", ccExpInput)
                    if ccExpInput.is_displayed():
                        ccExpInput.clear()  # Clear the input field
                        print("Field cleared.")
                    else:
                        print("Element is not visible.")
                    print("Getting placeholder text")
                    placeholder_text = ccExpInput.get_attribute("placeholder")
                    print("Placeholder text:", placeholder_text)
                    ccExp = 'Exp Date' #INSERT CARD EXP DATE in Month Year Format (Ex: 1125 is November 2025)
                    action_chains = ActionChains(driver)
                    for digit in ccExp:
                        action_chains.send_keys_to_element(ccExpInput, digit).perform()
                        time.sleep(0.05)  # Adjust the sleep time if necessary
                    driver.switch_to.default_content()
                except Exception as e:
                    print("An exception occurred:", e)
                # CC CVC
                try:
                    iframe_locator = (
                        By.XPATH, '//iframe[@title="Field container for: Security code"]')
                    iframe = WebDriverWait(driver, 10).until(EC.presence_of_element_located(iframe_locator))
                    driver.switch_to.frame(iframe)
                    print("Starting to input CVC")
                    ccCVCInput = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, 'verification_value'))
                    )
                    print("Element located:", ccCVCInput)
                    if ccCVCInput.is_displayed():
                        ccCVCInput.clear()  # Clear the input field
                        print("Field cleared.")
                    else:
                        print("Element is not visible.")
                    print("Getting placeholder text")
                    placeholder_text = ccCVCInput.get_attribute("placeholder")
                    print("Placeholder text:", placeholder_text)
                    ccCVC = 'CVC Code' #INSERT CARD CVC CODE
                    action_chains = ActionChains(driver)
                    for digit in ccCVC:
                        action_chains.send_keys_to_element(ccCVCInput, digit).perform()
                        time.sleep(0.02)  # Adjust the sleep time if necessary
                    driver.switch_to.default_content()
                except Exception as e:
                    print("An exception occurred:", e)

                # PAY NOW BUTTON (PLACE ORDER!!!!!)
                try:
                    pay_now_button = WebDriverWait(driver, 30).until(
                        EC.element_to_be_clickable((By.XPATH,
                                                    "//button[contains(@class, 'QT4by rqC98 hodFu VDIfJ j6D1f janiy')]"))
                    )
                    pay_now_button.click()
                    send_email_notification(f"PRODUCT PURCHASED: {main_header}",
                                            f'The {main_header} has now been purchased on {url}. :)', sender_email,
                                            receiver_email, app_password)
                    # Wait to close the webpage to let the purchase go through
                    time.sleep(30)
                    break

                except:
                    print("Timeout while waiting for the Pay now button")

    except requests.exceptions.RequestException as e:
        print("An error occurred {Line 280}:", e)
        send_email_notification("Product Watching Program Error", "An error occurred. The program has stopped.",
                                sender_email, receiver_email, app_password)


def check_product_availability():
    global start, response, main_header, osc, isc, error_state
    search_text = "In stock"
    last_email_time = None

    sender_email = "example1@example.com" #INSERT SENDER EMAIL
    receiver_email = "example@example.com" #INSERT RECEIVER EMAIL
    app_password = "App Password" #INSERT APP PASSWORD FOR SENDER EMAIL

    if start == 0:
        start = 1
        main_header = get_main_header(url)
        subject = f"{main_header} Watching Started Successfully"
        body = f"The program has successfully started watching \"{main_header}\" at {url} using {computer_name}."
        send_email_notification(subject, body, sender_email, receiver_email, app_password)

    try:
        if is_website_available(url):
            # response = requests.get(url, timeout=10)  # Set a timeout for the request
            response.raise_for_status()
            # print("Website Available")
            if error_state == 1:
                send_email_notification(f"Product Watcher Issue Update", f"The tracker is back online on {computer_name}", sender_email,
                                        receiver_email, app_password)
                print(f"{url} is online.")
                error_state = 0
            if search_text in response.text or alt_search_text in response.text:
                send_email_notification(f"PRODUCT UPDATE: {main_header}",
                                        f'The {main_header} is now available on {url}.', sender_email,
                                        receiver_email, app_password)
                isc += 1
                purchase_product(url, main_header, sender_email, receiver_email, app_password)
                print("Email notification sent.")
                return True  # Product ordered, return True to exit the loop
            else:
                osc += 1
                # print("Product is still unavailable.")

                osc, isc, last_email_time = check_midnight(sender_email, receiver_email, app_password,
                                                           last_email_time)

                time.sleep(10)  # Wait for 10 seconds before checking again
        else:  # If the original URL is unavailable
            if is_website_available(check_url):
                print("Google is online.")
                # try:
                #     response = requests.get(url, timeout=10)
                #     response.raise_for_status()
                #     print("zbattery.solutions is online.")
                # except (RequestException, ConnectTimeout) as e:
                print(f"An error occurred while accessing {url} [338]")
                send_email_notification(f"Product Watcher Issue",
                                        f"The tracker has checked the site {osc + isc} times today and {computer_name} is currently connected to the internet, but is currently experiencing issues reaching {url} [Line 339].",
                                        sender_email, receiver_email, app_password)
                error_state = 1
                time.sleep(2 * 60)  # Wait 2 minutes before checking again
            else:
                print("Google is offline. Retrying in 1 minute.")
                time.sleep(1 * 60)  # Wait for 1 minute before checking again
    except (RequestException, ConnectTimeout) as e:
        print("An error occurred {Line 348}:", e)
        send_email_notification(f"Product Watcher Issue",
                                f"The tracker has checked the site {osc + isc} times today, but is currently experiencing issues reaching {url} on {computer_name} [Line 349].",
                                sender_email, receiver_email, app_password)
        error_state = 1
        return False  # Product not yet ordered, return False to continue the loop


try:
    while not check_product_availability():
        pass
except RuntimeError as e:
    print("An error occurred {351}:", e)
