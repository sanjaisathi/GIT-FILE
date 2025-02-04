from flask import Flask, request, render_template, redirect, url_for, session, flash
from pymongo import MongoClient
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
db = client['farmer_market_db'] 
users_collection = db['users']  
products_collection = db['products']  
orders_collection = db['orders']  

# Upload folder for images
UPLOAD_FOLDER = 'static/uploads/'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    user_type = request.form['user_type']
    contact_details = request.form['contact']

    if users_collection.find_one({'username': username}):
        flash('Username already exists')
        return redirect(url_for('index'))

    user_data = {
        'username': username,
        'password': password,
        'type': user_type,
        'contact': contact_details
    }

    users_collection.insert_one(user_data)
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    user = users_collection.find_one({'username': username})

    if user and user['password'] == password:
        session['username'] = username
        session['user_type'] = user['type']
        session['contact'] = user['contact']
        return redirect(url_for('dashboard'))
    flash('Invalid credentials')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        user_type = session['user_type']
        products = list(products_collection.find())

        if user_type == 'seller':
            seller_orders = list(orders_collection.find({'seller_contact': session['contact']}))
            return render_template('seller_dashboard.html', products=products, orders=seller_orders, contact=session['contact'])
        elif user_type == 'customer':
            orders = list(orders_collection.find({'buyer': session['username']}))
            return render_template('buyer_dashboard.html', products=products, orders=orders, contact=session['contact'])
    return redirect(url_for('index'))

@app.route('/add_product', methods=['POST'])
def add_product():
    if 'username' in session and session['user_type'] == 'seller':
        product_name = request.form['name']
        product_description = request.form['description']
        product_price = request.form['price']
        product_quantity = request.form['quantity']

        if 'image' in request.files:
            image = request.files['image']
            image_path = os.path.join(UPLOAD_FOLDER, image.filename)
            image.save(image_path)
            image_url = f'/static/uploads/{image.filename}'
        else:
            image_url = None

        product_data = {
            'name': product_name,
            'description': product_description,
            'price': product_price,
            'quantity': product_quantity,
            'seller': session['username'],
            'contact': session['contact'],
            'image': image_url
        }

        products_collection.insert_one(product_data)
    return redirect(url_for('dashboard'))

@app.route('/order_product/<product_name>', methods=['POST'])
def order_product(product_name):
    if 'username' in session and session['user_type'] == 'customer':
        product = products_collection.find_one({'name': product_name})
        if product:
            order_data = {
                'product_name': product_name,
                'buyer': session['username'],
                'buyer_contact': session['contact'],
                'seller_contact': product['contact']
            }
            orders_collection.insert_one(order_data)
    return redirect(url_for('dashboard'))

@app.route('/edit_product/<product_name>', methods=['GET', 'POST'])
def edit_product(product_name):
    product = products_collection.find_one({'name': product_name})

    if request.method == 'POST':
        new_description = request.form['description']
        new_price = request.form['price']
        new_quantity = request.form['quantity']

        if 'image' in request.files and request.files['image'].filename != '':
            image = request.files['image']
            image_path = os.path.join(UPLOAD_FOLDER, image.filename)
            image.save(image_path)
            image_url = f'/static/uploads/{image.filename}'
        else:
            image_url = product['image'] 

        products_collection.update_one(
            {'name': product_name},
            {'$set': {
                'description': new_description,
                'price': new_price,
                'quantity': new_quantity,
                'image': image_url
            }}
        )
        return redirect(url_for('dashboard'))

    return render_template('edit_product.html', product=product)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
