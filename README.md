# LogIT - Smartest way to track your expenses
#### Video Demo: https://youtu.be/OVKDnrSkBmE
#### Description:
LogIT is a simple and powerfull tool to log and track your expenses. It contains features such as recording your expenses and
tracking them using tables and charts which are going to be explained and descibed further.

This project was made using HTML, CSS (Bootstrap), JavaScript, Python with Flask and Jinja, and SQL.

Register page allows to register new user by inputing full name (which is going to be separated to first and last name),
unique email adress and username, and 8-character long password. If all of the criteria above is met, then user is successfully
added to the database.

Login page allows user to log in and has link to "Forgot password" and "Register" page. If login and password match query from
the database, then user will be successfully logged in.

Password recovery page was probably one of the most interesting pages to make. Firstly, it gets email from the user, then it checks
if this email is in the database, if it is in the database it sends an email from "LogIT support email" with some text and link to
the new password page. How it works is another interesting topic. When email is sent, it attaches email and key to link as parameter (...?email='email'&key='key')
and when new password page is loaded, it knows which user's password has to be changed, it checks if key in link is equal to key generated,
to prevent another user just change someones email. If new password and confirmation are the same, user has successfully changed the password.

Home page contains 4 elements - pie chart with % of all spendings from each category (if there is an expense in particullar category),
cards with how much was spend in each category, add an expense button and history table which gets user's last 10 expenses. The page layout
depends on width of the page. I also debated on what colors should web-application use and came up with those what are now. I think it's
really colorful color palette. Each expense category has a different color.

Add an expense page contains a simple form, which contains 4 fields - category, name of the expense, price and date. In total you can choose
from 9 different categories. Currency of the price field can be changed (see in account page). You can't put negative and has to be a number.

Statistics page contains two graphs - pie chart, which contains % of all categories, and bar chart, which contains 5 most expensive items in
user's history.

History page shows history table, which can be sorted in multiple ways - by collunm name, in example, by name, category, price or date, or
searched by - specific name, category, price or date. The record can also be deleted. Each category is shown in different color style,
according to category color.

Account page has 2 forms - to change user information (name, surname, email, username, currency) and password. User can change email and
username to email and username which are not already taken. User can pick from 3 different currencies - Euro, US Dollar and Great British Pound.
In order to change password user has to provide the old password, new one and confirmation.
