from app.database import SessionLocal
from app.security.password import hash_password

from app.models.user import User
from app.models.customer import Customer
from app.models.delivery_partner import DeliveryPartner
from app.models.order import Order
from app.models.payment import Payment
from app.models.tracking import Tracking
from app.models.complaint import Complaint
from app.models.restaurant import Restaurant, MenuItem
from app.models.order_item import OrderItem
from app.models.review import Review

# Use a mailbox you can read, so the order emails reach you
CUSTOMER_EMAIL = "hyd.customer@example.com"

PARTNER_PASSWORD = "Partner@123"
CUSTOMER_PASSWORD = "Customer@123"

# name, email, phone, vehicle type, vehicle number, city, pincode
PARTNERS = [
    ("Ravi Kumar", "ravi.partner@example.com", "9876501001", "Bike", "TS09AB1001", "Hyderabad", "500001"),
    ("Imran Khan", "imran.partner@example.com", "9876501002", "Bike", "TS09AB1002", "Hyderabad", "500500"),
    ("Rahul Patil", "rahul.partner@example.com", "9876501003", "Bike", "MH12AB1003", "Pune", "411040"),
]

# name, email, phone, address, city, pincode
CUSTOMERS = [
    ("Ananya Reddy", CUSTOMER_EMAIL, "9123401001",
     "Banjara Hills, Road 12, Hyderabad", "Hyderabad", "500034"),
    ("Priya Sharma", "priya.customer@example.com", "9123401002",
     "Baner Road, Pune", "Pune", "411040"),
]

db = SessionLocal()


def get_or_create_user(name, email, password, role):
    user = db.query(User).filter(User.email == email.lower()).first()
    if user:
        return user, False
    user = User(
        full_name=name, email=email.lower(),
        hashed_password=hash_password(password), role=role
    )
    db.add(user)
    db.flush()
    return user, True


for name, email, phone, vtype, vnum, city, pin in PARTNERS:
    user, new = get_or_create_user(name, email, PARTNER_PASSWORD, "delivery_partner")
    if new:
        db.add(DeliveryPartner(
            user_id=user.id, phone=phone, vehicle_type=vtype,
            vehicle_number=vnum, city=city, pincode=pin
        ))
        print(f"Partner  {email}  ({city} {pin})")

for name, email, phone, address, city, pin in CUSTOMERS:
    user, new = get_or_create_user(name, email, CUSTOMER_PASSWORD, "customer")
    if new:
        db.add(Customer(
            user_id=user.id, phone=phone, address=address, city=city, pincode=pin
        ))
        print(f"Customer {email}  ({city} {pin})")

db.commit()
db.close()

print("Demo accounts ready.")
print("Partners:  password", PARTNER_PASSWORD)
print("Customers: password", CUSTOMER_PASSWORD)