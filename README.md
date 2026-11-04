# MarketHub – Multi-Vendor E-Commerce Marketplace

MarketHub is a Django-based multi-vendor e-commerce marketplace designed to connect customers with different vendors through one online shopping platform.

The platform allows customers to browse products, manage shopping carts and place orders, while vendors can manage their stores, products and customer orders. Marketplace administrators oversee users, vendors, products and platform activities.

## Features

### Customer Features
- User registration and authentication.
- Browse products and product categories.
- View individual product details.
- Add products to a shopping cart.
- Manage shopping cart items.
- Place and manage orders.

### Vendor Features
- Apply to become a marketplace vendor.
- Vendor approval workflow.
- Vendor dashboard.
- Create, edit and manage products.
- Upload multiple product images.
- Manage product stock and availability.
- View and manage vendor orders.
- Track order processing statuses.

### Administrator Features
- Administrative dashboard.
- Manage marketplace users.
- Review vendor applications.
- Approve, reject and suspend vendors.
- Manage products and categories.
- Monitor marketplace orders.

## Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend programming language |
| Django | Web framework |
| SQLite | Development database |
| HTML5 | Page structure |
| CSS3 | Styling and layout |
| JavaScript | Frontend interactions |
| Pillow | Image processing |
| Git and GitHub | Version control |

## Project Structure

```text
E-COMMERCE_DJANGO/
│
├── accounts/
├── vendors/
├── products/
├── carts/
├── orders/
├── ecommerce/
│
├── templates/
├── static/
│   └── css/
│
├── media/
├── manage.py
├── requirements.txt
└── README.md
```

## Getting Started

### 1. Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

### 2. Navigate into the Project

```bash
cd E-COMMERCE_DJANGO
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

### 4. Activate the Virtual Environment

Windows:

```bash
venv\Scripts\activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Apply Database Migrations

```bash
python manage.py migrate
```

### 7. Create an Administrator Account

```bash
python manage.py createsuperuser
```

### 8. Run the Development Server

```bash
python manage.py runserver
```

Open your browser and visit:

```text
http://127.0.0.1:8000/
```

## Development Status

MarketHub is under active development. Features and improvements are being added as the project progresses.

## Future Improvements

- Online payment integration.
- Enhanced order tracking.
- Customer reviews and ratings.
- Email notifications.
- Advanced product search and filtering.
- Production deployment.

## Author

**Masha B.**

GitHub: [@mashab246](https://github.com/mashab246)

---

*MarketHub – Bringing customers and vendors together.*
