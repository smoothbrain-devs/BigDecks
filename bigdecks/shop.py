"""Shop functionality

This module contains the routes and logic for the card shop.
"""

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort

from bigdecks.auth import login_required
from bigdecks.database import get_db_connection

bp = Blueprint('shop', __name__, url_prefix='/shop')

# had to input like this so they stopped switch everytime you changed tabs
featured_cards = [
    {
        'id': 1,
        'scryfall_id': 'e9d5aee0-5963-41db-a22b-cfea40a967a3',
        'name': 'Black Lotus',
        'set_name': 'Limited Edition Alpha',
        'image_uri': 'https://cards.scryfall.io/normal/front/b/d/bd8fa327-dd41-4737-8f19-2cf5eb1f7cdd.jpg',
        'price': '10000.00'
    },
    {
        'id': 2,
        'scryfall_id': 'a1b4e28e-6376-4976-b3be-db3dc6ea7a21',
        'name': 'Jace, the Mind Sculptor',
        'set_name': 'Worldwake',
        'image_uri': 'https://cards.scryfall.io/normal/front/c/8/c8817585-0d32-4d56-9142-0d29512e86a9.jpg',
        'price': '79.99'
    },
    {
        'id': 3,
        'scryfall_id': '54b7ede0-b9d1-4bf9-8bbc-75ad6c7ea6c7',
        'name': 'Liliana of the Veil',
        'set_name': 'Innistrad',
        'image_uri': 'https://cards.scryfall.io/normal/front/e/6/e653437e-2e56-4443-aec5-5bb7d8860238.jpg',
        'price': '44.99'
    },
    {
        'id': 4,
        'scryfall_id': '6984e65f-4a11-4fce-82f4-8aae4e2a2a69',
        'name': 'Tarmogoyf',
        'set_name': 'Future Sight',
        'image_uri': 'https://cards.scryfall.io/normal/front/2/b/2b49dfb7-dbe7-4a2b-b9de-c620a0db2e47.jpg',
        'price': '29.99'
    },
    {
        'id': 5,
        'scryfall_id': '9460e3c6-e745-41d3-a3c8-89a89aa91141',
        'name': 'Force of Will',
        'set_name': 'Alliances',
        'image_uri': 'https://cards.scryfall.io/normal/front/d/d/dd60b291-0a88-4e8e-bef8-76cdfd6c8183.jpg',
        'price': '89.99'
    },
    {
        'id': 6,
        'scryfall_id': 'de0ba1ef-4252-4fd6-983c-e23ee3842d6f',
        'name': 'Mox Sapphire',
        'set_name': 'Limited Edition Alpha',
        'image_uri': 'https://cards.scryfall.io/normal/front/e/8/e8631a91-8abb-46f6-b38d-41c4dd1ce4ac.jpg',
        'price': '7500.00'
    },
    {
        'id': 7,
        'scryfall_id': '8dbac3ad-b454-48fe-9bc2-7f2ba73d7855',
        'name': 'Thoughtseize',
        'set_name': 'Theros',
        'image_uri': 'https://cards.scryfall.io/normal/front/3/1/310a1c46-8331-4a09-9fcb-d942f8102364.jpg',
        'price': '15.99'
    },
    {
        'id': 8,
        'scryfall_id': 'fd7ab235-6ad7-42d7-9f89-873a2fcdb529',
        'name': 'Scalding Tarn',
        'set_name': 'Zendikar',
        'image_uri': 'https://cards.scryfall.io/normal/front/f/2/f2661d4a-450a-433a-b893-b1ee15982494.jpg',
        'price': '29.99'
    },
    {
        'id': 9,
        'scryfall_id': '73519798-ae1f-4484-9ae2-9d5c3f5c85dc',
        'name': 'Wrenn and Six',
        'set_name': 'Modern Horizons',
        'image_uri': 'https://cards.scryfall.io/normal/front/5/b/5bd498cc-a609-4457-9325-6888d59ca36f.jpg',
        'price': '59.99'
    },
    {
        'id': 10,
        'scryfall_id': '1adde0b6-33cb-49bf-86c4-78f4a109c4f4',
        'name': 'Cavern of Souls',
        'set_name': 'Avacyn Restored',
        'image_uri': 'https://cards.scryfall.io/normal/front/1/8/180ae5f5-1632-4659-8a0b-1a65e5ef2da9.jpg',
        'price': '64.99'
    },
    {
        'id': 11,
        'scryfall_id': '53b16b3a-1a20-486d-9e5a-2e64b8953673',
        'name': 'Ragavan, Nimble Pilferer',
        'set_name': 'Modern Horizons 2',
        'image_uri': 'https://cards.scryfall.io/normal/front/a/9/a9738cda-adb1-47fb-9f4c-ecd930228c4d.jpg',
        'price': '74.99'
    },
    {
        'id': 12,
        'scryfall_id': '6ecaa5f2-634a-45ed-a60b-8ce7a1e97d9d',
        'name': 'Dockside Extortionist',
        'set_name': 'Commander 2019',
        'image_uri': 'https://cards.scryfall.io/normal/front/5/7/571bc9eb-8d13-4008-86b5-2e348a326d58.jpg',
        'price': '49.99'
    },
    {
        'id': 13,
        'scryfall_id': '9a15c358-26f7-4794-b962-d1ca03ebec12',
        'name': 'Mana Crypt',
        'set_name': 'Eternal Masters',
        'image_uri': 'https://cards.scryfall.io/normal/front/4/d/4d960186-4559-4af0-bd22-63baa15f8939.jpg',
        'price': '159.99'
    },
    {
        'id': 14,
        'scryfall_id': '1b59a2a2-206f-4c56-976d-6ad455a2759b',
        'name': 'Oko, Thief of Crowns',
        'set_name': 'Throne of Eldraine',
        'image_uri': 'https://cards.scryfall.io/normal/front/3/4/3462a3d0-5552-49fa-9eb7-100960c55891.jpg',
        'price': '19.99'
    },
    {
        'id': 15,
        'scryfall_id': '0a742797-6587-4083-a7b4-5d89f4656d9f',
        'name': 'Vampiric Tutor',
        'set_name': 'Visions',
        'image_uri': 'https://cards.scryfall.io/normal/front/1/8/18bd50f2-c3ba-4217-a2d5-bb771e199706.jpg',
        'price': '69.99'
    },
    {
        'id': 16,
        'scryfall_id': '9d1deb1b-3136-419b-b7d3-9ce5e89b4020',
        'name': 'Mana Drain',
        'set_name': 'Legends',
        'image_uri': 'https://cards.scryfall.io/normal/front/4/3/4385342c-45bc-4435-9f92-3f7c7eae8fff.jpg',
        'price': '189.99'
    },
    {
        'id': 17,
        'scryfall_id': '2cc65c3b-8f75-446d-8b4c-129c7c11d433',
        'name': 'Flooded Strand',
        'set_name': 'Onslaught',
        'image_uri': 'https://cards.scryfall.io/normal/front/8/c/8c2996d9-3287-4480-8c04-7a378e37e3cf.jpg',
        'price': '24.99'
    },
    {
        'id': 18,
        'scryfall_id': '6a0c5bd7-71c6-4c24-9ade-de1b0eb21ce4',
        'name': 'Urza, Lord High Artificer',
        'set_name': 'Modern Horizons',
        'image_uri': 'https://cards.scryfall.io/normal/front/9/e/9e7fb3c0-5159-4d1f-8490-ce4c9a60f567.jpg',
        'price': '39.99'
    },
    {
        'id': 19,
        'scryfall_id': '0d4f3a8d-7b6a-4d2f-b3a8-45a1a8b56e77',
        'name': 'Ancient Tomb',
        'set_name': 'Tempest',
        'image_uri': 'https://cards.scryfall.io/normal/front/b/d/bd3d4b4b-cf31-4f89-8140-9650edb03c7b.jpg',
        'price': '34.99'
    },
    {
        'id': 20,
        'scryfall_id': '1df7c1e4-7ec8-46fd-9bf5-1d10e3b79d73',
        'name': 'Smothering Tithe',
        'set_name': 'Ravnica Allegiance',
        'image_uri': 'https://cards.scryfall.io/normal/front/7/a/7af082fa-86a3-4f7b-966d-2be1f1d0c0bc.jpg',
        'price': '29.99'
    }
]

