import sqlite3

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort
from datetime import datetime
import logging

# Count all database connections
connection_count = 0

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    global connection_count
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    connection_count += 1
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      log_msg('Article with id "{id}" does not exist!'.format(id=post_id))
      return render_template('404.html'), 404
    else:
      log_msg('Article "{title}" successfully retrieved!'.format(title=post['title']))
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    log_msg('About page retrieve success!')
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            log_msg('New article "{title}" created!'.format(title=title))

            return redirect(url_for('index'))

    return render_template('create.html')


# Define healthz endpoint
@app.route("/healthz")
def healthz():

    connection = get_db_connection()
    connection.cursor()
    connection.execute("SELECT * FROM posts")
    connection.close()
    
    data = {"HTTP": 200, "result": "Ok - healthy"}
    return data


# Define metrics endpoint
@app.route("/metrics")
def metrics():
    try:
        connection = get_db_connection()
        posts = connection.execute("SELECT * FROM posts").fetchall()
        connection.close()
        posts_count = len(posts)
        
        http_code= 200
        resp = {"db_connection_count": connection_count, "post_count": posts_count}
        data = {"HTTP": http_code, "responce": resp}
        return data
    except Exception:
        
        http_code= 500
        return {"result": "ERROR - Metrics"}, http_code


# Log message function
def log_msg(msg):
    app.logger.info('{time} | {message}'.format( time=datetime.now().strftime("%d/%m/%Y, %H:%M:%S"), message=msg))
    
# start the application on port 3111
if __name__ == "__main__":
    ## stream logs to a file
    logging.basicConfig(level=logging.DEBUG)

    app.run(host='0.0.0.0', port='3111')
