import os
import sqlite3
import random
from datetime import datetime, timedelta

def generate_ecommerce_dataset(output_dir="projects/e-commerce/data"):
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "raw"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "processed"), exist_ok=True)

    db_path = os.path.join(output_dir, "ecommerce.db")
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Read and execute schema
    schema_path = os.path.join("projects/e-commerce/sql/schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    cursor.executescript(schema_sql)

    print("⚡ Initializing Synthetic E-Commerce Dataset Generator...")
    random.seed(42)

    # 1. Customers
    cities_channels = [
        ("Istanbul", "Organic Search"), ("Ankara", "Paid Ad"), ("Izmir", "Social Media"),
        ("Bursa", "Direct"), ("Antalya", "Referral"), ("Adana", "Paid Ad"),
        ("Gaziantep", "Social Media"), ("Konya", "Organic Search"), ("Kocaeli", "Direct")
    ]
    first_names = ["Ahmet", "Mehmet", "Ayse", "Fatma", "Can", "Zeynep", "Emre", "Elif", "Burak", "Selin", 
                   "Kerem", "Deniz", "Murat", "Gamze", "Omer", "Ece", "Hakan", "Merve", "Ali", "Buse"]
    last_names = ["Yilmaz", "Kaya", "Demir", "Celik", "Sahin", "Yildiz", "Ozturk", "Aydin", "Ozkan", "Arslan",
                  "Dogan", "Kilic", "Aslan", "Cetin", "Kara", "Koc", "Kurt", "Ozdemir", "Simsek", "Polat"]

    start_date = datetime(2024, 1, 1)
    end_date = datetime(2026, 3, 1)

    num_customers = 1200
    customers_data = []

    for i in range(1, num_customers + 1):
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        email = f"{fn.lower()}.{ln.lower()}{i}@example.com"
        city, channel = random.choice(cities_channels)
        state = city + " Region"
        signup_dt = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
        segment = random.choice(["Standard", "VIP", "Corporate"])
        customers_data.append((i, fn, ln, email, city, state, signup_dt.strftime("%Y-%m-%d"), segment, channel))

    cursor.executemany("""
        INSERT INTO customers (customer_id, first_name, last_name, email, city, state, signup_date, customer_segment, acquisition_channel)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, customers_data)
    print(f"  ✓ Created {len(customers_data)} customers.")

    # 2. Products
    product_catalog = [
        ("Electronics", "Smartphones", "Pro Phone 15", 450.00, 799.00),
        ("Electronics", "Laptops", "UltraBook 14", 600.00, 1099.00),
        ("Electronics", "Audio", "Noise-Cancelling Headphones", 70.00, 149.00),
        ("Electronics", "Accessories", "Fast Wireless Charger", 12.00, 29.99),
        ("Electronics", "Smart Home", "Smart Voice Assistant Speaker", 35.00, 79.99),
        ("Fashion", "Men's Clothing", "Slim Fit Cotton Shirt", 15.00, 39.99),
        ("Fashion", "Women's Clothing", "Floral Summer Dress", 18.00, 49.99),
        ("Fashion", "Footwear", "Leather Urban Sneakers", 35.00, 89.99),
        ("Fashion", "Accessories", "Classic Polarized Sunglasses", 10.00, 29.99),
        ("Home & Living", "Furniture", "Ergonomic Mesh Desk Chair", 85.00, 199.00),
        ("Home & Living", "Kitchen", "Stainless Steel Espresso Maker", 40.00, 99.00),
        ("Home & Living", "Decor", "Minimalist Table Lamp", 14.00, 34.99),
        ("Beauty & Personal Care", "Skincare", "Hydrating Face Serum", 8.00, 24.99),
        ("Beauty & Personal Care", "Haircare", "Professional Hair Dryer", 25.00, 69.99),
        ("Sports & Outdoors", "Fitness", "Non-Slip Yoga Mat", 9.00, 24.99),
        ("Sports & Outdoors", "Camping", "Lightweight 2-Person Tent", 50.00, 129.99),
    ]

    products_data = []
    for pid, (cat, subcat, pname, cost, price) in enumerate(product_catalog, 1):
        stock = random.randint(50, 500)
        products_data.append((pid, pname, cat, subcat, cost, price, stock))

    cursor.executemany("""
        INSERT INTO products (product_id, product_name, category, sub_category, cost_price, unit_price, stock_quantity)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, products_data)
    print(f"  ✓ Created {len(products_data)} products.")

    # 3. Marketing Campaigns
    campaigns = [
        ("New Year Blast 2024", "Paid Ad", 15000.00, "2024-01-01", "2024-01-15"),
        ("Spring Fashion Sale", "Social Media", 8000.00, "2024-03-15", "2024-03-31"),
        ("Summer Tech Expo", "Organic Search", 12000.00, "2024-06-01", "2024-06-30"),
        ("Back to School", "Social Media", 10000.00, "2024-08-20", "2024-09-10"),
        ("Black Friday Megadeals", "Paid Ad", 25000.00, "2024-11-20", "2024-11-30"),
        ("New Year Blast 2025", "Paid Ad", 18000.00, "2025-01-01", "2025-01-15"),
        ("Valentine Special", "Social Media", 7000.00, "2025-02-01", "2025-02-14"),
        ("Spring Fashion 2025", "Social Media", 9500.00, "2025-03-15", "2025-03-31"),
        ("Black Friday 2025", "Paid Ad", 30000.00, "2025-11-20", "2025-11-30"),
    ]
    cursor.executemany("""
        INSERT INTO marketing_campaigns (campaign_name, channel, budget, start_date, end_date)
        VALUES (?, ?, ?, ?, ?)
    """, campaigns)

    # 4. Orders and Order Items
    num_orders = 5500
    orders_data = []
    order_items_data = []
    reviews_data = []

    payment_methods = ["Credit Card", "Debit Card", "PayPal", "Bank Transfer", "BNPL"]
    order_statuses = ["Completed", "Completed", "Completed", "Completed", "Completed", 
                      "Completed", "Completed", "Pending", "Cancelled", "Returned"]

    order_item_id = 1
    review_id = 1

    # Map customer signup dates
    cust_signup_dict = {c[0]: datetime.strptime(c[6], "%Y-%m-%d") for c in customers_data}

    for oid in range(1, num_orders + 1):
        cid = random.randint(1, num_customers)
        signup_dt = cust_signup_dict[cid]
        
        # Order date must be after customer signup date
        max_days = max(1, (end_date - signup_dt).days)
        order_dt = signup_dt + timedelta(days=random.randint(0, max_days), hours=random.randint(0, 23))
        
        status = random.choice(order_statuses)
        pay_method = random.choice(payment_methods)
        shipping_cost = round(random.uniform(5.0, 15.0), 2) if random.random() > 0.3 else 0.00
        discount = round(random.choice([0, 0, 0, 5, 10, 15, 20]), 2)

        # Select 1 to 4 items for this order
        num_items = random.choices([1, 2, 3, 4], weights=[0.5, 0.3, 0.15, 0.05])[0]
        selected_prods = random.sample(products_data, num_items)

        order_total = 0.0
        for prod in selected_prods:
            pid = prod[0]
            unit_price = prod[4] # unit_price
            qty = random.randint(1, 3)
            item_total = round(unit_price * qty, 2)
            order_total += item_total
            
            order_items_data.append((order_item_id, oid, pid, qty, unit_price, item_total))
            order_item_id += 1

            # Generate product review for some completed orders
            if status == "Completed" and random.random() < 0.25:
                rating = random.choices([1, 2, 3, 4, 5], weights=[0.05, 0.05, 0.1, 0.3, 0.5])[0]
                review_txt = f"Review for product {prod[1]}: Rating {rating}/5"
                reviews_data.append((review_id, pid, cid, rating, review_txt, order_dt.strftime("%Y-%m-%d %H:%M:%S")))
                review_id += 1

        final_amount = max(0.0, round(order_total + shipping_cost - discount, 2))
        orders_data.append((oid, cid, order_dt.strftime("%Y-%m-%d %H:%M:%S"), status, pay_method, shipping_cost, discount, final_amount))

    cursor.executemany("""
        INSERT INTO orders (order_id, customer_id, order_date, order_status, payment_method, shipping_cost, discounts_applied, total_amount)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, orders_data)
    print(f"  ✓ Created {len(orders_data)} orders.")

    cursor.executemany("""
        INSERT INTO order_items (order_item_id, order_id, product_id, quantity, unit_price, total_price)
        VALUES (?, ?, ?, ?, ?, ?)
    """, order_items_data)
    print(f"  ✓ Created {len(order_items_data)} order items.")

    cursor.executemany("""
        INSERT INTO customer_reviews (review_id, product_id, customer_id, rating, review_text, review_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, reviews_data)
    print(f"  ✓ Created {len(reviews_data)} customer reviews.")

    conn.commit()
    conn.close()
    print(f"✅ Database successfully created and populated at `{db_path}`!")

if __name__ == "__main__":
    generate_ecommerce_dataset()
