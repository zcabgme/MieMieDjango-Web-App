# UCL5 MieMie - Django Web Application
UCL5 MieMie is an NLP and data mining web scraping engine to be used across UCL.

## Brief Introduction
The following repository contains a Django web application for visualising [UCL5 MieMie](https://github.com/UCLComputerScience/COMP0016_2020_21_Team16.git) data.

## Project Website
The [website](http://www.albert-mukhametov.info/web3/index.html) gives a greater overview of the challenges and design decisions that were made, implementation using the Python programming language and research undertaken.
## Using the Engine
To view and interact with the data, navitage to the following [link](https://miemiedjangoapp.azurewebsites.net). If you would like to run the application locally and commit changes, please follow the instructions below.
## Getting Started
These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Clone the Repository
Create a folder for this project, open a Terminal / Command Prompt at that folder and run the following commmand:
```
git clone https://github.com/thatguy1104/MieMieDjango-Web-App.git

cd MieMieDjango-Web-App
```

### Create Python Virtual Environment
```
python3 -m venv venv
```

### Activate Python Virtual Environment
```
source venv/bin/activate
```

You should see (venv) at the start of the terminal string (which ends in a $)
### Prerequisites
Installation of libraries required:
```
pip3 install -r requirements.txt
```

## Running the Server
Ensure that you are in the project directory and run the following command:
```
python manage.py runserver
```

## License
This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details