from mongoengine import Document, StringField, DateTimeField
import datetime
import pytz

# A model of the metadata for each dataset
class Dataset(Document):
    name = StringField(required=True)
    description = StringField()
    file_url = StringField(required=True)  # Link to the actual file stored in S3
    uploaded_at = DateTimeField(default=lambda: datetime.datetime.now(pytz.timezone("America/New_York")))