import json
import os
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy  # Importación correcta
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column


# from models import Base, Balance, Product, Transaction

# INIT APP #

class Base(DeclarativeBase):
    pass

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for flash messages

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
# db = SQLAlchemy(app)
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# DATABASE ORM MODELS #

class Transaction(db.Model):
    # id = db.Column(db.Integer, primary_key=True)
    # date = db.Column(db.DateTime, default=datetime.utcnow)
    # description = db.Column(db.String(255), nullable=False)
    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    description: Mapped[str] = mapped_column(String(255), nullable=False)


class Product(db.Model):
    # id = db.Column(db.Integer, primary_key=True)
    # name = db.Column(db.String(100), nullable=False, unique=True)
    # quantity = db.Column(db.Integer, default=0)
    # price = db.Column(db.Float, default=0.0)
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    quantity: Mapped[int] = mapped_column(default=0)
    price: Mapped[float] = mapped_column(default=0.0)


class Balance(db.Model):
    # id = db.Column(db.Integer, primary_key=True)
    # amount = db.Column(db.Float, default=0.0)
    id: Mapped[int] = mapped_column(primary_key=True)
    amount: Mapped[float] = mapped_column(default=0.0)


with app.app_context():
    print("This function runs before the first request is processed.")
    db.create_all()
    # Verificamos si existe un registro en Balance
    balance = Balance.query.first()
    if not balance:
        # Si no existe, se crea un registro por defecto
        print("No balance found. Initializing with a default value.")
        db.session.add(Balance(amount=0.0))  # Balance inicial en 0.0
        db.session.commit()

# ROUTES #


@app.route('/')
def main():
    balance = Balance.query.first()
    stock_level = Product.query.with_entities(db.func.sum(Product.quantity)).scalar()
    return render_template('main.html', stock_level=stock_level, account_balance=balance.amount)


@app.route('/purchase', methods=['GET', 'POST'])
def purchase():
    if request.method == 'POST':
        product_name = request.form.get('product-name')
        unit_price = request.form.get('unit-price')
        num_pieces = request.form.get('number-pieces')

        if not product_name or not unit_price or not num_pieces:
            flash('Please fill in all fields')
            return redirect(url_for('purchase'))

        try:
            unit_price = float(unit_price)
            num_pieces = int(num_pieces)

            if unit_price <= 0 or num_pieces < 1:
                flash('Invalid input: Unit price must be greater than zero and number of pieces must be at least 1')
                return redirect(url_for('purchase'))

            # Buscar o crear el producto
            product = Product.query.filter_by(name=product_name).first()
            if product:
                product.quantity += num_pieces
            else:
                product = Product(name=product_name, quantity=num_pieces, price=unit_price)
                db.session.add(product)

            # Actualizar el balance
            balance = Balance.query.first()
            balance.amount -= unit_price * num_pieces
            db.session.add(Transaction(description=f'Purchase of {num_pieces} pieces of {product_name} at ${unit_price:.2f} each'))

            db.session.commit()

            flash('Purchase recorded successfully')
            return redirect(url_for('purchase'))

        except ValueError:
            flash('Invalid input: Please enter valid numbers for unit price and number of pieces')
            return redirect(url_for('purchase'))

    return render_template('purchase.html')

@app.route('/sale', methods=['GET', 'POST'])
def sale():
    if request.method == 'POST':
        product_name = request.form['product-name']
        unit_price = request.form['unit-price']
        num_pieces = request.form['number-pieces']

        if not product_name or not unit_price or not num_pieces:
            flash('Please fill in all fields')
            return redirect(url_for('sale'))

        try:
            unit_price = float(unit_price)
            num_pieces = int(num_pieces)

            if unit_price <= 0 or num_pieces < 1:
                flash('Invalid input: Unit price must be greater than zero and number of pieces must be at least 1')
                return redirect(url_for('sale'))

            product = Product.query.filter_by(name=product_name).first()
            if not product or product.quantity < num_pieces:
                flash('Insufficient stock for sale')
                return redirect(url_for('sale'))

            product.quantity -= num_pieces
            balance = Balance.query.first()
            balance.amount += unit_price * num_pieces
            db.session.add(Transaction(description=f'Sale of {num_pieces} pieces of {product_name} at ${unit_price:.2f} each'))
            db.session.commit()

            flash('Sale recorded successfully')
            return redirect(url_for('sale'))

        except ValueError:
            flash('Invalid input: Please enter valid numbers for unit price and number of pieces')
            return redirect(url_for('sale'))

    return render_template('sale.html')

@app.route('/balance', methods=['GET', 'POST'])
def balance():
    balance = Balance.query.first()

    if request.method == 'POST':
        action = request.form['action']
        amount = request.form['amount']

        # Verifica que los campos estén presentes
        if not action or not amount:
            return jsonify({'success': False, 'message': 'Please fill in all fields'}), 400

        try:
            amount = float(amount)
            #balance = Balance.query.first()

            # Verifica si la acción es válida
            if action == 'add':
                balance.amount += amount
                description = f'Added €{amount:.2f} to account balance'
            elif action == 'subtract':
                balance.amount -= amount
                description = f'Subtracted €{amount:.2f} from account balance'
            else:
                return jsonify({'success': False, 'message': 'Invalid action selected'}), 400

            # Registra la transacción
            db.session.add(Transaction(description=description))
            db.session.commit()

            # Responde con éxito
            return jsonify({'success': True, 'message': 'Balance change recorded successfully'}), 200

        except Exception as e:
            # Si ocurre cualquier error, se muestra el error detallado
            return jsonify({'success': False, 'message': f'Error processing request: {str(e)}'}), 500

    # Si es un GET, solo devuelve la página de balance
    return render_template('balance.html')


@app.route('/api/balance', methods=['GET'])
def get_balance():
    balance = Balance.query.first()
    stock_level = Product.query.with_entities(db.func.sum(Product.quantity)).scalar()

    # Si balance no existe, devolvemos un error, por seguridad.
    if not balance:
        return jsonify({'error': 'Balance not found'}), 500

    return jsonify({'balance': balance.amount, 'stock_level': stock_level})


@app.route('/history/', methods=['GET'])
def get_history():
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from_date_str = request.args.get('from')
        to_date_str = request.args.get('to')

        query = Transaction.query

        if from_date_str and to_date_str:
            try:
                from_date = datetime.strptime(from_date_str, '%Y-%m-%d')
                to_date = datetime.strptime(to_date_str, '%Y-%m-%d')
                query = query.filter(Transaction.date.between(from_date, to_date))
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

        records = query.all()
        return jsonify([{
            'id': record.id,
            'date': record.date.strftime('%Y-%m-%d'),
            'description': record.description
        } for record in records])

    return render_template('history.html')

transactions_file = 'transactions.json'
# Load transactions from file if it exists
if os.path.exists(transactions_file):
    with open(transactions_file, 'r') as file:
        transactions = json.load(file)
else:
    transactions = []

if __name__ == '__main__':
    app.run(debug=True)
