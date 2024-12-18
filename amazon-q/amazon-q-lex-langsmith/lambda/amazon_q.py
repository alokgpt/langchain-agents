from typing import Any, AsyncGenerator, Dict, Iterator, List, Optional
from langchain_core.callbacks.manager import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun
)
from langchain_core.outputs import GenerationChunk
from langchain_core.language_models import LLM
from pydantic import ConfigDict
import json
import asyncio
import boto3
from tvm_client import TVMClient

class AmazonQ(LLM):
    """Amazon Q LLM wrapper.

    To authenticate, the AWS client uses the following methods to
    automatically load credentials:
    https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html

    Make sure the credentials / roles used have the required policies to
    access the Amazon Q service.
    """
    
    region_name: Optional[str] = None
    """AWS region name. If not provided, will be extracted from environment."""
    
    streaming: bool = False
    """Whether to stream the results or not."""
    
    client: Any = None
    """Amazon Q client."""

    application_id: str = None
    """Amazon Q client."""

    _last_response: Dict = None  # Add this to store the full response
    """Store the full response from Amazon Q."""

    parent_message_id: Optional[str] = None
    """AWS region name. If not provided, will be extracted from environment."""

    conversation_id: Optional[str] = None
    """AWS region name. If not provided, will be extracted from environment."""

    chat_mode: str = "RETRIEVAL_MODE"
    """AWS region name. If not provided, will be extracted from environment."""

    model_config = ConfigDict(
        extra="forbid",
    )

    @property
    def _llm_type(self) -> str:
        """Return type of llm."""
        return "amazon_q"

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the Amazon Q client."""
        super().__init__(**kwargs)

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Call out to Amazon Q service.

        Args:
            prompt: The prompt to pass into the model.
            stop: Optional list of stop words to use when generating.

        Returns:
            The string generated by the model.

        Example:
            .. code-block:: python

                response = llm.invoke("Tell me a joke.")
        """
        try:
            print("Prompt Length (Amazon Q ChatSync API takes a maximum of 7000 chars)")
            print(len(prompt))

            # Prepare the request
            request = {
                'applicationId': "130f4ea4-855f-4ddf-b2a5-1e40923692d4",
                'userMessage': prompt,
                'chatMode':self.chat_mode,
            }
            if not self.conversation_id:
                request = {
                    'applicationId': self.application_id,
                    'userMessage': prompt,
                    'chatMode':self.chat_mode,
                }
            else:
                request = {
                    'applicationId': self.application_id,
                    'userMessage': prompt,
                    'chatMode':self.chat_mode,
                    'conversationId':self.conversation_id,
                    'parentMessageId':self.parent_message_id,
                }
            
            # Call Amazon Q
            response = self.client.chat_sync(**request)
            self._last_response = response

            # Extract the response text
            if 'systemMessage' in response:
                return response["systemMessage"]
            else:
                raise ValueError("Unexpected response format from Amazon Q")

        except Exception as e:
            raise ValueError(f"Error raised by Amazon Q service: {e}")

    def get_last_response(self) -> Dict:
        """Method to access the full response from the last call"""
        return self._last_response

    async def _acall(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Async call to Amazon Q service."""
        
        def _execute_call():
            return self._call(prompt, stop=stop, **kwargs)

        # Run the synchronous call in a thread pool
        return await asyncio.get_running_loop().run_in_executor(
            None, _execute_call
        )

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Get the identifying parameters."""
        return {
            "region_name": self.region_name,
        }