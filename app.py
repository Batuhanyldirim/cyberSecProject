from flask import Flask,json
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
import random
from string import ascii_letters, digits
from flask import request

from apscheduler.schedulers.background import BackgroundScheduler




app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

auth = HTTPBasicAuth()


db = SQLAlchemy(app)



DAILY_MAX_EMAILS = 100
LIMIT_PER_REQUEST = 20

scheduler = BackgroundScheduler()


def refresh_limits():
    with app.app_context():
        print("refreshing limits")
        users = User.query.all()
        for user in users:
            user.remaining_email_limit = DAILY_MAX_EMAILS
        db.session.commit()

scheduler.add_job(func=refresh_limits, trigger="interval", days=1)


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




@app.route('/mail/view', methods=['GET'])
@auth.login_required
def view_emails():
    # get page and entries parameters from request
    user = auth.current_user()

    page = request.args.get('page', default=1, type=int)
    entries = request.args.get('entries', default=LIMIT_PER_REQUEST, type=int)

    entriesLimited  = max(min(entries, LIMIT_PER_REQUEST), 1)


    if user.remaining_email_limit < entriesLimited:
        # TODO: send email to user to notify them that they have exceeded their daily limit
        return json.jsonify({'error': 'You can only request {} more emails today'.format(user.remaining_email_limit)}), 429
    
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
