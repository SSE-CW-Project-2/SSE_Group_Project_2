from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pytest

@pytest.fixture(scope="function")
def driver():
    options = Options()
    # Configure any desired options here, e.g., options.headless = True for headless mode
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    yield driver
    driver.quit()

def test_home_page_title(driver):
    # Navigate to the web application
    driver.get("https://jumpstartevents.co.uk")
    
    # Check the title of the page
    assert "Home" in driver.title, "Test failed: Page title is not as expected."