entiment Analysis Tool
Overview
The Sentiment Analysis Tool is a web application that automates the analysis of user-provided text to determine its sentiment (positive, neutral, or negative) and highlights key phrases. The goal is to save time and improve accuracy compared to manual sentiment analysis. The tool provides a user-friendly interface to analyze and visualize text sentiment efficiently.

Application Functionality
General Functionality
User Input: Users can input text for sentiment analysis.
Sentiment Analysis: Uses Azure Text Analytics to determine sentiment and key phrases.
Dynamic Results Display: Displays sentiment analysis results dynamically with corresponding GIFs.
Feedback Submission: Authenticated users can submit feedback about the tool.
Role-Based Functionality
User: Submit text for analysis and provide feedback.
Manager: Review submitted feedback.
Admin: Review, approve, or reject feedback and clear feedback history.
System Diagram
Components
Frontend: HTML, CSS, JavaScript (jQuery, Bootstrap)
Backend: Django, Django Channels
Database: SQLite (development)
API Integration: Azure Text Analytics
Low-Code app: Marblism
Communication
Client-Server: Handled via HTTP requests (REST API) and WebSockets.
Data Format: JSON for data exchange.
Database Connection: SQLite.
Caching: Django's LocMemCache.
Sessions: Managed by Django's session framework.
Queue/Pub-Sub System: WebSockets (Django Channels).
Server-Side Description
Server Functionality
Session Management: Managed using Django's session framework.
Feedback Storage: Stored in SQLite database.
API Requests: Sentiment analysis requests sent to Azure Text Analytics API.
WebSocket Communication: Real-time notifications to the client.
Client Requests
Sentiment Analysis Request: Client sends a POST request with text for analysis.
Feedback Submission: Client sends a POST request to submit feedback.
Technologies Used
Programming Language: Python
Framework: Django
Database: SQLite
Frontend: HTML, CSS, JavaScript (jQuery, Bootstrap)
API: Azure Text Analytics
Server: Uvicorn (ASGI server for Django Channels)
Libraries:
azure-ai-textanalytics
django
channels
decouple
requests
gunicorn
Launch and Deployment Instructions
Setup Instructions
Clone the repository:

bash
Copy code
git clone https://github.com/yourusername/FeedbackAnalysis.git
cd FeedbackAnalysis
Create a virtual environment:

bash
Copy code
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
Install dependencies:

bash
Copy code
pip install -r requirements.txt
Set up Azure Text Analytics:
Create a .env file in the project root and add the following:

makefile
Copy code
DJANGO_SECRET_KEY=your-secret-key
AZURE_SUBSCRIPTION_KEY=your-subscription-key
AZURE_SENTIMENT_ENDPOINT=your-endpoint
DEBUG=False
Apply migrations:

bash
Copy code
python manage.py migrate
Collect static files:

bash
Copy code
python manage.py collectstatic
Run the server:

bash
Copy code
uvicorn FeedbackAnalysisConfig.asgi:application --host 127.0.0.1 --port 8000 --lifespan off
Deployment on Azure
Create and Configure Azure Resources:

bash
Copy code
az group create --name customer_analytic --location westeurope
az appservice plan create --name MyAppServicePlan --resource-group customer_analytic --sku B1 --is-linux --location westeurope
az webapp create --resource-group customer_analytic --plan MyAppServicePlan --name MySentimentAnalysisApp --runtime "PYTHON:3.12" --location westeurope
Configure Continuous Deployment from GitHub:

Navigate to your Web App in the Azure Portal.
Go to Deployment Center.
Set up GitHub as the source and configure it to use your repository and branch.
Configure Environment Variables:

Navigate to Configuration under your Web App settings in the Azure Portal.
Add the following Application settings:
DJANGO_SECRET_KEY: your-secret-key
AZURE_SUBSCRIPTION_KEY: your-subscription-key
AZURE_SENTIMENT_ENDPOINT: your-endpoint
DEBUG: False
Set the Startup Command:

bash
Copy code
gunicorn FeedbackAnalysisConfig.wsgi:application --config gunicorn_config.py
Conclusion
Issues Encountered
Sentiment Classification: Initial thresholds for sentiment classification led to misclassification.
Solution: Adjusted the sentiment classification thresholds to improve accuracy.
Summary
The Sentiment Analysis Tool successfully automates text sentiment analysis using Azure Text Analytics. It supports role-based access control and allows users to submit feedback, which can be reviewed and managed by admins. This project demonstrates the integration of Django with external APIs and the use of WebSockets for real-time updates.

Documentation
For detailed information, please refer to the Azure DevOps documentation and Django documentation.
