import os
import datetime  # Import datetime to get timestamps
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename

# --- Flask Configuration ---
app = Flask(__name__)
app.secret_key = "your_strong_secret_key_here_for_flash_messages"  # CHANGE THIS!

# Directory where the single current movie will be stored
app.config['CURRENT_MOVIE_FOLDER'] = 'static/current_movie'
# The fixed filename for the currently playing movie
CURRENT_MOVIE_FILENAME = 'current_movie.mp4'
# The companion file to store the upload timestamp
TIMESTAMP_FILENAME = 'current_movie_upload_time.txt'

app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'avi', 'mov', 'mkv', 'webm'}
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # Max upload size: 500 MB

# Ensure the designated movie folder exists
os.makedirs(app.config['CURRENT_MOVIE_FOLDER'], exist_ok=True)


# Helper function to check if the file extension is allowed
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


# --- Flask Routes ---

# The root route now handles POST requests for uploads, and redirects GET requests.
@app.route('/', methods=['GET', 'POST'])
def handle_upload_and_redirect():
    if request.method == 'POST':
        # This part handles uploads coming from send_movie.py or other POST requests
        if 'movie_file' not in request.files:
            flash('No file part', 'error')
            return redirect(url_for('now_playing'))  # Redirect to playing page

        file = request.files['movie_file']

        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(url_for('now_playing'))

        if file and allowed_file(file.filename):
            target_filepath = os.path.join(app.config['CURRENT_MOVIE_FOLDER'], CURRENT_MOVIE_FILENAME)
            timestamp_filepath = os.path.join(app.config['CURRENT_MOVIE_FOLDER'], TIMESTAMP_FILENAME)

            try:
                file.save(target_filepath)  # This will overwrite the existing file

                # Save the current timestamp
                upload_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(timestamp_filepath, 'w') as ts_file:
                    ts_file.write(upload_time)

                flash(f'Movie "{secure_filename(file.filename)}" uploaded and is now playing!', 'success')
                return redirect(url_for('now_playing'))
            except Exception as e:
                flash(f'Error saving movie: {e}', 'error')
                app.logger.error(f"Error saving movie {secure_filename(file.filename)}: {e}")
                return redirect(url_for('now_playing'))
        else:
            flash(f'Invalid file type. Allowed: {", ".join(app.config["ALLOWED_EXTENSIONS"])}', 'error')
            return redirect(url_for('now_playing'))

    # For GET requests to '/', just redirect to the now_playing page
    return redirect(url_for('now_playing'))


# The main route for playing the current movie
@app.route('/now_playing')
def now_playing():
    movie_path_on_server = os.path.join(app.config['CURRENT_MOVIE_FOLDER'], CURRENT_MOVIE_FILENAME)
    upload_timestamp = None

    if os.path.exists(movie_path_on_server):
        # Construct the URL for the current movie file
        movie_url = url_for('static', filename=f'current_movie/{CURRENT_MOVIE_FILENAME}')

        # Try to read the upload timestamp
        timestamp_filepath = os.path.join(app.config['CURRENT_MOVIE_FOLDER'], TIMESTAMP_FILENAME)
        if os.path.exists(timestamp_filepath):
            try:
                with open(timestamp_filepath, 'r') as ts_file:
                    upload_timestamp = ts_file.read().strip()
            except Exception as e:
                app.logger.error(f"Error reading timestamp file: {e}")
                upload_timestamp = "Unknown (error reading timestamp)"
        else:
            upload_timestamp = "Unknown (file not found)"

        return render_template('now_playing.html', movie_url=movie_url, movie_exists=True,
                               upload_timestamp=upload_timestamp)
    else:
        # No movie has been uploaded yet
        flash('No movie loaded yet. Please upload one using the script!', 'info')
        return render_template('now_playing.html', movie_exists=False)


# --- Main entry point to run the Flask app ---
#if __name__ == '__main__':
#    app.run(debug=True)