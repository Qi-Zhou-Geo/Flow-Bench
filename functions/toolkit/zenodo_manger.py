from zenodo_client import Zenodo, Creator

# Initialize client
ACCESS_TOKEN = 'your_access_token_here'
zenodo = Zenodo(access_token=ACCESS_TOKEN)

# Create new version from existing record
RECORD_ID = 'your_record_id'  # The published record ID
new_version = zenodo.new_version(RECORD_ID)

# Upload files
new_version.upload_file('data_v2.csv')
new_version.upload_file('readme.txt')

# Update metadata
new_version.metadata = {
    'title': 'My Dataset v2.0',
    'upload_type': 'dataset',
    'description': 'Updated version',
    'creators': [Creator(name='Your Name', affiliation='Your Institution')],
    'version': '2.0.0'
}

# Publish
new_version.publish()
print(f"New DOI: {new_version.doi}")