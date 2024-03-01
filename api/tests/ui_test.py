from selenium import webdriver
from selenium.common.exceptions import WebDriverException

options = webdriver.ChromeOptions()  # Can use other browsers/versions
options.add_argument("--headless")  # Ensures browser window will not be displayed
driver = webdriver.Chrome(options=options)


def test_home_page_exists():
    try:
        driver.get("http://localhost:5000")
        driver.implicitly_wait(10)

        # Check the title of the page
        assert "Home" in driver.title
    except WebDriverException:
        assert False, "Error: Could not load page. Is Flask running?"
