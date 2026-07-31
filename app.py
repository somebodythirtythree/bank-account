from flask import Flask, render_template, request, redirect, flash, session
import pymongo, datetime, os
from bson.objectid import ObjectId
from dotenv import load_dotenv
import certifi

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
client = pymongo.MongoClient(os.getenv('CONNECTION_STRING'), tlsCAFile=certifi.where())
accounts = client.accounts

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html')
    elif request.method == 'POST':
        if 'login' in request.form:
            username = request.form.get('username')
            password = request.form.get('password')
            user = accounts.users.find_one(
                {'username': username, 'password': password}
            )
            if not user:
                flash("Wrong username or password")
                return redirect('/')
            flash("Login Success")
            session['username'] = username
            return redirect('/home')
        
        elif 'register' in request.form:
            username = request.form.get('username')
            password = request.form.get('password')
            if accounts.users.find_one({'username': username}):
                flash("Username already exists. Please choose a different one.")
                return redirect('/')
            accounts.users.insert_one({
                'username': username,
                'password': password,
                'balance': 0,
                'transactions': []
            })
            flash("Registration successful! Please log in.")
            return redirect('/')

@app.route('/home', methods=['GET', 'POST'])
def home():
    if 'username' not in session:
        flash("Please log in first to access the home page.")
        return redirect('/')
    
    if request.method == 'GET':
        user = accounts.users.find_one({'username': session['username']})
        return render_template('home.html', user=user)
    elif request.method == 'POST':
        print(request.form)
        transaction_type = request.form.get('transactionType')
        if transaction_type == 'deposit':
            amount = float(request.form.get('amount'))
            accounts.users.update_one(
                {'username': session['username']},
                {
                    '$inc': {'balance': amount},
                    '$push': {'transactions': {
                        'type': 'deposit',
                        'amount': amount,
                        'date': datetime.datetime.now()
                    }}
                }
            )
            return redirect('/home')
        elif transaction_type == 'withdraw':
            amount = float(request.form.get('amount'))
            user = accounts.users.find_one({'username': session['username']})
            if user['balance'] < amount:
                flash("Insufficient funds.")
                return redirect('/home')
            accounts.users.update_one(
                {'username': session['username']},
                {
                    '$inc': {'balance': -amount},
                    '$push': {'transactions': {
                        'type': 'withdraw',
                        'amount': amount,
                        'date': datetime.datetime.now()
                    }}
                }
            )
            return redirect('/home')


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out. Have a nice day!")
    return redirect('/')

@app.route('/clear_transactions')
def clear_transactions():
    if 'username' not in session:
        flash("Please log in first to clear transaction history.")
        return redirect('/')
    
    accounts.users.update_one(
        {'username': session['username']},
        {'$set': {'transactions': [], 'balance': 0}}
    )
    flash("Transaction history cleared and balance reset")
    return redirect('/home')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)