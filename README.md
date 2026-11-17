# MarketHub – Multi-Vendor E-Commerce Marketplace

MarketHub is a Django-based multi-vendor e-commerce marketplace designed to connect customers with different vendors through one online shopping platform.

The platform enables customers to browse products, manage shopping carts and place orders. Vendors can manage their stores, products and customer orders, while marketplace administrators oversee users, vendors, products and platform activities.

## Group Members

| No. | Full Name | Registration Number |
|---|---|---|
| 1 | Galiwango Musa | 224-063011-29512 |
| 2 | Walusimbi Adnan | 224-063011-29698 |

## Project Background

The project began with the development of standalone frontend forms and pages using HTML5, CSS3 and JavaScript. These initial designs formed the frontend foundation for the development of the MarketHub Django-based e-commerce marketplace.

The original frontend coursework has been preserved separately within the project directory.

## Original HTML, CSS and JavaScript Coursework

The `html_css_javascript_forms_file/` directory contains the original frontend coursework developed by the group.

It includes:

- Home page.
- User registration and login pages.
- Customer and vendor pages.
- Product pages.
- Category page.
- Shopping cart page.
- Order and order item pages.
- Inventory manager page.
- CSS styling.
- JavaScript functionality.

These original files are preserved separately from the Django application.

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
| SQLite | Local development database |
| PostgreSQL | Production database |
| HTML5 | Page structure |
| CSS3 | Styling and layout |
| JavaScript | Frontend interactions |
| Pillow | Image processing |
| Cloudinary | Cloud media storage |
| WhiteNoise | Static file serving |
| Git and GitHub | Version control |
| Render | Application hosting and deployment |

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
│
├── html_css_javascript_forms_file/
│   ├── home.html
│   ├── register.html
│   ├── login.html
│   ├── customer.html
│   ├── vendor.html
│   ├── product.html
│   ├── product2.html
│   ├── category.html
│   ├── shopping_cart.html
│   ├── order.html
│   ├── order_item.html
│   ├── inventory_manager.html
│   ├── css/
│   └── js/
│
├── manage.py
├── requirements.txt
└── README.md
```

## Getting Started

Follow these instructions to run the Django application locally.

### 1. Clone the Repository

```bash
git clone https://github.com/mashab246/E-Commerce-Django.git
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

### 7. Create a Local Administrator Account

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

## Live Deployment

MarketHub is deployed using Render.

**Live Application:**

https://markethub-78ox.onrender.com/

## Testing

The project has been tested using Django's built-in testing framework.

The latest recorded test run completed successfully with 9 tests passing and no system check issues.

## Development Status

MarketHub has been developed with customer, vendor and administrator functionalities. The application has been deployed and is available online.

The original frontend coursework is also preserved in the project repository.

## Future Improvements

- Online payment integration.
- Enhanced order tracking.
- Customer reviews and ratings.
- Email notifications.
- Advanced product search and filtering.

## Authors

**Galiwango Musa**

GitHub: [@mashab246](https://github.com/mashab246)

**Walusimbi Adnan**

---

*MarketHub – Bringing customers and vendors together.*