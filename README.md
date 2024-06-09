# Sentiment Analysis Web Application

## Overview
This project is a web application that performs sentiment analysis on user-provided text using the Azure Text Analytics API. The application classifies text into positive, neutral, or negative sentiments and displays the results along with a relevant GIF.

## Features
- **User Input**: Users can input their text for analysis.
- **Sentiment Analysis**: The application uses Azure Text Analytics to determine the sentiment of the text.
- **Dynamic Results Display**: Results are displayed dynamically along with a corresponding GIF based on the sentiment.
- **Feedback Submission**: Authenticated users can submit feedback on the tool, which is stored in the database and can be reviewed and managed by users with appropriate roles (manager/admin).
- **Error Handling**: Robust error handling to manage API errors and user input issues.

## Technologies Used
- **Backend**: Python, Django
- **Frontend**: HTML, CSS, JavaScript (jQuery)
- **API Integration**: Azure Text Analytics
- **Styling**: Bootstrap

## Project Structure
```
FeedbackAnalysis/
│
├── FeedbackAnalysisConfig/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│
├── feedback/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── consumers.py
│   ├── forms.py
│   ├── models.py
│   ├── routing.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   ├── migrations/
│   │   ├── 0001_initial.py
│   │   ├── 0002_feedback.py
│   │   └── __init__.py
│   ├── static/
│   │   ├── css/
│   │   │   └── styles.css
│   │   └── js/
│   │       └── sentiment.js
│   └── templates/
│       └── feedback/
│           ├── approve_feedback.html
│           ├── choice_page.html
│           ├── feedback_list.html
│           ├── form.html
│           ├── registration/
│           │   ├── login.html
│           │   └── register.html
│           ├── reject_feedback.html
│           ├── results.html
│           ├── review_feedback.html
│           ├── set_language.html
│           ├── set_theme.html
│           └── submit_feedback.html
│
├── home/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   └── views.py
│
├── templates/
│   ├── base_generic.html
│   └── home.html
│
├── manage.py
├── db.sqlite3
├── requirements.txt
└── venv/
    ├── Scripts/
    │   └── python.exe (Windows)
    └── bin/
        └── python (macOS/Linux)
```

## Setup Instructions

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/FeedbackAnalysis.git
   cd FeedbackAnalysis
   ```

2. **Create a virtual environment**:
   - **Windows**:
     ```bash
     python -m venv venv
     venv\Scripts\activate
     ```
   - **macOS/Linux**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Azure Text Analytics**:
   - Obtain your Azure subscription key and endpoint from the Azure portal.
   - Create a `.env` file in the project root and add the following:
     ```
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
   python manage.py runserver
   ```

8. **Access the application**:
   - Open your browser and go to `http://127.0.0.1:8000/`.

## Deployment on Azure

### Steps to Deploy on Azure App Services

1. **Create and Configure Azure Resources**

   - **Create a Resource Group**:
     ```bash
     az group create --name customer_analytic --location westeurope
     ```

   - **Create an App Service Plan**:
     ```bash
     az appservice plan create --name MyAppServicePlan --resource-group customer_analytic --sku B1 --is-linux --location westeurope
     ```

   - **Create a Web App**:
     ```bash
     az webapp create --resource-group customer_analytic --plan MyAppServicePlan --name MySentimentAnalysisApp --runtime "PYTHON:3.12" --location westeurope
     ```

2. **Configure Continuous Deployment from GitHub**

   - Navigate to your Web App in the Azure Portal.
   - Go to **Deployment Center**.
   - Set up GitHub as the source and configure it to use your repository and branch.

3. **Configure Environment Variables**

   - Navigate to **Configuration** under your Web App settings in the Azure Portal.
   - Add the following Application settings:
     - `DJANGO_SECRET_KEY`: `your-secret-key`
     - `AZURE_SUBSCRIPTION_KEY`: `71cd915ca08d48218e3479c96690d2e6`
     - `AZURE_SENTIMENT_ENDPOINT`: `https://ca-la.cognitiveservices.azure.com/`
     - `DEBUG`: `False`

4. **Set the Startup Command**

   - In the Azure Portal, under **Configuration**, set the startup command:
     ```bash
     gunicorn FeedbackAnalysisConfig.wsgi:application --config gunicorn_config.py
     ```

5. **Collect Static Files**

   ```bash
   python manage.py collectstatic
   ```

   Commit and push the changes to GitHub:
   ```bash
   git add .
   git commit -m "Collect static files"
   git push origin main
   ```

6. **Monitor and Scale Your Application**

   - Use Azure's monitoring tools to track application performance.
   - Configure auto-scaling rules in the Azure Portal.

