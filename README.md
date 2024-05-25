

# Sentiment Analysis Web Application

## Overview
This project is a web application that performs sentiment analysis on user-provided text using the Azure Text Analytics API. The application classifies text into positive, neutral, or negative sentiments and displays the results along with a relevant GIF.

## Features
- **User Input**: Users can input their text for analysis.
- **Sentiment Analysis**: The application uses Azure Text Analytics to determine the sentiment of the text.
- **Dynamic Results Display**: Results are displayed dynamically along with a corresponding GIF based on the sentiment.
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
│   ├── models.py
│   ├── tests.py
│   ├── views.py
│   └── templates/
│       └── feedback/
│           ├── form.html
│           └── results.html
│   └── static/
│       ├── css/
│       │   └── styles.css
│       └── js/
│           └── sentiment.js
│
├── templates/
│   └── home.html
│
├── manage.py
├── db.sqlite3
├── venv/
│   ├── Scripts/
│   │   └── python.exe (Windows)
│   └── bin/
│       └── python (macOS/Linux)
└── requirements.txt
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
   - Add these to your Django settings in `FeedbackAnalysisConfig/settings.py`:
     ```python
     AZURE_SUBSCRIPTION_KEY = 'your_subscription_key'
     AZURE_SENTIMENT_ENDPOINT = 'your_endpoint'
     ```

5. **Apply migrations**:
   ```bash
   python manage.py migrate
   ```

6. **Run the server**:
   ```bash
   python manage.py runserver
   ```

7. **Access the application**:
   - Open your browser and go to `http://127.0.0.1:8000/`.

## Usage
1. **Navigate to the input form**.
2. **Enter text** for sentiment analysis.
3. **Submit the form** and view the results, including sentiment classification and a corresponding GIF.

## Encountered Issue and Resolution

### Issue Description:
During the development, we encountered a problem with the sentiment classification of certain comments. Specifically, comments that should have been classified as neutral were often misclassified as either negative or positive. This issue was primarily due to the default thresholds used by the pre-trained model, which did not accurately capture the intended neutral sentiment in some borderline cases.

### Analysis:
1. **Initial Testing**: 
   - We tested various comments and observed that neutral comments such as "The product is okay, it meets my expectations but nothing extraordinary." were often classified as negative.
   - Positive and negative comments were generally classified correctly, but there was an inconsistency with comments that should have been neutral.

2. **Threshold Adjustment**:
   - The default threshold settings for sentiment scores provided by the Azure Text Analytics API did not align well with our requirements for neutral sentiment detection.
   - The neutral sentiment was not being properly identified, leading to incorrect classification.

### Solution:
1. **Adjusting Thresholds for Sentiment Classification**:
   - We modified the logic used to determine the overall sentiment based on the confidence scores returned by the Azure Text Analytics API.
   - Specifically, we set a new threshold such that if the neutral score was greater than 0.2, the sentiment would be classified as neutral. This adjustment aimed to better capture comments that did not lean strongly towards either positive or negative sentiment.

2. **Implementation Changes**:
   - Updated the Django view handling the sentiment analysis to incorporate the new threshold logic.
   - The updated logic ensured that comments with a neutral score greater than 0.2 were classified as neutral, improving the accuracy of sentiment classification.

### Results:
After implementing the changes, we tested the sentiment analysis with various comments and observed a significant improvement in the accuracy of neutral sentiment classification. The adjusted thresholds ensured that comments with a more balanced sentiment were correctly identified as neutral, leading to more reliable results.

### Conclusion:
By carefully analyzing the problem and adjusting the sentiment classification thresholds, we were able to resolve the issue and improve the accuracy of our sentiment analysis. This experience underscores the importance of fine-tuning machine learning models and their parameters to align with specific application requirements.

## License
[MIT](LICENSE)
```

Feel free to modify any part of this README file to better fit your project specifics. Let me know if you need any further assistance! 😊
```
