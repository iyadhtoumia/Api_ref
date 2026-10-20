import re
import html
import time
import threading

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

from apple_api_client import AppleApiClient


DEFAULT_MAX_BROWSERS = 2
ORDER_URL = 'https://selfservicerepair.com/fr-CA/order'


class AppleScraper:
    def __init__(self, headless=True, max_browsers=DEFAULT_MAX_BROWSERS, use_api=True):
        self.headless = headless
        self._max_browsers = max_browsers
        self._semaphore = threading.Semaphore(max_browsers)
        self._setup_lock = threading.Lock()
        self._local = threading.local()
        self._use_api = use_api
        self._api_client = None
        self._api_lock = threading.Lock()

    def _get_api_client(self):
        """Lazily build the shared fast JSON-API client."""
        if self._api_client is None:
            with self._api_lock:
                if self._api_client is None:
                    self._api_client = AppleApiClient()
                    self._api_client.prewarm()
        return self._api_client

    # ------------------------------------------------------------------
    # Driver lifecycle (thread-local + semaphore capped)
    # ------------------------------------------------------------------
    def setup_driver(self):
        """Build and launch a new Chrome driver (caller must hold the setup lock)."""
        print(f"[Scraper] Launching Chrome browser...")
        chrome_options = webdriver.ChromeOptions()
        if self.headless:
            chrome_options.add_argument('--headless=new')

        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-background-networking')
        chrome_options.add_argument('--disable-default-apps')
        chrome_options.add_argument('--disable-sync')
        chrome_options.add_argument('--metrics-recording-only')
        chrome_options.add_argument('--mute-audio')
        chrome_options.add_argument('--disable-web-security')

        chrome_options.page_load_strategy = 'eager'
        chrome_options.add_argument('--blink-settings=imagesEnabled=false')
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_experimental_option('prefs', {
            'profile.managed_default_content_settings.images': 2,
            'profile.default_content_setting_values.notifications': 2,
        })
        try:
            service = Service(ChromeDriverManager().install())
        except Exception as e:
            print(f"[Scraper] Error installing Chrome driver: {e}")
            raise

        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(0)
        print(f"[Scraper] Chrome ready!")
        return driver

    def _get_driver(self):
        """Return this thread's driver, creating one (and reserving a slot) if needed."""
        driver = getattr(self._local, 'driver', None)
        if driver is not None:
            return driver

        self._semaphore.acquire()
        try:
            with self._setup_lock:
                driver = self.setup_driver()
            self._local.driver = driver
            self._local.acquired = True
        except Exception:
            self._semaphore.release()
            raise
        return driver

    def _driver_alive(self, driver):
        try:
            _ = driver.current_url
            return True
        except WebDriverException:
            return False

    def _get_live_driver(self):
        """Get this thread's driver, recreating it if it has died."""
        driver = getattr(self._local, 'driver', None)
        if driver is not None and not self._driver_alive(driver):
            print("[Scraper] Driver is dead, recreating...")
            self._close_thread_driver()
            driver = None
        if driver is None:
            driver = self._get_driver()
        return driver

    def _close_thread_driver(self):
        """Quit this thread's driver and release its semaphore slot."""
        driver = getattr(self._local, 'driver', None)
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass
            self._local.driver = None
        if getattr(self._local, 'acquired', False):
            self._local.acquired = False
            self._semaphore.release()

    def close(self):
        """Close the current thread's browser."""
        self._close_thread_driver()

    # ---- helpers ----
    @staticmethod
    def _first_displayed(driver, selectors):
        """Return the first displayed element matching any selector, else None."""
        for by, selector in selectors:
            try:
                for el in driver.find_elements(by, selector):
                    try:
                        if el.is_displayed():
                            return el
                    except Exception:
                        continue
            except Exception:
                continue
        return None

    def _wait_until(self, predicate, timeout, poll=0.25):
        """Poll predicate() until truthy or timeout. Returns the truthy value or None."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                result = predicate()
            except Exception:
                result = None
            if result:
                return result
            time.sleep(poll)
        return None

    def _find_serial_input(self, driver):
        """Locate the serial number input using efficient polling."""
        input_selectors = [
            (By.ID, 'serialNumberInput'),
            (By.CSS_SELECTOR, 'input[placeholder*="série"]'),
            (By.CSS_SELECTOR, 'input[placeholder*="serial"]'),
            (By.NAME, 'serialNumber'),
            (By.CSS_SELECTOR, 'input[type="text"]'),
            (By.XPATH, '//input[contains(@placeholder, "série")]'),
            (By.XPATH, '//input[contains(@placeholder, "numéro")]'),
            (By.XPATH, '//input[contains(@id, "serial")]'),
            (By.XPATH, '//input[contains(@name, "serial")]'),
        ]
        found = self._wait_until(
            lambda: self._first_displayed(driver, input_selectors),
            timeout=10,
        )
        if found:
            return found

        print("[Scraper] Fallback: inspecting all input elements...")
        for inp in driver.find_elements(By.TAG_NAME, 'input'):
            try:
                if inp.is_displayed() and (inp.get_attribute('type') or '') != 'hidden':
                    return inp
            except Exception:
                continue
        return None

    def get_logic_board_config(self, serial_number):
        if self._use_api:
            try:
                api_result = self._get_api_client().get_config(serial_number)
                if api_result.get('success'):
                    print(f"[Scraper] API success! Config: {api_result['config']}")
                    return api_result
                print(f"[Scraper] API path failed ({api_result.get('error')}), falling back to browser...")
            except Exception as e:
                print(f"[Scraper] API path error ({e}), falling back to browser...")

        try:
            driver = self._get_live_driver()

            print(f"[Scraper] Navigating to Apple Self Service Repair...")
            max_retries = 2
            for retry in range(max_retries):
                try:
                    driver.execute_cdp_cmd('Page.enable', {})
                    driver.execute_cdp_cmd('Page.setLifecycleEventsEnabled', {'enabled': True})
                    driver.get(ORDER_URL)
                    print(f"[Scraper] Page loaded successfully")
                    break
                except Exception as e:
                    if retry < max_retries - 1:
                        print(f"[Scraper] Page load attempt {retry + 1} failed, retrying...")
                        time.sleep(2)
                        continue
                    print(f"[Scraper] Page load error after {max_retries} attempts: {e}")
                    try:
                        driver.execute_script("window.stop();")
                        print(f"[Scraper] Stopped page load, continuing with partial content...")
                    except Exception:
                        pass
                    try:
                        driver.find_element(By.TAG_NAME, 'body')
                        print(f"[Scraper] Page is accessible despite timeout, continuing...")
                    except Exception:
                        return {
                            'success': False,
                            'error': f'Failed to load Apple website after {max_retries} attempts: {str(e)}'
                        }

            print(f"[Scraper] Current URL: {driver.current_url}")

            print(f"[Scraper] Looking for serial number input field...")
            serial_input = self._find_serial_input(driver)
            if not serial_input:
                print("[Scraper] Serial number input field not found.")
                return {
                    'success': False,
                    'error': 'Serial number input field not found. Website may have changed or page not fully loaded.'
                }

            try:
                print(f"[Scraper] Entering serial number: {serial_number}")
                serial_input.clear()
                serial_input.send_keys(serial_number)
                print(f"[Scraper] Serial number entered successfully")
            except Exception as e:
                print(f"[Scraper] Error entering serial number: {e}")
                return {
                    'success': False,
                    'error': f'Could not enter serial number: {str(e)}'
                }

            print(f"[Scraper] Clicking search button...")
            button_selectors = [
                (By.CSS_SELECTOR, 'button[type="submit"]'),
                (By.CSS_SELECTOR, 'button.search-button'),
                (By.CSS_SELECTOR, 'button.btn-primary'),
                (By.XPATH, '//button[contains(text(), "Rechercher")]'),
                (By.XPATH, '//button[contains(., "Rechercher")]'),
            ]
            search_button = self._wait_until(
                lambda: self._first_displayed(driver, button_selectors),
                timeout=5,
            )
            if not search_button:
                return {
                    'success': False,
                    'error': 'Could not find search button'
                }
            try:
                search_button.click()
            except Exception:
                driver.execute_script("arguments[0].click();", search_button)

            print(f"[Scraper] Looking for repair type dropdown...")
            dropdown_selectors = [
                (By.XPATH, '//span[@role="combobox" and contains(@aria-label, "type de réparation")]'),
                (By.XPATH, '//span[@role="combobox" and contains(., "Sélectionner le type de réparation")]'),
                (By.XPATH, '//span[contains(@class, "p-select-label") and contains(., "type de réparation")]'),
            ]
            repair_dropdown = self._wait_until(
                lambda: self._first_displayed(driver, dropdown_selectors),
                timeout=15,
            )

            if not repair_dropdown:
                print("[Scraper] Fallback: searching all combobox elements...")
                try:
                    for combo in driver.find_elements(By.CSS_SELECTOR, 'span[role="combobox"]'):
                        combo_text = (combo.text or '').strip().lower()
                        aria_label = (combo.get_attribute('aria-label') or '').lower()
                        if 'type de réparation' in combo_text or 'type de réparation' in aria_label or 'sélectionner' in combo_text:
                            repair_dropdown = combo
                            break
                except Exception as e:
                    print(f"[Scraper] Fallback error: {e}")

            if not repair_dropdown:
                return {
                    'success': False,
                    'error': 'Could not find repair type dropdown after search'
                }

            print(f"[Scraper] Clicking repair type dropdown...")
            try:
                repair_dropdown.click()
            except Exception:
                print("[Scraper] Click failed, trying JavaScript...")
                driver.execute_script("arguments[0].click();", repair_dropdown)

            print(f"[Scraper] Looking for 'Carte logique' option...")
            option_selectors = [
                (By.XPATH, "//li[@role='option' and contains(., 'Carte logique')]"),
                (By.XPATH, "//li[contains(@class, 'p-select-option') and contains(., 'Carte logique')]"),
                (By.XPATH, "//li[contains(., 'Carte logique')]"),
                (By.XPATH, "//*[@role='option' and contains(., 'Carte logique')]"),
                (By.XPATH, "//span[contains(@class, 'p-select-option-label') and text()='Carte logique']"),
            ]
            carte_logique_option = self._wait_until(
                lambda: self._first_displayed(driver, option_selectors),
                timeout=5,
            )

            if not carte_logique_option:
                print("[Scraper] Fallback: searching all visible options...")
                for option in driver.find_elements(By.XPATH, "//li[@role='option'] | //li[contains(@class, 'option')]"):
                    try:
                        if (option.text or '').strip() == 'Carte logique':
                            carte_logique_option = option
                            break
                    except Exception:
                        continue

            if not carte_logique_option:
                return {
                    'success': False,
                    'error': 'Could not find clickable "Carte logique" option'
                }

            print(f"[Scraper] Clicking 'Carte logique' option...")
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", carte_logique_option)
                carte_logique_option.click()
                print(f"[Scraper] Clicked successfully!")
            except Exception:
                try:
                    driver.execute_script("arguments[0].click();", carte_logique_option)
                    print(f"[Scraper] JavaScript click successful!")
                except Exception as e2:
                    return {
                        'success': False,
                        'error': f'Could not click Carte logique: {str(e2)}'
                    }

            print(f"[Scraper] Waiting for configuration to load...")

            def _config_ready():
                try:
                    return 'processeur' in driver.find_element(By.TAG_NAME, 'body').text.lower()
                except Exception:
                    return False

            config_loaded = bool(self._wait_until(_config_ready, timeout=10, poll=0.25))
            if not config_loaded:
                print("[Scraper] Warning: Full config may not have loaded yet")

            print(f"[Scraper] Extracting configuration...")
            page_source = html.unescape(driver.page_source)

            patterns = [
                r'Carte logique\s*\(([^)]*processeur[^)]+)\)',
                r'\(([^)]*processeur central[^)]+)\)',
                r'\(([^)]*cœurs[^)]*Go[^)]+)\)',
                r'Carte logique\s*\(([^)]+Go[^)]+)\)',
                r'Carte logique\s*\(([^)]+)\)',
                r'\(([^)]*M\d+[^)]+)\)',
            ]

            config_text = None
            for pattern in patterns:
                match = re.search(pattern, page_source, re.IGNORECASE)
                if match:
                    potential_config = match.group(1).strip()
                    if len(potential_config) > 30 or 'processeur' in potential_config.lower():
                        config_text = potential_config
                        print(f"[Scraper] Success with pattern: {pattern}")
                        break

            if not config_text or len(config_text) < 30:
                print(f"[Scraper] Short config found, trying element search for full version...")
                elements_to_check = [
                    "//h1[contains(., 'Carte logique')]",
                    "//h2[contains(., 'Carte logique')]",
                    "//h3[contains(., 'Carte logique')]",
                    "//div[contains(., 'Carte logique')]",
                    "//span[contains(., 'Carte logique')]",
                    "//*[contains(., 'processeur')]",
                ]
                for xpath in elements_to_check:
                    try:
                        for element in driver.find_elements(By.XPATH, xpath):
                            text_clean = html.unescape(element.text or '')
                            match = re.search(r'\(([^)]+)\)', text_clean)
                            if match:
                                potential = match.group(1).strip()
                                if len(potential) > 30 or 'processeur' in potential.lower():
                                    config_text = potential
                                    print(f"[Scraper] Found better config in element: {config_text}")
                                    break
                        if config_text and len(config_text) > 30:
                            break
                    except Exception:
                        continue

            if config_text:
                config_text = html.unescape(config_text)
                print(f"[Scraper] Success! Config: {config_text}")
                return {
                    'success': True,
                    'config': config_text,
                    'serial': serial_number
                }
            else:
                print(f"[Scraper] Could not find config. Page text sample:")
                try:
                    body_text = driver.find_element(By.TAG_NAME, 'body').text
                    print(body_text[:1000])
                except Exception:
                    pass
                return {
                    'success': False,
                    'error': 'Configuration text not found in page'
                }

        except Exception as e:
            print(f"[Scraper] Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f'Scraping error: {str(e)}'
            }
