# Sentiment Analysis Tool

## Overview

The Sentiment Analysis Tool is a web application that analyzes user-provided text to determine its sentiment (positive, neutral, or negative) and highlights key phrases. This tool automates sentiment analysis to save time and improve accuracy, providing a user-friendly interface for easy understanding.

## Features

- **User Input**: Submit text for analysis.
- **Sentiment Analysis**: Uses Azure Text Analytics to determine sentiment and key phrases.
- **Dynamic Display**: Shows sentiment results with corresponding GIFs.
- **Feedback**: Authenticated users can submit feedback about the tool.

### Role-Based Access
- **User**: Submit text and feedback.
- **Manager**: Review feedback.
- **Admin**: Manage feedback and clear history.

## Technologies Used

- **Backend**: Django, Django Channels, Uvicorn
- **Frontend**: HTML, CSS, JavaScript (jQuery, Bootstrap)
- **Database**: SQLite
- **API**: Azure Text Analytics

## Setup Instructions

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/FeedbackAnalysis.git
   cd FeedbackAnalysis
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   Create a `.env` file with the following:
   ```makefile
   DJANGO_SECRET_KEY=your-secret-key
   AZURE_SUBSCRIPTION_KEY=your-subscription-key
   AZURE_SENTIMENT_ENDPOINT=your-endpoint
   DEBUG=False
   ```

5. **Apply migrations**:
   ```bash
   python manage.py migrate
   ```

6. **Collect static files**:
   ```bash
   python manage.py collectstatic
   ```

7. **Run the server**:
   ```bash
   uvicorn FeedbackAnalysisConfig.asgi:application --host 127.0.0.1 --port 8000 --lifespan off
   ```

## Deployment on Azure

1. **Create and configure Azure resources**:
   ```bash
   az group create --name customer_analytic --location westeurope
   az appservice plan create --name MyAppServicePlan --resource-group customer_analytic --sku B1 --is-linux --location westeurope
   az webapp create --resource-group customer_analytic --plan MyAppServicePlan --name MySentimentAnalysisApp --runtime "PYTHON:3.12" --location westeurope
   ```

2. **Set up Continuous Deployment from GitHub**:
   - Use the Deployment Center in Azure Portal.
   - Configure GitHub as the source with your repository and branch.

3. **Set environment variables**:
   - In Azure Portal, go to Configuration under your Web App settings.
   - Add the following:
     - `DJANGO_SECRET_KEY`
     - `AZURE_SUBSCRIPTION_KEY`
     - `AZURE_SENTIMENT_ENDPOINT`
     - `DEBUG`

4. **Set the startup command**:
   ```bash
   gunicorn FeedbackAnalysisConfig.wsgi:application --config gunicorn_config.py
   ```

## Conclusion

The Sentiment Analysis Tool automates text sentiment analysis using Azure Text Analytics, supporting role-based access and real-time updates via WebSockets. This project integrates Django with external APIs for efficient sentiment analysis and feedback management.
