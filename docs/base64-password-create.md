# Base64 password create

Use one of the two options of how to create a base64 password provided below:

_Python3 interactive shell_
```python
from autoscaler.core.helpers import string_to_base64string
string_to_base64string("your-app-password-here")
```

_Shell_
```bash
echo -n $BITBUCKET_APP_PASSWORD | base64
```