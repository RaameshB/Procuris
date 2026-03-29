# YHack

## WebApp Structure
The webapp functionality of this app is split between the frontend and backend

### backend
The backend directory contains all of the files important to our Flask API. The routes folder contains the routes used to access the api data. vendors.py is the most important of these route files, as it transfers the vendor data. Some of the folders such as db, services, and utils are not currently used and will be used for future features.

### frontend
The frontend directory contains everything related to the frontend server. The frontend is built with React. Outside of the src folder is various configuration files. Within the src folder is the various components, styles, and api fetch statements used to communicate with our api.
