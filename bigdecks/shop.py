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
    # Fetch 15 random cards from the database
    inventory_items = []
    for _ in range(15):
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
            "image_url": card.image_uris.normal or card.image_uris.highest_resolution
        })
    
    return render_template("shop/inventory.html", inventory_items=inventory_items)


@bp.route("/shop/packs")
def packs():
    """Display booster packs and boxes for sale."""
    # Mock data for featured sets
    featured_sets = [
        {
            "name": "Lost Caverns of Ixalan",
            "description": "Delve into ancient Maya-inspired caverns filled with dinosaurs and pirates.",
            "release_date": "November 2023",
            "image_url": "https://cards.scryfall.io/art_crop/front/6/b/6b9bb8a1-1830-4895-8fcf-56c3ac1889b4.jpg",
            "set_code": "lci"
        },
        {
            "name": "Murders at Karlov Manor",
            "description": "A murder mystery set in the city of Ravnica.",
            "release_date": "February 2024",
            "image_url": "https://cards.scryfall.io/art_crop/front/9/5/95f2d22a-8614-4ddb-9e91-9a444524825f.jpg",
            "set_code": "mkm"
        },
        {
            "name": "Outlaws of Thunder Junction",
            "description": "Wild west-themed set featuring notorious outlaws.",
            "release_date": "April 2024",
            "image_url": "https://cards.scryfall.io/art_crop/front/3/b/3b01788a-bc01-4ede-a7f1-3d698a2a10f4.jpg",
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
                    "image_url": "https://cards.scryfall.io/normal/front/6/b/6b9bb8a1-1830-4895-8fcf-56c3ac1889b4.jpg"
                },
                {
                    "id": "lci-collector",
                    "name": "Lost Caverns of Ixalan Collector Booster",
                    "description": "15 premium cards per pack",
                    "price": 24.99,
                    "image_url": "https://cards.scryfall.io/normal/front/1/d/1d60022a-df1b-4970-b08d-a859fc6c0d9f.jpg"
                },
                {
                    "id": "lci-bundle",
                    "name": "Lost Caverns of Ixalan Bundle",
                    "description": "8 Draft Boosters + accessories",
                    "price": 44.99,
                    "image_url": "https://cards.scryfall.io/normal/front/f/4/f427911f-0411-4596-b5af-1a635942b31a.jpg"
                },
                {
                    "id": "lci-box",
                    "name": "Lost Caverns of Ixalan Draft Booster Box",
                    "description": "36 Draft Boosters",
                    "price": 139.99,
                    "image_url": "https://cards.scryfall.io/normal/front/d/9/d992ee97-29fd-49c2-a181-7fc8bfffdde8.jpg"
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
                    "image_url": "https://cards.scryfall.io/normal/front/9/5/95f2d22a-8614-4ddb-9e91-9a444524825f.jpg"
                },
                {
                    "id": "mkm-collector",
                    "name": "Murders at Karlov Manor Collector Booster",
                    "description": "15 premium cards per pack",
                    "price": 24.99,
                    "image_url": "https://cards.scryfall.io/normal/front/5/4/547d95d9-4c8f-489d-a08a-6a8c25653543.jpg"
                },
                {
                    "id": "mkm-bundle",
                    "name": "Murders at Karlov Manor Bundle",
                    "description": "8 Draft Boosters + accessories",
                    "price": 44.99,
                    "image_url": "https://cards.scryfall.io/normal/front/6/5/657b81a0-4ce3-4aa4-94c8-f82d8c1cf3e0.jpg"
                },
                {
                    "id": "mkm-box",
                    "name": "Murders at Karlov Manor Draft Booster Box",
                    "description": "36 Draft Boosters",
                    "price": 139.99,
                    "image_url": "https://cards.scryfall.io/normal/front/c/3/c3a9a640-8508-4baf-a76f-71f05f304b64.jpg"
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
                    "image_url": "https://cards.scryfall.io/normal/front/3/b/3b01788a-bc01-4ede-a7f1-3d698a2a10f4.jpg"
                },
                {
                    "id": "otj-collector",
                    "name": "Outlaws of Thunder Junction Collector Booster",
                    "description": "15 premium cards per pack",
                    "price": 24.99,
                    "image_url": "https://cards.scryfall.io/normal/front/7/0/705c3d3c-48d3-4582-9200-0c21a8c53f5d.jpg"
                },
                {
                    "id": "otj-bundle",
                    "name": "Outlaws of Thunder Junction Bundle",
                    "description": "8 Draft Boosters + accessories",
                    "price": 44.99,
                    "image_url": "https://cards.scryfall.io/normal/front/a/c/acbfd3f3-c58b-4e58-9de5-fd60ffcb4dec.jpg"
                },
                {
                    "id": "otj-box",
                    "name": "Outlaws of Thunder Junction Draft Booster Box",
                    "description": "36 Draft Boosters",
                    "price": 139.99,
                    "image_url": "https://cards.scryfall.io/normal/front/f/8/f8a58b9b-ca83-4755-ba13-dee993f2a214.jpg"
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
        item_id = int(request.form.get("item_id")) if request.form.get("item_id").isdigit() else request.form.get("item_id")
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
    cart_items = session.get("cart_items", [])
    
    if not cart_items:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("shop.inventory"))
    
    # Calculate order total
    total = sum(item.get("price", 0) * item.get("quantity", 0) for item in cart_items)
    
    # If form submitted, process the order
    if request.method == "POST":
        # Here you would add code to:
        # 1. Process payment
        # 2. Create order in database
        # 3. Clear cart
        
        # For now, just clear the cart and show confirmation
        session["cart_items"] = []
        session["cart_count"] = 0
        flash("Your order has been placed successfully!", "success")
        return redirect(url_for("shop.inventory"))
    
    # Display checkout page with order summary
    return render_template("shop/checkout.html", cart_items=cart_items, total=total)