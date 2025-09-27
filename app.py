from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/submit_user_info', methods=['POST'])
def submit_user_info():
    data = request.get_json()
    name = data.get('name')
    user_class = data.get('class')
    # In a real application, you might want to store this in a database
    return jsonify({
        'status': 'success',
        'name': name,
        'class': user_class
    })

if __name__ == '__main__':
    app.run(debug=True)
