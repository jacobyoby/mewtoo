"""Multimodal navigation advice: let the agent actually look at the screen.

Version: 0.0.8

Everything else in this agent perceives the game indirectly -- RAM reads,
OCR, and pixel statistics -- and navigates by coordinate heuristics. That
worked until Pallet Town, where the route reached the north fence and had
no way to find the one column that opens onto Route 1: no probe, tile
sweep, or coordinate rule found it (see docs/DEBUG_LOG.md).

A multimodal model can just look. Vision is far too slow to run per step
(~7s per call vs ~1s for a text action), so it runs only when the agent
is genuinely stuck, and answers one narrow question: which way is open.
"""
import base64
import io
import logging
import time

import numpy as np
import ollama
from PIL import Image

logger = logging.getLogger(__name__)

DIRECTIONS = ("UP", "DOWN", "LEFT", "RIGHT")

NAV_PROMPT = """This is a Pokemon Red Game Boy screen. The player sprite is the small
character near the middle of the screen. They are stuck and need to leave this area.

Look at the paths, gaps in fences, doorways, and open ground. Which single direction
should the player walk to make progress out of this area?

Answer with EXACTLY one word: UP, DOWN, LEFT, or RIGHT."""


class VisionAdvisor:
    """Asks a multimodal model which way is open when the agent is stuck."""

    def __init__(self, model: str = "gemma3:4b", scale: int = 3,
                 cooldown_steps: int = 12, timeout: int = 45, metrics=None):
        """Initialize the advisor.

        Args:
            model: Multimodal Ollama model (gemma3 is multimodal; qwen3 is not).
            scale: Upscale factor. The Game Boy screen is 160x144 -- too
                small for reliable vision without upscaling.
            cooldown_steps: Minimum steps between calls; vision is slow.
            timeout: Per-call ceiling in seconds.
            metrics: Optional metrics collector.
        """
        self.model = model
        self.scale = scale
        self.cooldown_steps = cooldown_steps
        self.timeout = timeout
        self.metrics = metrics
        self.client = ollama.Client()
        self.last_call_step: int | None = None
        self.last_direction: str | None = None

    def _encode(self, screen_image: np.ndarray) -> str:
        img = Image.fromarray(np.asarray(screen_image)[:, :, :3].astype("uint8"))
        img = img.resize((img.width * self.scale, img.height * self.scale), Image.NEAREST)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()

    def is_ready(self, step_count: int) -> bool:
        """True when enough steps have passed since the last call."""
        return (self.last_call_step is None
                or step_count - self.last_call_step >= self.cooldown_steps)

    @staticmethod
    def _parse_direction(text: str) -> str | None:
        """Pull a direction out of the model's reply, or None."""
        upper = (text or "").upper()
        # Prefer a standalone word; fall back to any mention
        for token in upper.replace("\n", " ").split():
            cleaned = "".join(c for c in token if c.isalpha())
            if cleaned in DIRECTIONS:
                return cleaned
        for d in DIRECTIONS:
            if d in upper:
                return d
        return None

    def suggest_direction(self, screen_image: np.ndarray, step_count: int) -> str | None:
        """Ask which way is open. Returns a direction, or None on any failure.

        Never raises: vision is an enhancement, and a failed look must not
        take down a run.
        """
        if screen_image is None or not self.is_ready(step_count):
            return None
        self.last_call_step = step_count
        try:
            start = time.time()
            response = self.client.chat(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": NAV_PROMPT,
                    "images": [self._encode(screen_image)],
                }],
                options={"num_predict": 12, "temperature": 0.2},
            )
            text = response["message"]["content"]
            direction = self._parse_direction(text)
            elapsed = time.time() - start
            if direction:
                logger.info(f"[VISION] Step {step_count}: looked at the screen "
                            f"({elapsed:.1f}s) -> go {direction}")
                self.last_direction = direction
            else:
                logger.info(f"[VISION] Step {step_count}: no direction in reply "
                            f"({elapsed:.1f}s): {text.strip()[:60]!r}")
            if self.metrics:
                self.metrics.llm.record_call(elapsed)
            return direction
        except Exception as e:
            logger.warning(f"[VISION] Look failed: {e}")
            return None
