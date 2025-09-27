from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)

@app.route('/')
def dashboard():
    return render_template('dashboard.html', active_page='dashboard')

@app.route('/quizes')
def quizes():
    return render_template('quizes.html', active_page='quizes')

@app.route('/flashcards')
def flashcards():
    return render_template('flashcards.html', active_page='flashcards')

@app.route('/slidedecks')
def slidedecks():
    return render_template('slidedecks.html', active_page='slidedecks')

@app.route('/books')
def books():
    return render_template('books.html', active_page='books')

@app.route('/submit_user_info', methods=['POST'])
def submit_user_info():
    data = request.get_json()
    return jsonify({
        'status': 'success',
        'class': data.get('class'),
        'study_topic': data.get('study_topic'),
        'subjects': data.get('subjects', [])
    })

@app.route('/logout')
def logout():
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)