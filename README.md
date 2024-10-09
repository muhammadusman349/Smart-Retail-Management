# Smart Retail Management System

Smart Retail Management System is a robust retail solution built with Django and Django REST Framework (DRF), providing efficient management of products, inventory, orders, and payments. It supports promotions, coupons, and third-party integrations, making it a versatile tool for modern retail businesses.

## Key Features

### 1. **Product Management**
   - Full CRUD functionality for products.
   - Categorization and tagging of products.
   - Advanced filtering and search capabilities by name, category, and stock levels.

### 2. **Inventory Management**
   - Real-time stock tracking.
   - Low-stock alerts and automated restock suggestions.
   - Integration with orders for seamless stock updates.

### 3. **Order & Payment Processing**
   - Manage orders with various payment methods (credit card, Stripe, cheque).
   - Payment status management (pending, completed, refunded).
   - Transaction tracking for all payment types.
   - Secure Stripe integration for payment processing.

### 4. **Promotions & Coupons**
   - Create promotional campaigns with customizable rules and expiration dates.
   - Generate and apply coupon codes at checkout.
   - Validate coupons based on order criteria.

### 5. **Webhooks & API Integrations**
   - Webhook support for payment gateways and notifications.
   - Flexible API integration for third-party services.

### 6. **Background Task Automation**
   - Celery-based task automation for periodic tasks (inventory checks, promotions, order processing).
   - Automated email notifications for stock alerts and promotions.

### 7. **Anomaly Detection**
   - Monitor stock and product movements using sensor data.
   - Automated anomaly alerts for unusual activities (e.g., theft, damage).


## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/muhammadusman349/Smart-Retail-Management.git

   cd Smart-Retail-Management
    ```
2. Set up a virtual environment:
    ```bash
    python3 -m venv env
    source env/bin/activate
    ```
3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4. Apply migrations:
    ```bash
    python manage.py migrate
    ```
5. Start the server:
    ```bash
    python manage.py runserver
    ```

## API Documentation

The API uses Django REST Framework and provides the following endpoints:

- /api/products/ – Manage product listings (CRUD).
- /api/orders/ – Handle orders, payments, and statuses.
- /api/coupons/ – Manage coupons and apply them to orders.
- /api/inventory/ – Track and update inventory levels.

For more detailed API usage, refer to the API documentation available through Swagger or Postman.

## Contribution
We welcome contributions! Feel free to fork the repository, make changes, and submit pull requests for any improvements or new features.

## License
This project is licensed under the MIT License. See the LICENSE file for details.