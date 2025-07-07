from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json

def initialize_driver():
    driver = webdriver.Chrome()
    driver.maximize_window()
    return driver, WebDriverWait(driver, 15)

def search_keyword(driver, wait, keyword):
    try:
        driver.get("https://www.myntra.com")
        search_input = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "desktop-searchBar")))
        search_input.clear()
        search_input.send_keys(keyword)
        search_input.send_keys(Keys.RETURN)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "results-base")))
        time.sleep(2)
        return True
    except Exception as e:
        print(f"Error searching for {keyword}: {e}")
        return False

def get_product_listings(wait, max_products=10):
    try:
        product_cards = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "product-base")))[:max_products]
        product_data = []
        
        for card in product_cards:
            try:
                link = card.find_element(By.TAG_NAME, "a").get_attribute("href")
                
                try:
                    image = card.find_element(By.CSS_SELECTOR, "img.img-responsive").get_attribute("src")
                except:
                    try:
                        image = card.find_element(By.CSS_SELECTOR, "img[src^='https://assets.myntassets.com']").get_attribute("src")
                    except:
                        image = None
                
                try:
                    brand = card.find_element(By.CLASS_NAME, "product-brand").text.strip()
                    name = card.find_element(By.CLASS_NAME, "product-product").text.strip()
                    title = f"{brand} - {name}"
                except:
                    title = None
                
                # Improved price extraction
                try:
                    price_div = card.find_element(By.CLASS_NAME, "product-price")
                    try:
                        discounted_price = price_div.find_element(By.CSS_SELECTOR, "span[data-testid='final-price']").text.replace("Rs.", "").replace("₹", "").strip()
                    except:
                        discounted_price = None
                    
                    try:
                        original_price = price_div.find_element(By.CSS_SELECTOR, "span[data-testid='strike-through-price']").text.replace("Rs.", "").replace("₹", "").strip()
                    except:
                        original_price = discounted_price
                    
                    try:
                        discount = price_div.find_element(By.CLASS_NAME, "product-discountPercentage").text.strip()
                    except:
                        discount = None
                except:
                    discounted_price = None
                    original_price = None
                    discount = None
                
                try:
                    search_rating = card.find_element(By.CLASS_NAME, "product-ratingsContainer").text.strip()
                except:
                    search_rating = None
                
                product_data.append({
                    "link": link,
                    "image_url": image,
                    "title": title,
                    "discounted_price": discounted_price,
                    "original_price": original_price,
                    "discount_percent": discount,
                    "search_rating": search_rating
                })
            except Exception as e:
                print(f"Error processing product card: {e}")
                continue
        
        return product_data
    except Exception as e:
        print(f"Error getting product listings: {e}")
        return []

def scrape_product_page(driver, wait, product):
    try:
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[1])
        driver.get(product["link"])
        time.sleep(3)
        
        # Price fallback from product page
        if product.get("discounted_price") is None:
            try:
                discounted_price = driver.find_element(By.CSS_SELECTOR, ".pdp-price").text.replace("Rs.", "").replace("₹", "").strip()
                product["discounted_price"] = discounted_price
            except:
                pass

        if product.get("original_price") is None:
            try:
                original_price = driver.find_element(By.CSS_SELECTOR, ".pdp-mrp").text.replace("MRP", "").replace("Rs.", "").replace("₹", "").strip()
                product["original_price"] = original_price
            except:
                pass
        
        # Get additional details not available on listing page
        try:
            rating_block = driver.find_element(By.CLASS_NAME, "index-overallRating").text.strip()
            rating = rating_block.split("\n")[0].split("|")[0].strip()
        except:
            rating = product.get("search_rating")
        
        try:
            review_block = driver.find_element(By.CSS_SELECTOR, ".index-totalRatings, .index-ratingsCount").text.strip()
            reviews = review_block.replace("Ratings", "").replace("&", "").strip()
        except:
            reviews = None
        
        try:
            size_buttons = driver.find_elements(By.CSS_SELECTOR, ".size-buttons-size-button:not(.size-buttons-size-button-unavailable)")
            sizes = [btn.text.strip() for btn in size_buttons]
            available_sizes = ", ".join(sizes) if sizes else None
        except:
            available_sizes = None
        
        product.update({
            "ratings": rating,
            "reviews": reviews,
            "available_sizes": available_sizes
        })
        
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        return product
    except Exception as e:
        print(f"Error scraping product page: {e}")
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        return None

def main():
    keywords = [
        "white shirt",
        "black dress",
        "denim jeans",
        "summer kurti",
        "co-ord set",
        "oversized t-shirt",
        "sneakers",
        "blue linen pants",
        "pink blazer for women",
        "yellow maxi dress"
    ]
    
    driver, wait = initialize_driver()
    all_results = {}
    
    try:
        for keyword in keywords:
            print(f"\nScraping for: {keyword}")
            if not search_keyword(driver, wait, keyword):
                continue
                
            products = get_product_listings(wait)
            keyword_results = []
            
            for product in products:
                detailed_product = scrape_product_page(driver, wait, product)
                if detailed_product:
                    final_product = {
                        "title": detailed_product["title"],
                        "image_url": detailed_product["image_url"],
                        "product_link": detailed_product["link"],
                        "discounted_price": detailed_product["discounted_price"],
                        "original_price": detailed_product["original_price"],
                        "discount_percent": detailed_product["discount_percent"],
                        "ratings": detailed_product["ratings"],
                        "reviews": detailed_product["reviews"],
                        "available_sizes": detailed_product["available_sizes"]
                    }
                    keyword_results.append(final_product)
            
            all_results[keyword] = keyword_results
            print(f"Scraped {len(keyword_results)} products for '{keyword}'")
        
        with open("myntra_products.json", "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        
        print("\n✅ Successfully scraped all keywords. Results saved to 'myntra_products.json'")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    main()