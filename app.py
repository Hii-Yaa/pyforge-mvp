from flask import Flask, render_template, request, redirect, url_for
from config import Config
from models import db, Item

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    items = Item.query.order_by(Item.created_at.desc()).all()
    return render_template('index.html', items=items)

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')

        if title:
            new_item = Item(title=title, description=description)
            db.session.add(new_item)
            db.session.commit()
            return redirect(url_for('index'))

    return render_template('create.html')

@app.route('/detail/<int:item_id>')
def detail(item_id):
    item = Item.query.get_or_404(item_id)
    return render_template('detail.html', item=item)

@app.route('/delete/<int:item_id>', methods=['POST'])
def delete(item_id):
    item = Item.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
