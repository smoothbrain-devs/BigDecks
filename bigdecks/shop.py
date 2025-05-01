"""Shop endpoint management

This module handles the shop inventory and shopping cart functionality.
"""

from flask import (
    Blueprint,
    render_template,
    session,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    g
)
from .auth import login_required
from .database import get_db_connection
from .services.card_service import CardService

bp = Blueprint(name="shop", import_name=__name__)


@bp.route("/shop")
def inventory():
    """Display the shop inventory with actual card images."""
    # Check if we already have inventory items in the session
    if "inventory_items" not in session:
        # If not, fetch 20 random cards and store them in the session
        inventory_items = []
        for _ in range(20):
            card = CardService.get_random_card()
            # Use actual card data for the shop items
            price = 0.99  # Default price
            if card.prices.usd is not None:
                try:
                    price = float(card.prices.usd)
                except (ValueError, TypeError):
                    pass
                    
            inventory_items.append({
                "id": card.id,
                "name": card.name,
                "description": f"{card.set_name} - {card.rarity}",
                "price": price,
                "image_url": card.image_uris.normal or card.image_uris.small or card.image_uris.highest_resolution
            })
        
        # Store in session
        session["inventory_items"] = inventory_items
    
    # Use the stored inventory items
    return render_template("shop/inventory.html", inventory_items=session["inventory_items"])


@bp.route("/shop/packs")
def packs():
    """Display booster packs and boxes for sale."""
    # Mock data for featured sets
    featured_sets = [
        {
            "name": "Lost Caverns of Ixalan",
            "description": "Delve into ancient Maya-inspired caverns filled with dinosaurs and pirates.",
            "release_date": "November 2023",
            "image_url": "https://via.placeholder.com/600x400?text=Lost+Caverns+of+Ixalan",
            "set_code": "lci"
        },
        {
            "name": "Murders at Karlov Manor",
            "description": "A murder mystery set in the city of Ravnica.",
            "release_date": "February 2024",
            "image_url": "https://via.placeholder.com/600x400?text=Murders+at+Karlov+Manor",
            "set_code": "mkm"
        },
        {
            "name": "Outlaws of Thunder Junction",
            "description": "Wild west-themed set featuring notorious outlaws.",
            "release_date": "April 2024",
            "image_url": "https://via.placeholder.com/600x400?text=Outlaws+of+Thunder+Junction",
            "set_code": "otj"
        }
    ]
    
    # Mock data for sets and products
    sets = [
        {
            "name": "Lost Caverns of Ixalan",
            "set_code": "lci",
            "products": [
                {
                    "id": "lci-booster",
                    "name": "Lost Caverns of Ixalan Draft Booster",
                    "description": "15 cards per pack",
                    "price": 4.99,
                    "image_url": "https://via.placeholder.com/300x400?text=Draft+Booster"
                },
                {
                    "id": "lci-collector",
                    "name": "Lost Caverns of Ixalan Collector Booster",
                    "description": "15 premium cards per pack",
                    "price": 24.99,
                    "image_url": "https://via.placeholder.com/300x400?text=Collector+Booster"
                },
                {
                    "id": "lci-bundle",
                    "name": "Lost Caverns of Ixalan Bundle",
                    "description": "8 Draft Boosters + accessories",
                    "price": 44.99,
                    "image_url": "https://via.placeholder.com/300x400?text=Bundle"
                },
                {
                    "id": "lci-box",
                    "name": "Lost Caverns of Ixalan Draft Booster Box",
                    "description": "36 Draft Boosters",
                    "price": 139.99,
                    "image_url": "https://via.placeholder.com/300x400?text=Booster+Box"
                }
            ]
        },
        {
            "name": "Murders at Karlov Manor",
            "set_code": "mkm",
            "products": [
                {
                    "id": "mkm-booster",
                    "name": "Murders at Karlov Manor Draft Booster",
                    "description": "15 cards per pack",
                    "price": 4.99,
                    "image_url": "https://via.placeholder.com/300x400?text=Draft+Booster"
                },
                {
                    "id": "mkm-collector",
                    "name": "Murders at Karlov Manor Collector Booster",
                    "description": "15 premium cards per pack",
                    "price": 24.99,
                    "image_url": "https://via.placeholder.com/300x400?text=Collector+Booster"
                },
                {
                    "id": "mkm-bundle",
                    "name": "Murders at Karlov Manor Bundle",
                    "description": "8 Draft Boosters + accessories",
                    "price": 44.99,
                    "image_url": "https://via.placeholder.com/300x400?text=Bundle"
                },
                {
                    "id": "mkm-box",
                    "name": "Murders at Karlov Manor Draft Booster Box",
                    "description": "36 Draft Boosters",
                    "price": 139.99,
                    "image_url": "https://via.placeholder.com/300x400?text=Booster+Box"
                }
            ]
        },
        {
            "name": "Outlaws of Thunder Junction",
            "set_code": "otj",
            "products": [
                {
                    "id": "otj-booster",
                    "name": "Outlaws of Thunder Junction Draft Booster",
                    "description": "15 cards per pack",
                    "price": 4.99,
                    "image_url": "https://via.placeholder.com/300x400?text=Draft+Booster"
                },
                {
                    "id": "otj-collector",
                    "name": "Outlaws of Thunder Junction Collector Booster",
                    "description": "15 premium cards per pack",
                    "price": 24.99,
                    "image_url": "https://via.placeholder.com/300x400?text=Collector+Booster"
                },
                {
                    "id": "otj-bundle",
                    "name": "Outlaws of Thunder Junction Bundle",
                    "description": "8 Draft Boosters + accessories",
                    "price": 44.99,
                    "image_url": "https://via.placeholder.com/300x400?text=Bundle"
                },
                {
                    "id": "otj-box",
                    "name": "Outlaws of Thunder Junction Draft Booster Box",
                    "description": "36 Draft Boosters",
                    "price": 139.99,
                    "image_url": "https://via.placeholder.com/300x400?text=Booster+Box"
                }
            ]
        }
    ]
    
    return render_template("shop/packs.html", featured_sets=featured_sets, sets=sets)


