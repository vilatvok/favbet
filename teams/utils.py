

def get_upload_path(instance, filename):
    class_name = instance.__class__.__name__
    match class_name:
        case 'Team':
            folder = 'teams'
        case 'Competition':
            folder = 'competitions'
        case 'Country':
            folder = 'countries'
    return folder + '/' + filename
