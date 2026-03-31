from typing import Optional


TAX_RATE = 0.08
PREMIUM_DISCOUNT = 0.9
DOMESTIC_SHIPPING = 5.99
INTERNATIONAL_SHIPPING = 15.99
FREE_SHIPPING_THRESHOLD = 50


def validate_order(order, inventory, customer_data):
    """
    Validate that an order can be fulfilled.

    Checks inventory existence, stock availability, and customer record.

    Args:
        order (dict): Order with 'order_id', 'item_id', 'quantity', 'customer_id'.
        inventory (dict): Maps item_id to {'quantity': int, 'price': float}.
        customer_data (dict): Maps customer_id to customer info.

    Returns:
        str | None: An error message string if validation fails, or None if valid.
    """
    if order['item_id'] not in inventory:
        return 'Item not in inventory'
    if inventory[order['item_id']]['quantity'] < order['quantity']:
        return 'Insufficient quantity'
    if order['customer_id'] not in customer_data:
        return 'Customer not found'
    return None


def calculate_price(item_id, quantity, customer, inventory):
    """
    Calculate the discounted item price before shipping and tax.

    Applies a 10% discount for premium customers.

    Args:
        item_id (str): The ID of the item being purchased.
        quantity (int): Number of units ordered.
        customer (dict): Customer record with a 'premium' boolean field.
        inventory (dict): Maps item_id to {'quantity': int, 'price': float}.

    Returns:
        float: The item price after any applicable discount.
    """
    price = inventory[item_id]['price'] * quantity
    if customer['premium']:
        price *= PREMIUM_DISCOUNT
    return price


def calculate_shipping(price, customer):
    """
    Determine the shipping cost based on customer location and order value.

    Domestic orders over the free shipping threshold ship for free.
    All international orders incur a flat shipping fee.

    Args:
        price (float): The discounted item price (used for threshold check).
        customer (dict): Customer record with a 'location' field ('domestic' or other).

    Returns:
        float: The shipping cost.
    """
    if customer['location'] == 'domestic':
        return 0 if price >= FREE_SHIPPING_THRESHOLD else DOMESTIC_SHIPPING
    return INTERNATIONAL_SHIPPING


def calculate_final_price(price, shipping):
    """
    Compute the final order total by adding tax and shipping.

    Args:
        price (float): The discounted item price.
        shipping (float): The shipping cost.

    Returns:
        tuple[float, float]: A (tax, final_price) tuple.
    """
    tax = price * TAX_RATE
    final_price = price + shipping + tax
    return tax, final_price


def update_inventory(inventory, item_id, quantity):
    """
    Deduct the purchased quantity from inventory in place.

    Args:
        inventory (dict): Maps item_id to {'quantity': int, 'price': float}.
        item_id (str): The item to update.
        quantity (int): The number of units to deduct.
    """
    inventory[item_id]['quantity'] -= quantity


def build_order_result(order, price, shipping, tax, final_price):
    """
    Construct the result dictionary for a successfully processed order.

    Args:
        order (dict): The original order dict.
        price (float): Discounted item price.
        shipping (float): Shipping cost.
        tax (float): Tax amount.
        final_price (float): Total amount charged.

    Returns:
        dict: A complete order result record.
    """
    return {
        'order_id': order['order_id'],
        'item_id': order['item_id'],
        'quantity': order['quantity'],
        'customer_id': order['customer_id'],
        'price': price,
        'shipping': shipping,
        'tax': tax,
        'final_price': final_price
    }


def process_single_order(order, inventory, customer_data):
    """
    Process one order end-to-end: validate, price, update inventory, build result.

    Args:
        order (dict): Order with 'order_id', 'item_id', 'quantity', 'customer_id'.
        inventory (dict): Mutable inventory dict, updated in place on success.
        customer_data (dict): Maps customer_id to customer info.

    Returns:
        tuple[dict | None, dict | None]: (result, error) — exactly one will be None.
    """
    error_message = validate_order(order, inventory, customer_data)
    if error_message:
        return None, {'order_id': order['order_id'], 'error': error_message}

    customer = customer_data[order['customer_id']]
    price = calculate_price(order['item_id'], order['quantity'], customer, inventory)
    shipping = calculate_shipping(price, customer)
    tax, final_price = calculate_final_price(price, shipping)

    update_inventory(inventory, order['item_id'], order['quantity'])
    result = build_order_result(order, price, shipping, tax, final_price)
    return result, None


def process_orders(orders, inventory, customer_data):
    """
    Process a batch of orders, updating inventory and tracking revenue.

    Each order is validated, priced, and recorded. Failed orders are collected
    separately with their error reasons. Inventory is mutated in place.

    Args:
        orders (list[dict]): List of orders, each with 'order_id', 'item_id',
            'quantity', and 'customer_id'.
        inventory (dict): Maps item_id to {'quantity': int, 'price': float}.
            Modified in place as orders are fulfilled.
        customer_data (dict): Maps customer_id to {'premium': bool, 'location': str}.

    Returns:
        dict: {
            'processed_orders': list of successful order result dicts,
            'error_orders': list of {'order_id', 'error'} dicts,
            'total_revenue': float sum of all final_prices for successful orders
        }
    """
    results = []
    error_orders = []
    total_revenue = 0

    for order in orders:
        result, error = process_single_order(order, inventory, customer_data)
        if error:
            error_orders.append(error)
        else:
            results.append(result)
            total_revenue += result['final_price']  # type: ignore

    return {
        'processed_orders': results,
        'error_orders': error_orders,
        'total_revenue': total_revenue
    }