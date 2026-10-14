"""
Apple Self Service Repair Scraper
Automates the process of fetching logic board configuration from Apple's repair site
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import re
import time

class AppleScraper:
    def __init__(self, headless=True):
        """Initialize the scraper with Chrome options"""
        self.headless = headless
        self.driver = None
    
    def setup_driver(self):
        """Setup Chrome driver with options"""
        print(f"[Scraper] Setting up Chrome driver...")
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless=new')
        
        # Balanced performance optimizations
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Additional stability options for Windows
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-background-networking')
        chrome_options.add_argument('--disable-default-apps')
        chrome_options.add_argument('--disable-sync')
        chrome_options.add_argument('--metrics-recording-only')
        chrome_options.add_argument('--mute-audio')
        chrome_options.add_argument('--disable-web-security')  # May help with resource loading
        
        # Use eager page load strategy to continue without waiting for all resources
        chrome_options.page_load_strategy = 'eager'
        
        print(f"[Scraper] Installing Chrome driver (downloading ~10MB, please wait)...") 
        try:
            service = Service(ChromeDriverManager().install())
            print(f"[Scraper] Chrome driver installed successfully!")
        except Exception as e:
            print(f"[Scraper] Error installing Chrome driver: {e}")
            raise
        
        print(f"[Scraper] Launching Chrome browser...")
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.set_page_load_timeout(60)  # Increased timeout
        self.driver.implicitly_wait(10)  # Increased implicit wait
        print(f"[Scraper] Chrome ready!")
    
    def get_logic_board_config(self, serial_number):
        """
        Main method to get logic board configuration from Apple Self Service Repair
        
        Args:
            serial_number (str): Device serial number
            
        Returns:
            dict: Contains success status and config text or error message
        """
        try:
            if not self.driver:
                self.setup_driver()
            
            # Navigate to Apple Self Service Repair
            print(f"[Scraper] Navigating to Apple Self Service Repair...")
            max_retries = 2
            for retry in range(max_retries):
                try:
                    # Use JavaScript to stop page load if it takes too long
                    self.driver.execute_cdp_cmd('Page.enable', {})
                    self.driver.execute_cdp_cmd('Page.setLifecycleEventsEnabled', {'enabled': True})
                    
                    self.driver.get('https://selfservicerepair.com/fr-CA/order')
                    print(f"[Scraper] Page loaded successfully")
                    break
                except Exception as e:
                    if retry < max_retries - 1:
                        print(f"[Scraper] Page load attempt {retry + 1} failed, retrying...")
                        time.sleep(2)
                        continue
                    else:
                        print(f"[Scraper] Page load error after {max_retries} attempts: {e}")
                        # Try to stop the page load and continue anyway
                        try:
                            self.driver.execute_script("window.stop();")
                            print(f"[Scraper] Stopped page load, continuing with partial content...")
                        except:
                            pass
                        
                        # Check if we can still interact with the page
                        try:
                            self.driver.find_element(By.TAG_NAME, 'body')
                            print(f"[Scraper] Page is accessible despite timeout, continuing...")
                        except:
                            return {
                                'success': False,
                                'error': f'Failed to load Apple website after {max_retries} attempts: {str(e)}'
                            }
            
            # Wait for page to load and be interactive
            print(f"[Scraper] Waiting for page elements...")
            time.sleep(5)  # Give more time for JavaScript to initialize
            
            # Debug: Print page title and URL
            print(f"[Scraper] Current URL: {self.driver.current_url}")
            print(f"[Scraper] Page title: {self.driver.title}")
            
            # Find and enter serial number - try multiple selectors
            print(f"[Scraper] Looking for serial number input field...")
            serial_input = None
            
            # Try multiple possible selectors for the serial number input
            input_selectors = [
                (By.ID, 'serialNumberInput'),
                (By.NAME, 'serialNumber'),
                (By.CSS_SELECTOR, 'input[placeholder*="série"]'),
                (By.CSS_SELECTOR, 'input[placeholder*="serial"]'),
                (By.CSS_SELECTOR, 'input[type="text"]'),
                (By.XPATH, '//input[contains(@placeholder, "série")]'),
                (By.XPATH, '//input[contains(@placeholder, "numéro")]'),
                (By.XPATH, '//input[contains(@id, "serial")]'),
                (By.XPATH, '//input[contains(@name, "serial")]'),
            ]
            
            for by_method, selector in input_selectors:
                try:
                    print(f"[Scraper] Trying selector: {by_method} = {selector}")
                    serial_input = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((by_method, selector))
                    )
                    if serial_input and serial_input.is_displayed():
                        print(f"[Scraper] ✓ Found input field with: {by_method} = {selector}")
                        break
                    else:
                        serial_input = None
                except Exception as e:
                    print(f"[Scraper]   Not found with this selector")
                    continue
            
            # Fallback: Find all input elements and inspect them
            if not serial_input:
                print(f"[Scraper] Fallback: Inspecting all input elements...")
                try:
                    all_inputs = self.driver.find_elements(By.TAG_NAME, 'input')
                    print(f"[Scraper] Found {len(all_inputs)} input elements")
                    
                    for i, inp in enumerate(all_inputs):
                        try:
                            inp_type = inp.get_attribute('type') or ''
                            inp_id = inp.get_attribute('id') or ''
                            inp_name = inp.get_attribute('name') or ''
                            inp_placeholder = inp.get_attribute('placeholder') or ''
                            inp_class = inp.get_attribute('class') or ''
                            is_visible = inp.is_displayed()
                            
                            print(f"  Input[{i}]: type='{inp_type}', id='{inp_id}', name='{inp_name}', placeholder='{inp_placeholder}', visible={is_visible}")
                            
                            # Look for the first visible text input
                            if is_visible and inp_type in ['text', ''] and not serial_input:
                                serial_input = inp
                                print(f"[Scraper] ✓ Using input[{i}] as serial number field")
                        except Exception as e:
                            print(f"  Input[{i}]: Error inspecting - {e}")
                            continue
                except Exception as e:
                    print(f"[Scraper] Fallback error: {e}")
            
            if not serial_input:
                # Take a screenshot for debugging
                try:
                    screenshot_path = 'debug_screenshot.png'
                    self.driver.save_screenshot(screenshot_path)
                    print(f"[Scraper] Screenshot saved to: {screenshot_path}")
                except:
                    pass
                
                # Print page source snippet
                print(f"[Scraper] Page source snippet:")
                try:
                    page_source = self.driver.page_source[:2000]
                    print(page_source)
                except:
                    pass
                
                return {
                    'success': False,
                    'error': 'Serial number input field not found. Website may have changed or page not fully loaded.'
                }
            
            # Enter the serial number
            try:
                print(f"[Scraper] Entering serial number: {serial_number}")
                serial_input.clear()
                time.sleep(0.5)
                serial_input.send_keys(serial_number)
                time.sleep(0.5)
                print(f"[Scraper] Serial number entered successfully")
            except Exception as e:
                print(f"[Scraper] Error entering serial number: {e}")
                return {
                    'success': False,
                    'error': f'Could not enter serial number: {str(e)}'
                }
            
            # Click search button - try multiple selectors
            print(f"[Scraper] Clicking search button...")
            search_button = None
            
            # Try different button selectors
            button_selectors = [
                'button[type="submit"]',
                'button.search-button',
                'button.btn-primary',
                '//button[contains(text(), "Rechercher")]',
                '//button[contains(., "Rechercher")]'
            ]
            
            for selector in button_selectors:
                try:
                    if selector.startswith('//'):
                        search_button = self.driver.find_element(By.XPATH, selector)
                    else:
                        search_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if search_button and search_button.is_displayed():
                        search_button.click()
                        break
                except:
                    continue
            
            if not search_button:
                return {
                    'success': False,
                    'error': 'Could not find search button'
                }
            
            # Wait for results to load
            print(f"[Scraper] Waiting for page to load results...")
            time.sleep(3)  # Reduced from 5
            

            
            # Wait for repair type dropdown to appear
            print(f"[Scraper] Looking for repair type dropdown...")
            
            # The repair type dropdown appears after search
            # Look for the dropdown with the placeholder text about repair type
            repair_dropdown = None
            
            # Try multiple selectors for the repair type dropdown specifically
            dropdown_selectors = [
                '//span[@role="combobox" and contains(@aria-label, "type de réparation")]',
                '//span[@role="combobox" and contains(., "Sélectionner le type de réparation")]',
                '//span[contains(@class, "p-select-label") and contains(., "type de réparation")]',
            ]
            
            for selector in dropdown_selectors:
                try:
                    repair_dropdown = WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    if repair_dropdown:
                        print(f"[Scraper] Found repair dropdown with: {selector}")
                        break
                except:
                    continue
            
            # Fallback: get all comboboxes and find the right one
            if not repair_dropdown:
                print(f"[Scraper] Fallback: searching all combobox elements...")
                try:
                    all_combos = self.driver.find_elements(By.CSS_SELECTOR, 'span[role="combobox"]')
                    print(f"[Scraper] Found {len(all_combos)} combobox elements")
                    
                    for i, combo in enumerate(all_combos):
                        combo_text = combo.text.strip()
                        aria_label = combo.get_attribute('aria-label') or ''
                        print(f"  Combobox[{i}]: text='{combo_text}', aria-label='{aria_label}'")
                        
                        # Look for repair type indicators
                        if 'type de réparation' in combo_text.lower() or 'type de réparation' in aria_label.lower() or 'Sélectionner' in combo_text:
                            repair_dropdown = combo
                            print(f"[Scraper] ✓ Found repair type dropdown at index {i}")
                            break
                except Exception as e:
                    print(f"[Scraper] Fallback error: {e}")
            
            if not repair_dropdown:
                return {
                    'success': False,
                    'error': 'Could not find repair type dropdown after search'
                }
            
            # Click dropdown to open it
            print(f"[Scraper] Clicking repair type dropdown...")
            try:
                repair_dropdown.click()
                time.sleep(2)
                print(f"[Scraper] Dropdown opened")
            except Exception as e:
                print(f"[Scraper] Click failed, trying JavaScript...")
                self.driver.execute_script("arguments[0].click();", repair_dropdown)
                time.sleep(2)
            
            # Find and select "Carte logique" option
            print(f"[Scraper] Looking for 'Carte logique' option...")
            
            # Wait a bit for the dropdown list to render
            time.sleep(1)
            
            # The options appear as list items or spans after dropdown opens
            carte_logique_option = None
            
            # Try to find the option using multiple approaches
            option_selectors = [
                "//li[@role='option' and contains(., 'Carte logique')]",
                "//li[contains(@class, 'p-select-option') and contains(., 'Carte logique')]",
                "//li[contains(., 'Carte logique')]",
                "//*[@role='option' and contains(., 'Carte logique')]",
                "//span[contains(@class, 'p-select-option-label') and text()='Carte logique']"
            ]
            
            for selector in option_selectors:
                try:
                    print(f"[Scraper] Trying selector: {selector}")
                    carte_logique_option = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    if carte_logique_option:
                        print(f"[Scraper] Found 'Carte logique' with selector!")
                        break
                except:
                    continue
            
            # Fallback: search all visible options manually
            if not carte_logique_option:
                print(f"[Scraper] Fallback: searching all visible options...")
                try:
                    # Get all list items that might be options
                    all_options = self.driver.find_elements(By.XPATH, "//li[@role='option'] | //li[contains(@class, 'option')]")
                    print(f"[Scraper] Found {len(all_options)} option elements")
                    
                    for i, option in enumerate(all_options):
                        try:
                            option_text = option.text.strip()
                            print(f"  Option [{i}]: '{option_text}'")
                            if option_text == 'Carte logique':
                                carte_logique_option = option
                                print(f"[Scraper] ✓ Found 'Carte logique' at index {i}!")
                                break
                        except:
                            continue
                except Exception as e:
                    print(f"[Scraper] Fallback error: {e}")
            
            if not carte_logique_option:
                # Last resort: get all li elements
                print(f"[Scraper] Last resort: checking all <li> elements...")
                try:
                    all_li = self.driver.find_elements(By.TAG_NAME, "li")
                    print(f"[Scraper] Found {len(all_li)} <li> elements total")
                    for i, li in enumerate(all_li[:20]):  # Check first 20
                        try:
                            li_text = li.text.strip()
                            if li_text:
                                print(f"  li[{i}]: '{li_text}'")
                            if li_text == 'Carte logique':
                                carte_logique_option = li
                                print(f"[Scraper] ✓ Found at li[{i}]!")
                                break
                        except:
                            continue
                except Exception as e:
                    print(f"[Scraper] Last resort error: {e}")
            
            if not carte_logique_option:
                return {
                    'success': False,
                    'error': 'Could not find clickable "Carte logique" option'
                }
            
            # Click the option
            print(f"[Scraper] Clicking 'Carte logique' option...")
            try:
                # Scroll into view first
                self.driver.execute_script("arguments[0].scrollIntoView(true);", carte_logique_option)
                time.sleep(0.5)
                carte_logique_option.click()
                print(f"[Scraper] ✓ Clicked successfully!")
            except Exception as e:
                print(f"[Scraper] Normal click failed: {e}, trying JavaScript...")
                try:
                    self.driver.execute_script("arguments[0].click();", carte_logique_option)
                    print(f"[Scraper] ✓ JavaScript click successful!")
                except Exception as e2:
                    return {
                        'success': False,
                        'error': f'Could not click Carte logique: {str(e2)}'
                    }
            
            time.sleep(3)
            print(f"[Scraper] Waiting for configuration to load...")
            
            # Extract the configuration text
            print(f"[Scraper] Extracting configuration...")
            
            # Wait for the full configuration to appear (with "processeur" text)
            # The full config takes a moment to load after selection
            config_loaded = False
            max_attempts = 10
            
            for attempt in range(max_attempts):
                time.sleep(1)  # Check every second
                page_text = self.driver.find_element(By.TAG_NAME, 'body').text
                
                # Check if full config is loaded (contains "processeur")
                if 'processeur' in page_text.lower():
                    print(f"[Scraper] Full configuration loaded after {attempt + 1} seconds")
                    config_loaded = True
                    break
            
            if not config_loaded:
                print(f"[Scraper] Warning: Full config may not have loaded yet")
            

            
            # Get the page source
            page_source = self.driver.page_source
            
            # Clean up HTML entities
            import html
            page_source = html.unescape(page_source)
            
            # Try multiple patterns to find the configuration
            # PRIORITY: Look for full config with "processeur" first
            patterns = [
                r'Carte logique\s*\(([^)]*processeur[^)]+)\)',  # Full config with processeur
                r'\(([^)]*processeur central[^)]+)\)',  # With "processeur central"
                r'\(([^)]*cœurs[^)]*Go[^)]+)\)',  # With cores and memory
                r'Carte logique\s*\(([^)]+Go[^)]+)\)',  # With Go (memory)
                r'Carte logique\s*\(([^)]+)\)',  # Any text in parentheses
                r'\(([^)]*M\d+[^)]+)\)',  # Look for M1, M2, M3, etc
            ]
            
            config_text = None
            for pattern in patterns:
                match = re.search(pattern, page_source, re.IGNORECASE)
                if match:
                    potential_config = match.group(1).strip()
                    
                    # Prefer longer configs (full config is longer)
                    if len(potential_config) > 30 or 'processeur' in potential_config.lower():
                        config_text = potential_config
                        print(f"[Scraper] Success with pattern: {pattern}")
                        print(f"[Scraper] Config: {config_text}")
                        break
            
            # Fallback: look for elements that might contain the config
            if not config_text or len(config_text) < 30:
                print(f"[Scraper] Short config found, trying element search for full version...")
                
                # Look for headings or text that contains "Carte logique"
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
                        elements = self.driver.find_elements(By.XPATH, xpath)
                        
                        for element in elements:
                            text = element.text
                            text_clean = html.unescape(text)
                            
                            # Try to extract config from element text
                            match = re.search(r'\(([^)]+)\)', text_clean)
                            if match:
                                potential = match.group(1).strip()
                                # Only use if it's longer than current or has "processeur"
                                if len(potential) > 30 or 'processeur' in potential.lower():
                                    config_text = potential
                                    print(f"[Scraper] Found better config in element: {config_text}")
                                    break
                        
                        if config_text and len(config_text) > 30:
                            break
                    except Exception as e:
                        continue
            
            if config_text:
                # Clean up HTML entities
                config_text = html.unescape(config_text)
                print(f"[Scraper] Success! Config: {config_text}")
                
                return {
                    'success': True,
                    'config': config_text,
                    'serial': serial_number
                }
            else:
                # Print page text for debugging
                print(f"[Scraper] Could not find config. Page text sample:")
                body_text = self.driver.find_element(By.TAG_NAME, 'body').text
                print(body_text[:1000])
                
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
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.close()