# same thing but for the packs - RENAMED TO booster_packs to avoid name conflict
booster_packs = [
    {
        'id': 1,
        'name': 'Murders at Karlov Manor',
        'image': 'https://cards.scryfall.io/normal/front/e/3/e3990f47-0b07-406e-8e9a-e9abc13e4b3e.jpg',
        'price': 4.99,
        'description': 'The latest Standard-legal expansion'
    },
    {
        'id': 2,
        'name': 'Bloomburrow',
        'image': 'https://cards.scryfall.io/normal/front/6/8/68465555-bcdf-43f6-8559-75c0b3037c91.jpg',
        'price': 4.99,
        'description': 'Explore the world of adorable animal adventurers'
    },
    {
        'id': 3,
        'name': 'Outlaws of Thunder Junction',
        'image': 'https://cards.scryfall.io/normal/front/1/5/15732a0a-6031-4e1a-a7fa-e96b8dc8b012.jpg',
        'price': 4.99,
        'description': 'Wild West-inspired set with powerful outlaws'
    },
    {
        'id': 4,
        'name': 'Modern Horizons 3',
        'image': 'https://cards.scryfall.io/normal/front/b/0/b065e2a4-5046-4829-a39a-57a2dbda342a.jpg',
        'price': 9.99,
        'description': 'Premium cards designed for Modern format'
    }
]

@bp.route('/')
def index():
    """Display the shop main page with categories."""
    return render_template('shop/index.html')

