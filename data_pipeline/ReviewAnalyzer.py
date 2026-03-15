import anthropic
import json
from typing import List, Dict

class ClaudeReviewSummarizer:
    """
    Generate review summaries using Claude API
    """

    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    def generate_summary(self, reviews: List[str], product_name: str = "Product") -> Dict:
        """
        Generate comprehensive review summary using Claude

        Args:
            reviews: List of review texts
            product_name: Name of the product being reviewed

        Returns:
            Dictionary with summary insights
        """
        # Prepare reviews for Claude
        review_context = "\n\n".join([
            f"Review {i+1}: {review}"
            for i, review in enumerate(reviews[:100])  # Limit to 100 reviews
        ])

        prompt = f"""Analyze these customer reviews for {product_name} and provide a comprehensive summary.

Reviews:
{review_context}

Provide a JSON response with the following structure:
{{
  "overall_sentiment": "positive/mixed/negative/neutral",
  "summary": "2-3 sentence overview of customer feedback",
  "aspect_ratings": {{
    "taste": 0.0-1.0,
    "quality": 0.0-1.0,
    "price": 0.0-1.0,
    "packaging": 0.0-1.0
  }}
}}

Important:
- aspect_ratings should be 0.0 to 1.0 where 1.0 is very positive, 0.0 is very negative
- Only include aspects that are actually mentioned in reviews
- Base ratings on actual customer sentiment, not just mentions
- For example, "price is too high" should give price a LOW score
"""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Parse JSON response
            response_text = message.content[0].text

            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text.strip()

            summary = json.loads(json_str)

            return summary

        except Exception as e:
            print(f"Error generating summary: {e}")
            return {
                "error": str(e),
                "overall_sentiment": "",
                "summary": ""
            }

    def generate_comparative_summary(self, platform_reviews: Dict[str, List[str]]) -> Dict:
        """
        Compare reviews across multiple platforms

        Args:
            platform_reviews: {"Amazon": [reviews], "Flipkart": [reviews]}

        Returns:
            Comparative analysis
        """
        # Prepare platform-wise review context
        platform_context = []
        for platform, reviews in platform_reviews.items():
            platform_context.append(f"\n{platform} Reviews:")
            platform_context.append("\n".join([f"- {r}" for r in reviews[:20]]))

        context = "\n".join(platform_context)

        prompt = f"""Compare customer reviews across different e-commerce platforms:

{context}

Provide a JSON response with:
{{
  "platform_comparison": {{
    "Amazon": {{
      "sentiment": "positive/mixed/negative",
      "avg_rating_estimate": 0.0-1.0,
      "unique_insights": ["insight 1", "insight 2"]
    }},
    "Flipkart": {{
      "sentiment": "positive/mixed/negative",
      "avg_rating_estimate": 0.0-1.0,
      "unique_insights": ["insight 1", "insight 2"]
    }}
  }},
  "overall_consensus": "What do customers agree on across platforms",
  "platform_differences": "Key differences in customer feedback by platform",
  "best_platform_to_buy": "Recommendation with reason"
}}
"""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text

            # Extract JSON
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            else:
                json_str = response_text.strip()

            return json.loads(json_str)

        except Exception as e:
            return {"error": str(e)}