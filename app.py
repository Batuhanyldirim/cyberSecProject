from flask import Flask,json,jsonify,request
from flask_sqlalchemy import SQLAlchemy
import random
from string import ascii_letters, digits
from base64 import b64encode




app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userName = db.Column(db.String(40))
    password = db.Column(db.String(60))
    session_token = db.Column(db.String(10))

class Email(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email  = db.Column(db.String(40))








@app.route('/login', methods=['POST'])
def login():
    # get username and password from request
    username = request.form.get('username')
    password = request.form.get('password')
    

    # query database for user with matching username and password
    user = User.query.filter_by(userName=username, password=password).first()

    # if user is found, return success message
    if user:
        session_token = ''.join(random.choices(ascii_letters + digits, k=10))

        # assign session token to user
        user.session_token = session_token

        # save changes to database
        db.session.commit()

        # return success message with session token
        return json.jsonify({'status': 'success', 'session_token': session_token})

    # if user is not found, return error message
    return json.jsonify({'status': 'error', 'message': 'Invalid username or password'})


""" @app.route('/mail/view', methods=['GET'])
def view_emails():
    # get page and entries parameters from request
    page = request.args.get('page', default=1, type=int)
    entries = request.args.get('entries', default=20, type=int)

    # query database for emails
    emails = Email.query.paginate(page=page, per_page=entries)

    emailStrings = [item.email for item in emails.items]


    # return emails as JSON response
    return json.jsonify({'emails': emailStrings})
 """

@app.route('/base64/encode', methods=['GET'])
def base64_encode():
    # Hardcoded username and password
    username = "user1"
    password = "p@ssw0rd"

    # Concatenate the username and password separated by a colon
    auth_string = f"{username}:{password}"

    # Encode the auth string in Base64
    encoded_auth_string = b64encode(auth_string.encode()).decode()

    # Return the encoded auth string in the response
    return jsonify({"encoded_auth_string": encoded_auth_string})



@app.route('/mail/view', methods=['GET'])
def view_emails():
    # get session token and username from request
    session_token = request.args.get('session_token')
    username = request.args.get('username')

    # query database for user with matching session token and username
    user = User.query.filter_by(session_token=session_token, userName=username).first()

    # if user is found, return paginated email list
    if user:
        # get page and entries parameters from request
        page = request.args.get('page', default=1, type=int)
        entries = request.args.get('entries', default=20, type=int)

        if entries > 20:
            return json.jsonify({'status': 'error', 'message': 'entry limit exceeded'})


        # query database for emails
        emails = Email.query.paginate(page=page, per_page=entries)

        emailStrings = [item.email for item in emails.items]

        # return emails as JSON response
        return json.jsonify({'emails': emailStrings})

    # if user is not found, return error message
    return json.jsonify({'status': 'error', 'message': 'Invalid session token or username'})


with app.app_context():
    db.create_all()
   
    
    db.session.bulk_insert_mappings(Email, [{'email': ''.join(random.choices(ascii_letters + digits, k=25)) + '@gmail.com'} for _ in range(1000000)])
    db.session.commit()   

    db.session.bulk_insert_mappings(User, [
        {'userName': 'user1', 'password': 'password1'}, 
        {'userName': 'user2', 'password': 'password2'}
        ])
    db.session.commit() 




if __name__ == '__main__':
    app.run()
