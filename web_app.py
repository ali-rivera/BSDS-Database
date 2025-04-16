#main flask app for uploading datasets

from flask import Flask, request, redirect, render_template, url_for
from werkzeug.utils import secure_filename
import os
import datetime
from dotenv import load_dotenv
from mongoengine import connect
from datasets.models import Dataset
from s3_utils import upload_file_to_s3

#load environment variables
load_dotenv()
#initialize flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'temp_uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

#connect to MongoDB
connect(
    db="mongodb",                    # Your DB name
    username="mongo",               # Your root user
    password="BSDSDATABASE",        # Your root password
    host="localhost",
    port=27017,
    authentication_source="admin"  # Required for root auth!
)

@app.route('/', methods=['GET', 'POST'])
def upload_dataset():
    if request.method == 'POST':
        file = request.files['file']
        name = request.form['name']
        description = request.form['description']
        if file:
            filename = secure_filename(file.filename)
            temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(temp_path)

            # Upload to S3
            s3_key = f"datasets/{filename}"
            file_url = upload_file_to_s3(temp_path, s3_key)

            if file_url:
                dataset = Dataset(
                    name=name,
                    description=description,
                    file_url=file_url,
                    uploaded_at=datetime.datetime.now()
                )
                dataset.save()
                os.remove(temp_path)
                return redirect(url_for('success', url = file_url))
            else:
                return "Upload to S3 Failed", 500
    return render_template('upload.html')

@app.route('/datasets')
def datasets():
    datasets = Dataset.objects.order_by('-uploaded_at')
    return render_template('browse.html', datasets=datasets)

@app.route('/success')
def success():
    url = request.args.get('url')
    return f"""
        <h2> Upload Successful! </h2>
        <a href='/'>Upload another dataset</a> |<a href='/datasets'>View all datasets</a>
    """

if __name__ == '__main__':
    app.run(debug=True)