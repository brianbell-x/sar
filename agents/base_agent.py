import json
from typing import Any, Dict

class BaseAgent:
    def __init__(self, client):
        """Initialize BaseAgent.

        Args:
            client: OpenAI client instance.
            model: Model identifier.
        """
        self.client = client
        self.model = "o3-mini-2025-01-31"
        self.system_prompt = ""
        self.json_schema = {}

    def run(self, input_data: Any) -> Dict[str, Any]:
        """Process input data and return API response.

        Args:
            input_data: Input as a string or dictionary.

        Returns:
            API response as JSON.
        """
        # Convert input_data to appropriate format and call API
        formatted_input = self._format_input(input_data)
        response = self._call_api(formatted_input)
        return self._parse_response(response)

    def _format_input(self, input_data: Any):
        """Format the input data for the Responses API.
        
        Args:
            input_data: Input as a string or dictionary.
            
        Returns:
            User content formatted as a string for the Responses API.
        """
        # Prepare user content
        user_content = input_data
        if isinstance(user_content, dict):
            user_content = json.dumps(user_content)
            
        return user_content

    def _call_api(self, user_content):
        """Call the Responses API directly.
        
        Args:
            user_content: Formatted user content for the Responses API.
            
        Returns:
            Raw response from the API.
        """
        # Standardize the user content to string format
        user_content_str = str(user_content)
        
        # Ensure JSON format is requested
        # This is the centralized place for this check to avoid duplication
        if "json" not in user_content_str.lower():
            user_content_str = f"{user_content_str}\nPlease provide the response in JSON format."
            
        # Centralized API call with standardized parameters
        response = self.client.responses.create(
            model=self.model,
            instructions=self.system_prompt,  # System prompt goes in instructions
            input=user_content_str,           # User content goes in input
            text={"format": {"type": "json_object"}},
            reasoning={"effort": "high"},     # Use high reasoning effort for better quality
            tools=[],                         # No external tools needed
            store=True                        # Store for later reference if needed
        )
        return response

    def _parse_response(self, response):
        """Extract and parse the response content."""
        # 1) Validate status
        if response.status != "completed":
            if response.error:
                raise Exception(f"API Error: {response.error}")
            elif response.incomplete_details:
                raise Exception(f"Incomplete response: {response.incomplete_details}")
            else:
                raise Exception(f"Response status: {response.status}")

        # 2) Safety check: does output exist?
        if not response.output or len(response.output) == 0:
            raise Exception("No output items returned from the API")

        # 3) Loop through each item in output, find the one with type='message'
        for item in response.output:
            # We only want items that are "type": "message" (assistant output)
            if hasattr(item, 'type') and item.type == "message":
                # Now parse the message content
                if hasattr(item, 'content') and item.content and len(item.content) > 0:
                    content_block = item.content[0]
                    if hasattr(content_block, 'text'):
                        raw_text = content_block.text
                        # Optionally parse as JSON
                        try:
                            return json.loads(raw_text)
                        except json.JSONDecodeError:
                            return raw_text

        # 4) If we exit loop with no "message" found, raise an error
        raise Exception("No message-type output items found in response")
