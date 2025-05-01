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
        item_id = int(request.form.get("item_id"))
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
        item_id = int(request.form.get("item_id"))
        
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
        item_id = int(request.form.get("item_id"))
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

# Add to bigdecks/shop.py

@bp.route("/shop/packs")
def packs():
    """Display booster packs and boxes for purchase."""
    # Featured sets with nice artwork
    featured_sets = [
        {
            "name": "Ravnica Remastered",
            "set_code": "RVR",
            "description": "A powerful set featuring the best cards from across all Ravnica blocks.",
            "release_date": "January 12, 2025",
            "image_url": "https://m.media-amazon.com/images/I/81jGHGpJ6YL._AC_UF894,1000_QL80_.jpg"
        },
        {
            "name": "Bloomburrow",
            "set_code": "BBR",
            "description": "Explore a whimsical world of woodland creatures with their own societies and magic.",
            "release_date": "March 15, 2025",
            "image_url": "https://i0.wp.com/mtgazone.com/wp-content/uploads/2024/02/Bloomburrow-Key-Art.jpg"
        },
        {
            "name": "Modern Horizons 3",
            "set_code": "MH3",
            "description": "The latest Modern Horizons set, pushing the boundaries of Modern format once again.",
            "release_date": "April 18, 2025",
            "image_url": "https://i.redd.it/modern-horizons-3-is-set-to-release-on-june-14th-2024-v0-7kq1c8zqvtuc1.jpg?s=f2ada48c7feb1ed6ca5e2da4195b81d064dcfc78"
        }
    ]
    
    # Sets and their products
    sets = [
        {
            "name": "Ravnica Remastered",
            "set_code": "RVR",
            "products": [
                {
                    "id": "rvr_booster",
                    "name": "Ravnica Remastered Draft Booster",
                    "description": "15 cards per pack, great for drafting.",
                    "price": 4.99,
                    "image_url": "https://m.media-amazon.com/images/I/71e7n7GrxfL._AC_UF894,1000_QL80_.jpg"
                },
                {
                    "id": "rvr_collector",
                    "name": "Ravnica Remastered Collector Booster",
                    "description": "15 cards per pack including foils and special treatments.",
                    "price": 24.99,
                    "image_url": "https://m.media-amazon.com/images/I/71KGq+SwhYL._AC_UF894,1000_QL80_.jpg"
                },
                {
                    "id": "rvr_box",
                    "name": "Ravnica Remastered Draft Booster Box",
                    "description": "36 Draft Booster packs.",
                    "price": 149.99,
                    "image_url": "https://m.media-amazon.com/images/I/810X4hXhX-L._AC_UF894,1000_QL80_.jpg"
                },
                {
                    "id": "rvr_collector_box",
                    "name": "Ravnica Remastered Collector Box",
                    "description": "12 Collector Booster packs.",
                    "price": 249.99,
                    "image_url": "https://m.media-amazon.com/images/I/91P8FrCzDrL._AC_UF894,1000_QL80_.jpg"
                }
            ]
        },
        {
            "name": "Bloomburrow",
            "set_code": "BBR",
            "products": [
                {
                    "id": "bbr_play",
                    "name": "Bloomburrow Play Booster",
                    "description": "10 cards per pack, optimized for gameplay.",
                    "price": 5.99,
                    "image_url": "https://cdn11.bigcommerce.com/s-xoh7bo/images/stencil/original/products/5969/90969/184892_200w__25258.1709150818.jpg"
                },
                {
                    "id": "bbr_collector",
                    "name": "Bloomburrow Collector Booster",
                    "description": "15 cards per pack with the most sought-after treatments.",
                    "price": 29.99,
                    "image_url": "https://cdn.shopify.com/s/files/1/0355/9531/7933/files/184893_200w_6f92ecca-46c8-43d1-a99e-f52dcc8d9c6a_large.jpg"
                },
                {
                    "id": "bbr_box",
                    "name": "Bloomburrow Play Booster Box",
                    "description": "18 Play Booster packs.",
                    "price": 99.99,
                    "image_url": "https://i0.wp.com/legitmtg.com/wp-content/uploads/2024/02/Bloom-Burrow-Play-Booster-Box.jpg"
                },
                {
                    "id": "bbr_bundle",
                    "name": "Bloomburrow Bundle",
                    "description": "8 Play Boosters, 40 lands, and accessories.",
                    "price": 49.99,
                    "image_url": "https://d1rw89lz12ur5s.cloudfront.net/photo/coretcg/file/1864990/414c39f01b6a4d97852df74be3d2d7ad.jpg"
                }
            ]
        },
        {
            "name": "Modern Horizons 3",
            "set_code": "MH3",
            "products": [
                {
                    "id": "mh3_draft",
                    "name": "Modern Horizons 3 Draft Booster",
                    "description": "15 cards per pack with a guaranteed premium Modern-legal reprint.",
                    "price": 7.99,
                    "image_url": "https://upload.wikimedia.org/wikipedia/en/a/a2/Modern_Horizons_booster_pack.jpg"
                },
                {
                    "id": "mh3_collector",
                    "name": "Modern Horizons 3 Collector Booster",
                    "description": "15 cards with special treatments and high-value reprints.",
                    "price": 34.99,
                    "image_url": "https://cdn.shopify.com/s/files/1/0567/4178/1416/files/MH2CB_PACK.png"
                },
                {
                    "id": "mh3_draft_box",
                    "name": "Modern Horizons 3 Draft Booster Box",
                    "description": "36 Draft Booster packs.",
                    "price": 269.99,
                    "image_url": "https://m.media-amazon.com/images/I/A1R60dNMhVL._AC_UF1000,1000_QL80_.jpg"
                },
                {
                    "id": "mh3_collector_box",
                    "name": "Modern Horizons 3 Collector Box",
                    "description": "12 Collector Booster packs for the premium experience.",
                    "price": 399.99,
                    "image_url": "https://m.media-amazon.com/images/I/91T23m8g+1L._AC_UF894,1000_QL80_.jpg"
                }
            ]
        }
    ]
    
    return render_template("shop/packs.html", featured_sets=featured_sets, sets=sets)