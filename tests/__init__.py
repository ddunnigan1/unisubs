import os

import optionalapps

__path__.extend(os.path.join(p, 'tests')
                for p in optionalapps.get_repository_paths())
