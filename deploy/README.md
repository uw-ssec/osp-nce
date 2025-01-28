# Deployment Utilities

The bash script in this folder installs software and libraries that the end user will need to run the GRACE streamlit web app. The script:

- installs the correct version of Python, if needed 
- installs the poetry package manager, if needed, and uses it to load the right packages to run the web app
- allows the user to specify environment variables (which they need to connect to databases which the app depends on)
- kills any processes running on the port needed to listen for API calls
- launches the Streamlit application

This script represents a streamlined way to launch the web app without requiring end users to configure the computing environment.