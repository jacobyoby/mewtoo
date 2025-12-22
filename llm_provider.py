"""LLM Provider abstraction for Mewtwo."""
import time
from abc import ABC, abstractmethod
from typing import Optional
import anthropic
import ollama
import threading


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 10) -> str:
        """Generate a response from the LLM.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            max_tokens: Maximum tokens to generate (default: 10 for faster responses)
        """
        pass


class OllamaProvider(LLMProvider):
    """Ollama provider for local LLM inference."""
    
    def __init__(self, model: str = "llama3.2", metrics=None):
        """Initialize Ollama provider.
        
        Args:
            model: Model name to use (default: llama3.2)
            metrics: Optional metrics collector instance
        """
        self.model = model
        self.client = ollama.Client()
        self.metrics = metrics
        
        # Validate model exists
        try:
            available_models = self._list_available_models()
            if model not in available_models:
                # Check if there's a model with the same base name (before colon)
                model_base = model.split(':')[0] if ':' in model else model
                matching_models = [m for m in available_models if m.startswith(model_base + ':') or m == model_base]
                
                if matching_models:
                    suggested = matching_models[0]
                    print(f"Warning: Model '{model}' not found in Ollama.")
                    print(f"Available models: {', '.join(available_models)}")
                    print(f"Using '{suggested}' instead.")
                    self.model = suggested
                elif available_models:
                    suggested = available_models[0]
                    print(f"Warning: Model '{model}' not found in Ollama.")
                    print(f"Available models: {', '.join(available_models)}")
                    print(f"Using '{suggested}' instead.")
                    self.model = suggested
                else:
                    raise ValueError(
                        f"Model '{model}' not found and no models available. "
                        f"Install a model with: ollama pull llama3.2"
                    )
        except Exception as e:
            # If we can't check, warn but continue (might work anyway)
            if isinstance(e, ValueError):
                raise
            print(f"Warning: Could not verify model availability: {e}")
    
    def _call_with_timeout(self, func, timeout=30):
        """Call a function with timeout protection."""
        result = [None]
        exception = [None]
        
        def target():
            try:
                result[0] = func()
            except Exception as e:
                exception[0] = e
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout)
        
        if thread.is_alive():
            raise TimeoutError(f"Function call timed out after {timeout} seconds")
        
        if exception[0]:
            raise exception[0]
        
        return result[0]
    
    def _list_available_models(self) -> list[str]:
        """List available Ollama models."""
        try:
            response = self.client.list()
            if hasattr(response, 'models'):
                return [m.model for m in response.models]
            elif isinstance(response, dict) and 'models' in response:
                return [m.get('model', m.get('name', '')) for m in response['models']]
            else:
                return []
        except Exception:
            return []
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 10) -> str:
        """Generate a response using Ollama.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            max_tokens: Maximum tokens to generate (default: 10 for faster responses)
        
        Raises:
            ValueError: If model is not found or other error occurs
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Use options to limit tokens for faster responses
        options = {
            "num_predict": max_tokens,  # Limit prediction length
            "temperature": 0.1,  # Lower temperature for more deterministic responses
        }
        
        start_time = time.time()
        try:
            # Add timeout protection (30 seconds max)
            response = self._call_with_timeout(
                lambda: self.client.chat(
                    model=self.model,
                    messages=messages,
                    options=options
                ),
                timeout=30
            )
            latency = time.time() - start_time
            
            # Extract token count if available
            tokens = None
            if isinstance(response, dict):
                # Ollama may include token counts in response
                if "eval_count" in response:
                    tokens = response.get("eval_count")
                elif "prompt_eval_count" in response and "eval_count" in response:
                    tokens = response.get("prompt_eval_count", 0) + response.get("eval_count", 0)
            
            # Record metrics
            if self.metrics:
                self.metrics.llm.record_call(latency, tokens=tokens)
            
            return response["message"]["content"]
        except TimeoutError:
            latency = time.time() - start_time
            if self.metrics:
                self.metrics.llm.record_call(latency, timeout=True)
            raise ValueError(f"LLM call timed out after 30 seconds. Model: {self.model}")
        except Exception as e:
            latency = time.time() - start_time
            if self.metrics:
                self.metrics.llm.record_call(latency, error=True)
            error_msg = str(e)
            if "not found" in error_msg.lower() or "404" in error_msg:
                available_models = self._list_available_models()
                raise ValueError(
                    f"Model '{self.model}' not found in Ollama.\n"
                    f"Available models: {', '.join(available_models) if available_models else 'None'}\n"
                    f"Install a model with: ollama pull llama3.2"
                ) from e
            raise


class ClaudeProvider(LLMProvider):
    """Anthropic Claude provider for cloud-based inference."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022", metrics=None):
        """Initialize Claude provider.
        
        Args:
            api_key: Anthropic API key (if None, reads from environment)
            model: Model name to use
            metrics: Optional metrics collector instance
        """
        self.api_key = api_key
        self.model = model
        self.client = anthropic.Anthropic(api_key=api_key)
        self.metrics = metrics
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 10) -> str:
        """Generate a response using Claude.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            max_tokens: Maximum tokens to generate (default: 10 for faster responses)
        """
        start_time = time.time()
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,  # Reduced from 4096 for faster responses
                system=system_prompt or "",
                messages=[{"role": "user", "content": prompt}]
            )
            latency = time.time() - start_time
            
            # Extract token count from Claude response
            tokens = None
            if hasattr(response, 'usage'):
                usage = response.usage
                if hasattr(usage, 'input_tokens') and hasattr(usage, 'output_tokens'):
                    tokens = usage.input_tokens + usage.output_tokens
            
            # Record metrics
            if self.metrics:
                self.metrics.llm.record_call(latency, tokens=tokens)
            
            return response.content[0].text
        except Exception as e:
            latency = time.time() - start_time
            if self.metrics:
                self.metrics.llm.record_call(latency, error=True)
            raise

