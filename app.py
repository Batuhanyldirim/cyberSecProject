from flask import Flask,json
from flask_sqlalchemy import SQLAlchemy
import random
from string import ascii_letters, digits

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

db = SQLAlchemy(app)


class Email(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email  = db.Column(db.String(40))


from flask import request

@app.route('/mail/view')
def view_emails():
    # get page and entries parameters from request
    page = request.args.get('page', default=1, type=int)
    entries = request.args.get('entries', default=20, type=int)

    # query database for emails
    emails = Email.query.paginate(page=page, per_page=entries)

    emailStrings = [item.email for item in emails.items]


    # return emails as JSON response
    return json.jsonify({'emails': emailStrings})


with app.app_context():
    db.create_all()
   
    
    db.session.bulk_insert_mappings(Email, [{'email': ''.join(random.choices(ascii_letters + digits, k=25)) + '@gmail.com'} for _ in range(1000000)])
    db.session.commit()    




if __name__ == '__main__':
    app.run()
