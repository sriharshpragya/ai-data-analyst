"""
Populate sample e-commerce data.
Runs after schema creation via database/init.sql.
"""
import os
import psycopg2
import random
from datetime import datetime, timedelta
from decimal import Decimal


def get_connection():
    """Get PostgreSQL connection."""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        user=os.getenv("POSTGRES_USER", "analyst"),
        password=os.getenv("POSTGRES_PASSWORD", "analyst_password"),
        database=os.getenv("POSTGRES_DB", "ecommerce"),
    )


def data_already_exists(conn):
    """Check if data is already populated."""
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM customers")
        count = cursor.fetchone()[0]
        return count > 0
    except:
        return False


def insert_sample_data(conn):
    """Insert realistic sample data."""
    cursor = conn.cursor()
    
    # Categories
    categories = [
        ("Electronics", "Phones, laptops, gadgets"),
        ("Clothing", "Apparel and accessories"),
        ("Books", "Physical and digital books"),
        ("Home & Kitchen", "Home goods and appliances"),
        ("Sports", "Sports equipment and gear"),
    ]
    cursor.executemany(
        "INSERT INTO categories (name, description) VALUES (%s, %s)",
        categories
    )
    print("✅ Categories inserted")
    
    # Customers
    initial_customers = [
        ("john@example.com", "John Smith", "Mumbai", "IN", "premium"),
        ("priya@example.com", "Priya Sharma", "Bangalore", "IN", "standard"),
        ("alex@example.com", "Alex Johnson", "New York", "US", "premium"),
        ("emma@example.com", "Emma Watson", "London", "UK", "premium"),
        ("raj@example.com", "Raj Kumar", "Delhi", "IN", "standard"),
        ("sara@example.com", "Sara Ali", "Dubai", "AE", "premium"),
        ("mike@example.com", "Mike Brown", "Toronto", "CA", "standard"),
        ("lisa@example.com", "Lisa Wong", "Singapore", "SG", "premium"),
        ("carlos@example.com", "Carlos Silva", "São Paulo", "BR", "standard"),
        ("yuki@example.com", "Yuki Tanaka", "Tokyo", "JP", "premium"),
    ]
    
    cities = [
        ("Mumbai", "IN"), ("Delhi", "IN"), ("Bangalore", "IN"),
        ("New York", "US"), ("San Francisco", "US"), ("London", "UK"),
        ("Tokyo", "JP"), ("Sydney", "AU"), ("Berlin", "DE"), ("Paris", "FR")
    ]
    
    additional_customers = []
    for i in range(20):
        city, country = random.choice(cities)
        tier = random.choices(
            ["standard", "premium", "enterprise"],
            weights=[70, 25, 5]
        )[0]
        additional_customers.append((
            f"user{i+11}@example.com",
            f"Customer {i+11}",
            city, country, tier,
        ))
    
    all_customers = initial_customers + additional_customers
    cursor.executemany(
        "INSERT INTO customers (email, name, city, country, tier) VALUES (%s, %s, %s, %s, %s)",
        all_customers
    )
    print("✅ Customers inserted")
    
    # Products
    products_data = [
        # Electronics (category_id = 1)
        ("iPhone 15", 1, 79999.00, 55000.00, 50),
        ("Samsung Galaxy S24", 1, 74999.00, 52000.00, 30),
        ("MacBook Air M2", 1, 114900.00, 85000.00, 20),
        ("Dell XPS 13", 1, 99999.00, 72000.00, 15),
        ("Sony WH-1000XM5", 1, 34990.00, 22000.00, 100),
        ("iPad Pro", 1, 89900.00, 62000.00, 25),
        # Clothing (category_id = 2)
        ("Nike Air Max", 2, 8999.00, 4500.00, 200),
        ("Levi's 501 Jeans", 2, 4499.00, 2000.00, 150),
        ("Adidas T-Shirt", 2, 1999.00, 800.00, 300),
        ("H&M Sweater", 2, 2999.00, 1200.00, 250),
        # Books (category_id = 3)
        ("Atomic Habits", 3, 599.00, 200.00, 500),
        ("Python Programming Guide", 3, 1299.00, 400.00, 100),
        ("The Lean Startup", 3, 799.00, 250.00, 200),
        ("Deep Learning", 3, 2499.00, 900.00, 50),
        # Home & Kitchen (category_id = 4)
        ("Instant Pot Duo", 4, 12999.00, 6500.00, 40),
        ("Dyson V15 Vacuum", 4, 65900.00, 42000.00, 15),
        ("Nespresso Machine", 4, 24999.00, 15000.00, 30),
        # Sports (category_id = 5)
        ("Yoga Mat", 5, 1499.00, 600.00, 200),
        ("Dumbbells 10kg Pair", 5, 2999.00, 1500.00, 100),
        ("Running Shoes", 5, 5999.00, 3000.00, 150),
    ]
    
    cursor.executemany(
        "INSERT INTO products (name, category_id, price, cost, stock_quantity) VALUES (%s, %s, %s, %s, %s)",
        products_data
    )
    print("✅ Products inserted")
    
    # Orders + Order Items
    now = datetime.now()
    order_count = 0
    
    for _ in range(100):
        customer_id = random.randint(1, 30)
        days_ago = random.randint(0, 180)
        order_date = now - timedelta(days=days_ago)
        
        status = random.choices(
            ["completed", "completed", "completed", "processing", "pending", "cancelled"],
            weights=[60, 15, 5, 10, 5, 5]
        )[0]
        
        num_items = random.randint(1, 4)
        selected_products = random.sample(range(1, len(products_data) + 1), num_items)
        
        order_total = 0
        order_items = []
        
        for product_id in selected_products:
            product_price = float(products_data[product_id - 1][2])
            quantity = random.randint(1, 3)
            item_total = product_price * quantity
            order_total += item_total
            order_items.append((product_id, quantity, product_price))
        
        cursor.execute(
            "INSERT INTO orders (customer_id, order_date, status, total_amount) VALUES (%s, %s, %s, %s) RETURNING id",
            (customer_id, order_date, status, order_total)
        )
        order_id = cursor.fetchone()[0]
        order_count += 1
        
        for product_id, quantity, unit_price in order_items:
            cursor.execute(
                "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (%s, %s, %s, %s)",
                (order_id, product_id, quantity, unit_price)
            )
    
    print(f"✅ {order_count} orders inserted with items")
    conn.commit()


def print_summary(conn):
    """Show what was created."""
    cursor = conn.cursor()
    print("\n" + "=" * 50)
    print("📊 Database Summary")
    print("=" * 50)
    
    for table in ["categories", "customers", "products", "orders", "order_items"]:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table}: {count} rows")
    
    cursor.execute("SELECT SUM(total_amount) FROM orders WHERE status = 'completed'")
    total_revenue = cursor.fetchone()[0] or 0
    print(f"\n  Total revenue: ₹{total_revenue:,.2f}")


def main():
    """Main entry point."""
    print("🚀 Populating sample data...")
    
    conn = get_connection()
    try:
        if data_already_exists(conn):
            print("ℹ️  Data already exists, skipping population")
            print_summary(conn)
            return
        
        insert_sample_data(conn)
        print_summary(conn)
        print("\n✅ Sample data ready!")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
