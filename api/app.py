from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)

app.secret_key = '3w45768j6565t6879m0'

@app.route('/')
def home():
    return render_template('index.html', logged_in=session.get('logged_in', False))

@app.route('/login', methods=['GET', 'POST'])
def login():
    session['logged_in'] = False
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == 'admin' and password == 'password':
            # Log the user in by setting a session variable
            session['logged_in'] = True
            next_page = request.form.get('next') or url_for('home')
            return redirect(next_page)
        else:
            # If login fails, return to login page with an error
            return render_template('login.html', error=True, next=request.form.get('next'))

    # Handle the GET request
    next_page = request.args.get('next', url_for('home'))
    return render_template('login.html', next=next_page)

@app.route('/logout')
def logout():
    session['logged_in'] = False
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)