@bp.route("/cart")
def cart():
    """Display the shopping cart."""
    cart_items = session.get("cart_items", [])
    total = sum(item.get("price", 0) * item.get("quantity", 0) for item in cart_items)
    return render_template("shop/cart.html", cart_items=cart_items, total=total)


@bp.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    """Add an item to the shopping cart."""
    try:
        item_id = request.form.get("item_id")
        if item_id.isdigit():
            item_id = int(item_id)
            
        item_name = request.form.get("item_name")
        item_price = float(request.form.get("item_price"))
        
        # Initialize cart if it doesn't exist
        if "cart_items" not in session:
            session["cart_items"] = []
        
        # Check if item already in cart
        item_found = False
        for item in session["cart_items"]:
            if item["id"] == item_id:
                item["quantity"] += 1
                item_found = True
                break
        
        # Add new item if not found
        if not item_found:
            session["cart_items"].append({
                "id": item_id,
                "name": item_name,
                "price": item_price,
                "quantity": 1
            })
        
        # Update cart count
        cart_count = sum(item.get("quantity", 0) for item in session["cart_items"])
        session["cart_count"] = cart_count
        
        # Save the session
        session.modified = True
        
        return jsonify({"success": True, "cart_count": cart_count})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@bp.route("/remove_from_cart", methods=["POST"])
def remove_from_cart():
    """Remove an item from the shopping cart."""
    try:
        item_id = request.form.get("item_id")
        if item_id.isdigit():
            item_id = int(item_id)
        
        if "cart_items" in session:
            session["cart_items"] = [item for item in session["cart_items"] if item["id"] != item_id]
            
            # Update cart count
            cart_count = sum(item.get("quantity", 0) for item in session["cart_items"])
            session["cart_count"] = cart_count
            
            # Save the session
            session.modified = True
        
        return jsonify({"success": True, "cart_count": cart_count})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@bp.route("/update_quantity", methods=["POST"])
def update_quantity():
    """Update the quantity of an item in the cart."""
    try:
        item_id = request.form.get("item_id")
        if item_id.isdigit():
            item_id = int(item_id)
            
        quantity = int(request.form.get("quantity"))
        
        if quantity < 1:
            return jsonify({"success": False, "error": "Quantity must be at least 1"})
        
        if "cart_items" in session:
            for item in session["cart_items"]:
                if item["id"] == item_id:
                    item["quantity"] = quantity
                    break
            
            # Update cart count
            cart_count = sum(item.get("quantity", 0) for item in session["cart_items"])
            session["cart_count"] = cart_count
            
            # Save the session
            session.modified = True
        
        return jsonify({"success": True, "cart_count": cart_count})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@bp.route("/checkout")
@login_required
def checkout():
    """Process the checkout."""
    # In a real implementation, this would process payment and create orders
    # For now, we'll just clear the cart and show a confirmation
    session["cart_items"] = []
    session["cart_count"] = 0
    flash("Your order has been placed successfully!")
    return redirect(url_for("shop.inventory"))