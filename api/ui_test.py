from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
import sys

# Path to your WebDriver executable (change the path as needed)
# If the WebDriver executable is in your PATH, you can omit this.

# Initialize the WebDriver (this example uses Chrome)
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(options=options)

homepage = "https://jumpstartevents.co.uk"

try:
    # Navigate to the web application
    driver.get(homepage)
    # Optionally, wait for the page to load or for specific elements to become available
    # This example waits up to 10 seconds for the page title to be available
    driver.implicitly_wait(10)

    # Check the title of the page
    assert "Home" in driver.title

    # Perform additional tests, such as finding elements or interacting with the page
    # For example, to find an element by its ID and enter text:
    # element = driver.find_element(By.ID, "yourElementId")
    # element.send_keys("some text")

    print("Test passed: Page title is as expected.")
except AssertionError:
    print("Test failed: Page title is not as expected.")
    sys.exit(1)
except WebDriverException:
    print("Test failed: WebDriver error occurred. Is Flask running?")
    sys.exit(1)

try:
    logo = driver.find_element(By.ID, "logo")
    logo.click()
    driver.implicitly_wait(10)  
    assert driver.current_url == homepage

    print("Successfully clicked on the logo and navigated to the homepage.")
finally:
    # Clean up: close the browser window
    driver.quit()
