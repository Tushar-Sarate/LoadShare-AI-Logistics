from app.database import SessionLocal
from app.models.user import User
from app.models.customer import Customer
from app.models.delivery_partner import DeliveryPartner
from app.models.order import Order
from app.models.payment import Payment
from app.models.tracking import Tracking
from app.models.complaint import Complaint
from app.models.restaurant import Restaurant, MenuItem
from app.models.order_item import OrderItem

# name, cuisine, emoji, address, city, pincode, [(item, description, price, veg)]
DATA = [
    # ---------------- Pune ----------------
    ("Spice Garden", "North Indian", "🍛", "Baner Road", "Pune", "411040", [
        ("Paneer Butter Masala", "Creamy tomato gravy", 220, True),
        ("Butter Naan", "Soft tandoor bread", 40, True),
        ("Chicken Biryani", "Hyderabadi style", 260, False),
        ("Dal Tadka", "Yellow lentils", 150, True),
        ("Gulab Jamun", "2 pieces", 60, True),
    ]),
    ("Pizza Point", "Pizza, Italian", "🍕", "Aundh Road", "Pune", "411040", [
        ("Margherita Pizza", "Cheese and tomato", 199, True),
        ("Farmhouse Pizza", "Loaded with veggies", 299, True),
        ("Chicken Tikka Pizza", "Spicy chicken", 329, False),
        ("Garlic Bread", "With cheese dip", 119, True),
        ("Cold Coffee", "Thick and chilled", 99, True),
    ]),
    ("Burger Hub", "Burgers, Fast Food", "🍔", "Wakad Chowk", "Pune", "411040", [
        ("Aloo Tikki Burger", "Classic veg burger", 89, True),
        ("Chicken Zinger Burger", "Crispy fried chicken", 179, False),
        ("French Fries", "Salted and crispy", 99, True),
        ("Veg Wrap", "Fresh veggies and sauce", 129, True),
        ("Chocolate Shake", "Rich and creamy", 119, True),
    ]),
    ("Dosa Corner", "South Indian", "🥞", "Shivaji Nagar", "Pune", "411001", [
        ("Masala Dosa", "With chutney and sambar", 90, True),
        ("Idli Sambar", "3 pieces", 70, True),
        ("Medu Vada", "2 pieces", 60, True),
        ("Filter Coffee", "Hot and strong", 40, True),
    ]),
    ("Misal and More", "Maharashtrian, Street Food", "🌶️", "FC Road", "Pune", "411040", [
        ("Kolhapuri Misal", "Spicy sprouts curry with pav", 110, True),
        ("Sabudana Vada", "2 pieces", 60, True),
        ("Chicken Kolhapuri", "Fiery red gravy", 280, False),
        ("Puran Poli", "Sweet stuffed flatbread", 70, True),
        ("Solkadhi", "Kokum coconut drink", 40, True),
    ]),
    ("Pune Biryani House", "Biryani, Mughlai", "🍗", "Camp", "Pune", "411001", [
        ("Chicken Dum Biryani", "Slow cooked", 250, False),
        ("Mutton Biryani", "Tender mutton", 350, False),
        ("Veg Biryani", "Vegetables and saffron", 190, True),
        ("Chicken 65", "Crispy starter", 210, False),
        ("Raita", "Cool curd", 40, True),
    ]),

    # ---------------- Mumbai ----------------
    ("Vada Pav Junction", "Street Food, Maharashtrian", "🥪", "Fort", "Mumbai", "400001", [
        ("Vada Pav", "Mumbai classic", 25, True),
        ("Misal Pav", "Spicy and tangy", 90, True),
        ("Pav Bhaji", "Buttery mashed veggies", 140, True),
        ("Bombay Sandwich", "Grilled with chutney", 80, True),
        ("Cutting Chai", "Half glass tea", 20, True),
    ]),
    ("Coastal Catch", "Seafood, Malvani", "🦐", "Bandra West", "Mumbai", "400050", [
        ("Bombil Fry", "Crispy Bombay duck", 220, False),
        ("Prawns Curry", "Coconut based", 350, False),
        ("Surmai Thali", "Fish with rice and bhakri", 420, False),
        ("Veg Thali", "Seasonal vegetables", 200, True),
        ("Solkadhi", "Kokum coconut drink", 60, True),
    ]),
    ("Dragon Wok", "Chinese, Indo-Chinese", "🥡", "Bandra West", "Mumbai", "400050", [
        ("Veg Manchurian", "Gravy", 160, True),
        ("Chicken Hakka Noodles", "Wok tossed", 180, False),
        ("Schezwan Fried Rice", "Spicy", 170, True),
        ("Chilli Chicken", "Dry", 230, False),
        ("Spring Rolls", "4 pieces", 120, True),
    ]),

    # ---------------- Delhi ----------------
    ("Punjabi Dhaba", "Punjabi, North Indian", "🍲", "Connaught Place", "Delhi", "110001", [
        ("Butter Chicken", "Rich and creamy", 320, False),
        ("Dal Makhani", "Slow cooked black lentils", 210, True),
        ("Amritsari Kulcha", "Stuffed and crisp", 120, True),
        ("Tandoori Roti", "Whole wheat", 20, True),
        ("Sweet Lassi", "Thick and chilled", 80, True),
    ]),
    ("Mughlai Darbar", "Mughlai, Kebabs", "🍢", "Hauz Khas", "Delhi", "110016", [
        ("Seekh Kebab", "Minced mutton", 260, False),
        ("Mutton Korma", "Royal gravy", 380, False),
        ("Paneer Tikka", "Smoky tandoor", 240, True),
        ("Rumali Roti", "Thin and soft", 30, True),
        ("Shahi Tukda", "Rich bread dessert", 110, True),
    ]),
    ("Chaat Corner", "Street Food, Chaat", "🥗", "Chandni Chowk", "Delhi", "110006", [
        ("Aloo Tikki Chaat", "With chutneys", 80, True),
        ("Golgappa", "6 pieces", 50, True),
        ("Dahi Bhalla", "Soft and creamy", 90, True),
        ("Chole Bhature", "Fluffy bhature", 130, True),
        ("Jalebi", "Hot and crisp", 60, True),
    ]),
    ("Mithai Mahal", "Dessert, Sweets", "🍰", "Chandni Chowk", "Delhi", "110006", [
        ("Gulab Jamun", "4 pieces", 80, True),
        ("Rasmalai", "2 pieces", 120, True),
        ("Kaju Katli", "250 g", 200, True),
        ("Soan Papdi", "250 g", 100, True),
        ("Jalebi", "250 g", 70, True),
    ]),
    ("Cheesy Slice Pizzeria", "Pizza, Italian", "🍕", "Hauz Khas", "Delhi", "110016", [
        ("Margherita Pizza", "Classic", 199, True),
        ("Paneer Tikka Pizza", "Indian toppings", 299, True),
        ("Chicken Sausage Pizza", "Loaded", 329, False),
        ("Garlic Bread", "With cheese", 119, True),
        ("Brownie", "Warm chocolate", 99, True),
    ]),

    # ---------------- Bengaluru ----------------
    ("Meghana Biryani House", "Biryani, Andhra", "🍗", "MG Road", "Bangalore", "560001", [
        ("Chicken Dum Biryani", "Spicy Andhra style", 280, False),
        ("Mutton Biryani", "Tender mutton", 380, False),
        ("Paneer Biryani", "Veg favourite", 240, True),
        ("Chicken 65", "Crispy starter", 220, False),
        ("Raita", "Cool curd", 40, True),
    ]),
    ("Udupi Tiffins", "South Indian, Udupi", "🥞", "Indiranagar", "Bangalore", "560034", [
        ("Benne Dosa", "Butter dosa", 90, True),
        ("Idli Vada", "Classic combo", 80, True),
        ("Bisi Bele Bath", "Spicy rice and lentils", 110, True),
        ("Kesari Bath", "Sweet semolina", 50, True),
        ("Filter Coffee", "Strong and hot", 35, True),
    ]),
    ("Wok Express", "Chinese, Indo-Chinese", "🥡", "MG Road", "Bangalore", "560001", [
        ("Veg Hakka Noodles", "Wok tossed", 150, True),
        ("Chicken Manchurian", "Gravy", 220, False),
        ("Chilli Paneer", "Dry", 200, True),
        ("Chicken Lollipop", "6 pieces", 230, False),
        ("Schezwan Fried Rice", "Spicy", 170, True),
    ]),
    ("Burger Barn", "Burgers, Fast Food", "🍔", "Indiranagar", "Bangalore", "560034", [
        ("Veg Burger", "Crispy patty", 99, True),
        ("Chicken Burger", "Juicy and crispy", 169, False),
        ("French Fries", "Salted", 89, True),
        ("Peri Peri Wrap", "Chicken wrap", 149, False),
        ("Oreo Shake", "Thick shake", 119, True),
    ]),

    # ---------------- Hyderabad ----------------
    ("Hyderabadi Dum Biryani", "Biryani, Hyderabadi", "🍛", "Abids", "Hyderabad", "500001", [
        ("Chicken Dum Biryani", "Authentic dum", 300, False),
        ("Mutton Biryani", "Slow cooked", 400, False),
        ("Veg Biryani", "Fragrant rice", 220, True),
        ("Mirchi Ka Salan", "Peanut chilli curry", 90, True),
        ("Double Ka Meetha", "Bread pudding", 80, True),
    ]),
    ("Irani Cafe", "Mughlai, Cafe", "☕", "Banjara Hills", "Hyderabad", "500034", [
        ("Irani Chai", "Rich and creamy", 30, True),
        ("Osmania Biscuits", "6 pieces", 40, True),
        ("Chicken Haleem", "Slow cooked", 250, False),
        ("Keema Samosa", "2 pieces", 60, False),
        ("Bun Maska", "Buttered bun", 50, True),
    ]),

    # ---------------- Chennai ----------------
    ("Chettinad Kitchen", "South Indian, Chettinad", "🌶️", "T Nagar", "Chennai", "600001", [
        ("Chettinad Chicken", "Spicy and aromatic", 290, False),
        ("Mutton Chukka", "Dry roast", 360, False),
        ("Kuzhi Paniyaram", "Veg dumplings", 90, True),
        ("Kerala Parotta", "Layered bread", 30, True),
        ("Curd Rice", "Cooling", 80, True),
    ]),
    ("Marina Seafood", "Seafood, South Indian", "🐟", "Besant Nagar", "Chennai", "600020", [
        ("Fish Fry", "Crispy", 260, False),
        ("Prawn Masala", "Spicy", 340, False),
        ("Crab Roast", "Pepper style", 420, False),
        ("Lemon Rice", "Tangy", 100, True),
        ("Rasam", "Peppery soup", 60, True),
    ]),

    # ---------------- Kolkata ----------------
    ("Bengali Bhoj", "Bengali, Seafood", "🐟", "Park Street", "Kolkata", "700001", [
        ("Kosha Mangsho", "Slow cooked mutton", 340, False),
        ("Ilish Bhapa", "Steamed hilsa", 450, False),
        ("Shukto", "Mixed vegetables", 150, True),
        ("Luchi Alur Dum", "Puffed bread and potato", 140, True),
        ("Rasgulla", "4 pieces", 60, True),
    ]),
    ("Kathi Roll Hub", "Street Food, Rolls", "🌯", "Ballygunge", "Kolkata", "700019", [
        ("Egg Roll", "Classic", 70, False),
        ("Chicken Kathi Roll", "Juicy", 130, False),
        ("Paneer Roll", "Veg favourite", 120, True),
        ("Mutton Roll", "Rich", 170, False),
        ("Phuchka", "6 pieces", 50, True),
    ]),

    # ---------------- Ahmedabad ----------------
    ("Gujarati Thali House", "Gujarati, Thali", "🍽️", "CG Road", "Ahmedabad", "380001", [
        ("Full Gujarati Thali", "Unlimited", 280, True),
        ("Dhokla", "Soft and spongy", 90, True),
        ("Khandvi", "Gram flour rolls", 100, True),
        ("Thepla", "With pickle", 70, True),
        ("Chaas", "Spiced buttermilk", 30, True),
    ]),

    # ---------------- Jaipur ----------------
    ("Rajwada Rasoi", "Rajasthani, North Indian", "🍲", "MI Road", "Jaipur", "302001", [
        ("Dal Baati Churma", "Rajasthani classic", 240, True),
        ("Laal Maas", "Fiery mutton curry", 380, False),
        ("Gatte Ki Sabzi", "Gram flour dumplings", 180, True),
        ("Ker Sangri", "Desert beans", 200, True),
        ("Ghewar", "Sweet disc", 120, True),
    ]),

    # ---------------- Lucknow ----------------
    ("Awadhi Dastarkhwan", "Mughlai, Awadhi", "🍢", "Hazratganj", "Lucknow", "226001", [
        ("Galouti Kebab", "Melt in mouth", 260, False),
        ("Awadhi Biryani", "Fragrant", 300, False),
        ("Nihari", "Slow cooked", 320, False),
        ("Sheermal", "Saffron bread", 50, True),
        ("Kulfi Falooda", "Cold dessert", 110, True),
    ]),

    # ---------------- Chandigarh ----------------
    ("Amritsari Tadka", "Punjabi, North Indian", "🍛", "Sector 17", "Chandigarh", "160017", [
        ("Amritsari Fish", "Crispy fried", 280, False),
        ("Sarson Da Saag Makki Roti", "Winter special", 200, True),
        ("Chole Kulche", "Street style", 130, True),
        ("Chicken Tikka", "Tandoori", 270, False),
        ("Sweet Lassi", "Thick", 90, True),
    ]),

    # ---------------- Kochi ----------------
    ("Kerala Kitchen", "Kerala, South Indian, Seafood", "🥥", "Fort Kochi", "Kochi", "682001", [
        ("Karimeen Pollichathu", "Pearl spot fish", 380, False),
        ("Appam and Veg Stew", "Soft appams", 180, True),
        ("Kerala Chicken Roast", "Spicy", 280, False),
        ("Puttu Kadala", "Steamed rice and chickpea curry", 120, True),
        ("Payasam", "Sweet pudding", 80, True),
    ]),

    # ---------------- Goa ----------------
    ("Goan Shack", "Goan, Seafood", "🦀", "Panaji", "Goa", "403001", [
        ("Prawn Balchao", "Tangy and spicy", 380, False),
        ("Fish Curry Rice", "Coconut curry", 260, False),
        ("Chicken Xacuti", "Roasted spices", 300, False),
        ("Mushroom Xacuti", "Veg version", 220, True),
        ("Bebinca", "Layered dessert", 120, True),
    ]),

    # ---------------- Indore ----------------
    ("Sarafa Snacks", "Street Food, Chaat", "🥘", "Sarafa Bazaar", "Indore", "452001", [
        ("Poha Jalebi", "Breakfast classic", 70, True),
        ("Bhutte Ka Kees", "Grated corn snack", 80, True),
        ("Garadu", "Fried yam", 100, True),
        ("Sabudana Khichdi", "Fasting special", 90, True),
        ("Rabri", "Thick sweet milk", 100, True),
    ]),
]

db = SessionLocal()

existing = {name for (name,) in db.query(Restaurant.name).all()}
added = 0

for name, cuisine, emoji, address, city, pincode, items in DATA:

    if name in existing:
        continue

    restaurant = Restaurant(
        name=name, cuisine=cuisine, emoji=emoji,
        address=address, city=city, pincode=pincode
    )
    db.add(restaurant)
    db.flush()

    for item_name, description, price, veg in items:
        db.add(MenuItem(
            restaurant_id=restaurant.id,
            name=item_name,
            description=description,
            price=price,
            is_veg=veg
        ))

    added += 1

db.commit()
db.close()

print(f"Added {added} restaurants")