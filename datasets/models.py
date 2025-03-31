from mongoengine import Document, StringField, DateTimeField

# A model of the metadata for each dataset
class Dataset(Document):
    name = StringField(required=True)
    description = StringField()
    file_url = StringField(required=True)  # Link to the actual file stored in S3
    uploaded_at = DateTimeField(default=datetime.datetime.utcnow)