from flask import Flask,json
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
import random
from string import ascii_letters, digits
from flask import request
import os
import smtplib
from email.message import EmailMessage


import threading

from apscheduler.schedulers.background import BackgroundScheduler




app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

auth = HTTPBasicAuth()


db = SQLAlchemy(app)

email_password = os.environ.get('EMAIL_PASSWORD')



DAILY_MAX_EMAILS = 100
LIMIT_PER_REQUEST = 20

# email server and authentication details
smtp_server = "smtp.gmail.com"
smtp_port = 587
smtp_username = "flaskurban@gmail.com"
smtp_password = email_password
subject = "Daily email limit exceeded"


scheduler = BackgroundScheduler()


def refresh_limits():
    with app.app_context():
        print('refreshing limits')
        users = User.query.all()
        for user in users:
            user.remaining_email_limit = DAILY_MAX_EMAILS
            user.email_sent = False
        db.session.commit()

scheduler.add_job(func=refresh_limits, trigger="interval", minutes=1)


class Email(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email  = db.Column(db.String(40))

@auth.verify_password
def verify_password(user_name, password):
    user = User.query.filter_by(username=user_name).first()
    return user if user and user.password == password else False


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False) 
    remaining_email_limit = db.Column(db.Integer, nullable=False)
    email_sent = db.Column(db.Boolean, default=False, nullable=False)



def send_email(user, errorMessage):


    # recipient's email address and email content
    to_email = user.email
    body = errorMessage

    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['To'] = to_email

    # TODO login once and reuse connection (doesn't matter much as there are only 10 users)
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)

    user.email_sent = True




@app.route('/mail/view', methods=['GET'])
@auth.login_required
def view_emails():
    # get page and entries parameters from request
    user = auth.current_user()

    page = request.args.get('page', default=1, type=int)
    entries = request.args.get('entries', default=LIMIT_PER_REQUEST, type=int)

    entriesLimited  = max(min(entries, LIMIT_PER_REQUEST), 1)


    if user.remaining_email_limit < entriesLimited:
        # TODO: send email to user to notify them that they have exceeded their daily 
        errorMessage = 'You can only request {} more emails today'.format(user.remaining_email_limit)
        if not user.email_sent:

            user.email_sent = True
            thread = threading.Thread(target=send_email, args=(user, errorMessage))
            thread.start()
            db.session.commit()






        return json.jsonify({'error': errorMessage}), 429

    
    user.remaining_email_limit -= entriesLimited



    # query database for emails
    emails = Email.query.paginate(page=page, per_page=entries)
    db.session.commit()

    emailStrings = [item.email for item in emails.items]


    # return emails as JSON response
    return json.jsonify({'emails': emailStrings})


with app.app_context():
    db.create_all()
   
    
    db.session.bulk_insert_mappings(Email, [{'email': ''.join(random.choices(ascii_letters + digits, k=25)) + '@gmail.com'} for _ in range(1000000)])

    
    users = [User(username="user{}".format(i),
              email="user{}@example.com".format(i),
              password="password{}".format(i),
              remaining_email_limit=DAILY_MAX_EMAILS) for i in range(10)]
        
    

    db.session.bulk_save_objects(users)

    



    
    db.session.commit()    


    scheduler.start()



if __name__ == '__main__':
    app.run()
