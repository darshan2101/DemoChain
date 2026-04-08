"""Generate synthetic NOVA database for all assessment tasks."""

import json
import random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)

# product categories and their attributes
CATEGORIES = {
    "skincare": {
        "types": ["Moisturizer", "Serum", "Cleanser", "Toner", "Sunscreen", "Eye Cream", "Face Mask"],
        "ingredients": ["Hyaluronic Acid", "Retinol", "Vitamin C", "Niacinamide", "Salicylic Acid",
                       "Glycolic Acid", "Peptides", "Ceramides", "Squalane", "Green Tea Extract"],
        "skin_types": ["oily", "dry", "combination", "sensitive", "normal"],
        "price_range": (18, 85)
    },
    "makeup": {
        "types": ["Foundation", "Concealer", "Lipstick", "Mascara", "Blush", "Eyeshadow Palette", "Setting Spray"],
        "shades": ["Fair", "Light", "Medium", "Tan", "Deep", "Rich"],
        "finishes": ["matte", "dewy", "satin", "natural"],
        "price_range": (12, 62)
    },
    "hair": {
        "types": ["Shampoo", "Conditioner", "Hair Oil", "Hair Mask", "Styling Cream", "Heat Protectant"],
        "hair_types": ["straight", "wavy", "curly", "coily"],
        "concerns": ["frizz", "damage", "dryness", "oiliness", "volume", "color-treated"],
        "price_range": (14, 48)
    },
    "apparel": {
        "types": ["T-Shirt", "Dress", "Jacket", "Hoodie", "Pants", "Skirt", "Blouse"],
        "sizes": ["XS", "S", "M", "L", "XL", "XXL"],
        "materials": ["cotton", "polyester", "linen", "silk blend", "organic cotton"],
        "price_range": (25, 120)
    },
    "footwear": {
        "types": ["Sneakers", "Sandals", "Boots", "Loafers", "Heels", "Flats"],
        "sizes": ["5", "6", "7", "8", "9", "10", "11", "12"],
        "price_range": (35, 150)
    },
    "accessories": {
        "types": ["Tote Bag", "Crossbody Bag", "Watch", "Sunglasses", "Scarf", "Belt", "Jewelry Set"],
        "materials": ["vegan leather", "canvas", "stainless steel", "recycled materials"],
        "price_range": (15, 95)
    }
}

ORDER_STATUSES = ["confirmed", "processing", "shipped", "out_for_delivery", "delivered", "returned"]
TICKET_INTENTS = ["order_status", "returns", "product_recommendation", "sizing", "ingredient_query"]


def generate_products(count=200):
    """Create a diverse product catalog across all NOVA categories."""
    products = []
    for i in range(count):
        cat_name = random.choice(list(CATEGORIES.keys()))
        cat = CATEGORIES[cat_name]
        product_type = random.choice(cat["types"])
        sku = f"NOVA-{cat_name[:3].upper()}-{i+1:04d}"

        product = {
            "sku": sku,
            "name": f"NOVA {product_type} — {fake.color_name()} Edition",
            "category": cat_name,
            "type": product_type,
            "price": round(random.uniform(*cat["price_range"]), 2),
            "rating": round(random.uniform(3.2, 5.0), 1),
            "review_count": random.randint(12, 2400),
            "in_stock": random.random() > 0.15,
            "description": fake.paragraph(nb_sentences=3)
        }

        # category-specific attributes
        if cat_name == "skincare":
            product["ingredients"] = random.sample(cat["ingredients"], k=random.randint(2, 5))
            product["skin_types"] = random.sample(cat["skin_types"], k=random.randint(1, 3))
        elif cat_name == "makeup":
            product["shades"] = random.sample(cat["shades"], k=random.randint(2, 5))
            product["finish"] = random.choice(cat["finishes"])
        elif cat_name == "hair":
            product["hair_types"] = random.sample(cat["hair_types"], k=random.randint(1, 3))
            product["concerns"] = random.sample(cat["concerns"], k=random.randint(1, 3))
        elif cat_name == "apparel":
            product["available_sizes"] = random.sample(cat["sizes"], k=random.randint(3, 6))
            product["material"] = random.choice(cat["materials"])
            product["size_guide"] = {
                "XS": "Chest: 30-32in", "S": "Chest: 34-36in", "M": "Chest: 38-40in",
                "L": "Chest: 42-44in", "XL": "Chest: 46-48in", "XXL": "Chest: 50-52in"
            }
        elif cat_name == "footwear":
            product["available_sizes"] = random.sample(cat["sizes"], k=random.randint(4, 7))
            product["fit_note"] = random.choice(["Runs true to size", "Runs slightly small — order half size up",
                                                  "Wide fit available", "Narrow fit — consider sizing up"])
        elif cat_name == "accessories":
            product["material"] = random.choice(cat["materials"])

        products.append(product)
    return products


