from voluptuous import Required, Schema, Any, All, Range

schema = Schema ({
    Required('version'): '0.1',
    'system': [{'name': str,
        'id': int,
        'location': [{'name': str,
            'type': Any('star', 'planet'),
            'id': All(int
            }]
        }],
    #'cargo': list,
    #'equipment': list,
    #'property': list,
    #'ship': list,
    })