## Usage
1. **Navigate to the input form**.
2. **Enter text** for sentiment analysis.
3. **Submit the form** and view the results, including sentiment classification and a corresponding GIF.

## Role-Based Access Control

### Overview
The application includes role-based access control to manage different types of users (Admin, Manager, User). Each role has specific permissions.

### How to Use Role-Based Access

1. **User Registration**:
   - Users can register through the registration form and choose their role (Admin, Manager, User).

2. **Custom User Model**:
   - The application uses a custom user model `CustomUser` with a `role` field to store the user's role.

### Adding New Roles
- The roles can be updated or extended in the `CustomUser` model:
  ```python
  class CustomUser(AbstractUser):
      ROLE_CHOICES = (
          ('admin', 'Admin'),
          ('manager', 'Manager'),
          ('user', 'User'),
          # Add more roles as needed
      )
      role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
  ```

### Enforcing Role-Based Permissions
- Use Django's built-in decorators to enforce role-based access in views. For example:
  ```python
  from django.contrib.auth.decorators import user_passes_test

  def admin_required(user):
      return user.is_authenticated and user.role == 'admin'

  @user_passes_test(admin_required)
  def admin_view(request):
      # View code for admin users
      return render(request, 'admin_template.html')
  ```

## Feedback Submission Feature

### Overview
Authenticated users can submit feedback on the tool, which is stored in the database. This feedback can be reviewed and managed by users with appropriate roles (manager/admin).

### How to Submit Feedback

1. **Navigate to the Submit Feedback Form**:
   - Once logged in, users can access the submit feedback form.

2. **Submit Feedback**:
   - Fill out the feedback form and submit it.

### Reviewing Feedback

1. **Navigate to the Feedback List**:
   - Admin and Manager users can view the list of submitted feedback.

2. **Approve or Reject Feedback**:
   - Admin users can approve or reject the feedback.

### Templates for Feedback

- **Submit Feedback**:
  ```html
  <!DOCTYPE html>
  <html lang="en">
  <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <link href="https://cdn.jsdelivr

.net/npm/bootstrap@5.1.0/dist/css/bootstrap.min.css" rel="stylesheet">
      <title>Submit Feedback</title>
  </head>
  <body>
  <div class="container">
      <h2>Submit Feedback</h2>
      <form method="post" action="{% url 'submit_feedback' %}">
          {% csrf_token %}
          <div class="mb-3">
              <label for="feedback" class="form-label">Feedback</label>
              <textarea name="feedback" class="form-control" id="feedback" rows="5" required></textarea>
          </div>
          <button type="submit" class="btn btn-primary">Submit</button>
      </form>
  </div>
  </body>
  </html>
  ```

## Encountered Issue and Resolution

### Issue Description:
During the development, I encountered a problem with the sentiment classification of certain comments. Specifically, comments that should have been classified as neutral were often misclassified as either negative or positive. This issue was primarily due to the default thresholds used by the pre-trained model, which did not accurately capture the intended neutral sentiment in some borderline cases.

### Analysis:
1. **Initial Testing**: 
   - I tested various comments and observed that neutral comments such as "The product is okay, it meets my expectations but nothing extraordinary." were often classified as negative.
   - Positive and negative comments were generally classified correctly, but there was an inconsistency with comments that should have been neutral.

2. **Threshold Adjustment**:
   - The default threshold settings for sentiment scores provided by the Azure Text Analytics API did not align well with my requirements for neutral sentiment detection.
   - The neutral sentiment was not being properly identified, leading to incorrect classification.

### Solution:
1. **Adjusting Thresholds for Sentiment Classification**:
   - I modified the logic used to determine the overall sentiment based on the confidence scores returned by the Azure Text Analytics API.
   - Specifically, I set a new threshold such that if the neutral score was greater than 0.2, the sentiment would be classified as neutral. This adjustment aimed to better capture comments that did not lean strongly towards either positive or negative sentiment.

2. **Implementation Changes**:
   - I updated the Django view handling the sentiment analysis to incorporate the new threshold logic.
   - The updated logic ensured that comments with a neutral score greater than 0.2 were classified as neutral, improving the accuracy of sentiment classification.

### Results:
After implementing the changes, I tested the sentiment analysis with various comments and observed a significant improvement in the accuracy of neutral sentiment classification. The adjusted thresholds ensured that comments with a more balanced sentiment were correctly identified as neutral, leading to more reliable results.

### Conclusion:
By carefully analyzing the problem and adjusting the sentiment classification thresholds, I was able to resolve the issue and improve the accuracy of the sentiment analysis. This experience underscores the importance of fine-tuning machine learning models and their parameters to align with specific application requirements.

