$(document).ready(function() {
    $('#sentimentForm').on('submit', function(e) {
        e.preventDefault();
        var feedbackText = $('textarea[name="feedback"]').val();
        var actionUrl = $(this).data('action-url');

        $.ajax({
            url: actionUrl,
            method: 'POST',
            data: {
                csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
                feedback: feedbackText
            },
            success: function(response) {
                $('#results').html('');
                if (response.results && response.results.length > 0) {
                    response.results.forEach(function(result) {
                        $('#results').append('<h3>Overall Sentiment: ' + result.sentiment + '</h3>');
                        $('#results').append('<p>Confidence - Positive: ' + result.overall_scores.positive.toFixed(2) + ', Neutral: ' + result.overall_scores.neutral.toFixed(2) + ', Negative: ' + result.overall_scores.negative.toFixed(2) + '</p>');

                        if (result.key_phrases.length > 0) {
                            $('#results').append('<h4>Key Phrases:</h4>');
                            result.key_phrases.forEach(function(phrase) {
                                $('#results').append('<p>' + phrase + '</p>');
                            });
                        }

                        if (result.opinions.length > 0) {
                            result.opinions.forEach(function(opinion) {
                                $('#results').append('<p>Aspect: ' + opinion.target + ' (' + opinion.sentiment + ')</p>');
                                opinion.assessments.forEach(function(assessment) {
                                    $('#results').append('<p style="margin-left: 20px;">- ' + assessment.text + ': ' + assessment.sentiment + ' (Confidence - Positive: ' + assessment.confidence_scores.positive.toFixed(2) + ', Negative: ' + assessment.confidence_scores.negative.toFixed(2) + ')</p>');
                                });
                            });
                        }
                    });
                } else {
                    $('#results').append('<p>No detailed sentiment data available.</p>');
                }
            },
            error: function() {
                $('#results').html('<p>An error occurred while processing your feedback.</p>');
            }
        });
    });
});