def generate_customers(count=100):
    """Create customer profiles with purchase history context."""
    customers = []
    for i in range(count):
        skin_type = random.choice(["oily", "dry", "combination", "sensitive", "normal"])
        customers.append({
            "customer_id": f"CUST-{i+1:04d}",
            "name": fake.name(),
            "email": fake.email(),
            "country": fake.country_code(),
            "member_since": fake.date_between(start_date="-5y").isoformat(),
            "skin_type": skin_type,
            "preferences": random.sample(list(CATEGORIES.keys()), k=random.randint(1, 3)),
            "lifetime_value": round(random.uniform(45, 800), 2),
            "total_orders": random.randint(1, 25)
        })
    return customers


def generate_orders(customers, products, count=500):
    """Create purchase history linked to real customers and products."""
    orders = []
    for i in range(count):
        customer = random.choice(customers)
        num_items = random.randint(1, 4)
        items = random.sample(products, k=min(num_items, len(products)))
        status = random.choice(ORDER_STATUSES)
        order_date = fake.date_time_between(start_date="-6M")

        order = {
            "order_id": f"ORD-{i+1:06d}",
            "customer_id": customer["customer_id"],
            "items": [{"sku": item["sku"], "name": item["name"], "price": item["price"]} for item in items],
            "total": round(sum(item["price"] for item in items), 2),
            "status": status,
            "order_date": order_date.isoformat(),
            "estimated_delivery": (order_date + timedelta(days=random.randint(3, 14))).isoformat(),
        }

        if status == "shipped":
            order["tracking_number"] = f"NOVA{fake.bothify('??########').upper()}"
            order["carrier"] = random.choice(["FedEx", "UPS", "DHL", "USPS"])
        if status == "delivered":
            order["delivered_date"] = (order_date + timedelta(days=random.randint(3, 10))).isoformat()
        if status == "returned":
            order["return_reason"] = random.choice(["Wrong size", "Didn't match description",
                                                      "Changed mind", "Defective", "Allergic reaction"])

        orders.append(order)
    return orders


def generate_support_tickets(customers, orders, count=50):
    """Create sample support tickets across all intent types."""
    templates = {
        "order_status": [
            "Where is my order {order_id}? It's been a week!",
            "Can you check the status of order {order_id}?",
            "My order {order_id} still shows processing. When will it ship?",
        ],
        "returns": [
            "I need to return order {order_id}. The product didn't work for my skin.",
            "How do I start a return for {order_id}? The size is wrong.",
            "I want to return the {product_name} from order {order_id}.",
        ],
        "product_recommendation": [
            "What moisturizer do you recommend for {skin_type} skin?",
            "I'm looking for a new serum. I loved the {product_name} — anything similar?",
            "Can you suggest products for someone with {skin_type} skin who likes {category}?",
        ],
        "sizing": [
            "What size should I get in the {product_name}? I usually wear medium.",
            "Does the {product_name} run true to size?",
            "I'm between sizes for the {product_name}. Any advice?",
        ],
        "ingredient_query": [
            "Does the {product_name} contain parabens?",
            "What are the active ingredients in the {product_name}?",
            "Is the {product_name} safe for sensitive skin?",
        ]
    }

    tickets = []
    for i in range(count):
        intent = random.choice(TICKET_INTENTS)
        customer = random.choice(customers)
        order = random.choice(orders)
        product = random.choice(order["items"])
        template = random.choice(templates[intent])

        message = template.format(
            order_id=order["order_id"],
            product_name=product["name"],
            skin_type=customer.get("skin_type", "normal"),
            category=random.choice(list(CATEGORIES.keys()))
        )

        # some tickets express frustration
        frustration = random.random()
        if frustration > 0.8:
            message += " This is really frustrating. I've been waiting forever!"

        tickets.append({
            "ticket_id": f"TKT-{i+1:04d}",
            "customer_id": customer["customer_id"],
            "intent": intent,
            "message": message,
            "priority": "high" if frustration > 0.85 else "normal",
            "created_at": fake.date_time_between(start_date="-30d").isoformat(),
            "status": random.choice(["open", "in_progress", "resolved"])
        })
    return tickets


def main():
    print("Generating NOVA mock database...")
    products = generate_products(200)
    customers = generate_customers(100)
    orders = generate_orders(customers, products, 500)
    tickets = generate_support_tickets(customers, orders, 50)

    db = {
        "products": products,
        "customers": customers,
        "orders": orders,
        "support_tickets": tickets,
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "product_count": len(products),
            "customer_count": len(customers),
            "order_count": len(orders),
            "ticket_count": len(tickets),
            "categories": list(CATEGORIES.keys())
        }
    }

    with open("nova_mock_db.json", "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

    print(f"Done! {len(products)} products, {len(customers)} customers, "
          f"{len(orders)} orders, {len(tickets)} tickets -> nova_mock_db.json")


if __name__ == "__main__":
    main()
