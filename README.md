# Scheduling-Demo

This project consists of an application with features to support the booking of tennis court for a tennis club.

In the file 'docs.txt', detailed information about all the features of the platform and future plans can be found, as well as how to run the app.

## Highlights of the Project:
- ### Internal functional programming structure
- ### Database schema design and implementation using a RDBMS [PostgreSQL], as well as CRUD operations based on user actions
- ### Login functionality, as well as admin credentials used to access hidden content
- ### Email system implemented with AWS Lambda to notify admins and users of bookings
- ### Form validations to prevent invalid user input
- ### Implementation of SASS for easier styling of the platform

## Project Structure - Folders
- ### helpers 
  - this folder consists of functions and variables used multiple times in the app. 
    - The creation of this folder results in a better organized environment, which in turn allows for a more consistent and efficient coding implementation in the development of the platform
    - The 'funcs' folder consists of the internal functional programming structure which serves as the backbone of the platform's back-end
- ### lambdafuncs
  - this folder consists of the functionality implemented in AWS Lambda, an automated scheduled email system to notify admins and users of court bookings
    - admins receive a table with all the bookings for the day at 8 am
    - every one hour of the operating hours of the club for the day, users with a court booked for the next hour are notified of the booking through email
- ### static
  - this folder consists of the CSS and SASS styling of the platform's pages
- ### templates
  - this folder consists of the html files for the different pages of the platform
- ### Single files
  - app.py --> consists of the main app
  - docs.txt --> detailed information about the app (specific features, future plans, how to run the app, resources used)
  - schema.txt --> database schema used in the PostgreSQL RDBMS used in the platform 