@bp.route('/singles')
def singles():
    """Display individual cards for sale."""
    return render_template('shop/singles.html', featured_cards=featured_cards)

@bp.route('/packs')
def packs():
    """Display booster packs for sale."""
    return render_template('shop/packs.html', packs=booster_packs)

@bp.route('/cart')
def cart():
    """Display shopping cart contents."""
    if 'cart' not in session:
        session['cart'] = []
    
    cart_items = session['cart']
    total = sum(float(item['price']) * item['quantity'] for item in cart_items)
    
    return render_template('shop/cart.html', cart_items=cart_items, total=total)

@bp.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    """Add item to shopping cart."""
    item_id = request.form.get('item_id')
    item_type = request.form.get('item_type')
    name = request.form.get('name')
    price = request.form.get('price')
    image = request.form.get('image')
    quantity = int(request.form.get('quantity', 1))
    
    if 'cart' not in session:
        session['cart'] = []
    
    # Check if item already in cart
    found = False
    for item in session['cart']:
        if item['item_id'] == item_id and item['item_type'] == item_type:
            item['quantity'] += quantity
            found = True
            break
    
    if not found:
        session['cart'].append({
            'item_id': item_id,
            'item_type': item_type,
            'name': name,
            'price': price,
            'image': image,
            'quantity': quantity
        })
    
    session.modified = True
    flash(f"Added {quantity} {name} to your cart!")
    
    # Redirect back to the referring page
    if item_type == 'pack':
        return redirect(url_for('shop.packs'))
    else:
        return redirect(url_for('shop.singles'))

@bp.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    """Remove item from shopping cart."""
    item_id = request.form.get('item_id')
    item_type = request.form.get('item_type')
    
    if 'cart' in session:
        session['cart'] = [item for item in session['cart'] 
                           if not (item['item_id'] == item_id and item['item_type'] == item_type)]
        session.modified = True
    
    return redirect(url_for('shop.cart'))

@bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """Process checkout."""
    if 'cart' not in session or not session['cart']:
        flash("Your cart is empty!")
        return redirect(url_for('shop.index'))
    
    if request.method == 'POST':
        #  this would process payment and create an order
        # but for now, just clear cart and show success message
        
        # Get form data
        name = request.form.get('name')
        address = request.form.get('address')
        city = request.form.get('city')
        state = request.form.get('state')
        zipcode = request.form.get('zipcode')
        
        # Create a simple order in the database
        db = get_db_connection('users')
        
        # Check if order table exists, if not create it
        try:
            db.execute(
                'SELECT name FROM sqlite_master WHERE type="table" AND name="order"'
            ).fetchone()
        except:
            db.execute('''
                CREATE TABLE IF NOT EXISTS "order" (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    address TEXT NOT NULL,
                    city TEXT NOT NULL,
                    state TEXT NOT NULL,
                    zipcode TEXT NOT NULL,
                    total REAL NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user (id)
                )
            ''')
            db.execute('''
                CREATE TABLE IF NOT EXISTS order_item (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    item_id TEXT NOT NULL,
                    item_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    price REAL NOT NULL,
                    quantity INTEGER NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES "order" (id)
                )
            ''')
            db.commit()
        
        # Calculate total
        total = sum(float(item['price']) * item['quantity'] for item in session['cart'])
        
        # Insert order
        cursor = db.execute(
            'INSERT INTO "order" (user_id, name, address, city, state, zipcode, total)'
            ' VALUES (?, ?, ?, ?, ?, ?, ?)',
            (g.user['id'], name, address, city, state, zipcode, total)
        )
        order_id = cursor.lastrowid
        
        # Insert order items
        for item in session['cart']:
            db.execute(
                'INSERT INTO order_item (order_id, item_id, item_type, name, price, quantity)'
                ' VALUES (?, ?, ?, ?, ?, ?)',
                (order_id, item['item_id'], item['item_type'], item['name'], 
                 item['price'], item['quantity'])
            )
        
        db.commit()
        
        # Clear cart
        session['cart'] = []
        
        flash("Order placed successfully! Thank you for your purchase.")
        return redirect(url_for('shop.order_confirmation', order_id=order_id))
    
    # GET request - show checkout form
    cart_items = session['cart']
    total = sum(float(item['price']) * item['quantity'] for item in cart_items)
    
    return render_template('shop/checkout.html', cart_items=cart_items, total=total)

@bp.route('/order_confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    """Display order confirmation."""
    db = get_db_connection('users')
    
    # Get order details
    order = db.execute(
        'SELECT * FROM "order" WHERE id = ? AND user_id = ?',
        (order_id, g.user['id'])
    ).fetchone()
    
    if order is None:
        abort(404, f"Order id {order_id} doesn't exist or doesn't belong to you.")
    
    # Get order items
    items = db.execute(
        'SELECT * FROM order_item WHERE order_id = ?',
        (order_id,)
    ).fetchall()
    
    return render_template('shop/confirmation.html', order=order, items=items)