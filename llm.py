"""
LLM wrapper.

ask(prompt, schema, validate) sends one prompt to the model and returns a
dict that (1) is valid JSON matching `schema` and (2) passes `validate`.

If the output is broken or breaks a game rule, the error is sent back to
the model and it tries again (like Agentopia's error-feedback loop).
After `max_retries` failures, it returns None and the caller falls back
to a default action.

MockLLM returns random answers without calling Ollama, so the engine can
be tested quickly.
"""

import json
import random
import time


class OllamaDown(Exception):
    """Ollama could not be reached for a long time: stop the run (progress is saved)."""


def is_connection_error(ex):
    return isinstance(ex, ConnectionError) or "Connect" in type(ex).__name__


class LLM:
    def __init__(self, cfg):
        import ollama  # imported here so mock mode works without ollama installed
        self.model = cfg["llm"]["model"]
        # a timeout so one stuck call can never freeze the whole run
        # talk to Ollama directly on this machine: fixed address, and ignore any proxy/VPN settings
        self.client = ollama.Client(host=cfg["llm"].get("host", "http://127.0.0.1:11434"),
                                    timeout=cfg["llm"].get("timeout_seconds", 240), trust_env=False)
        self.options = {
            "num_ctx": cfg["llm"]["num_ctx"],
            "temperature": cfg["llm"].get("temperature", 0.7),
            # cap the answer length: stops the model from looping forever inside the JSON
            "num_predict": cfg["llm"].get("max_output_tokens", 900),
        }
        if cfg["llm"].get("seed") is not None:   # set per repetition by run.py --run
            self.options["seed"] = cfg["llm"]["seed"]
        self.think = cfg["llm"]["think"]
        self.max_retries = cfg["llm"]["max_retries"]
        self.down_wait = cfg["llm"].get("wait_if_down_minutes", 10)

    def check(self):
        """Fail fast if Ollama is not running."""
        try:
            self.client.list()
        except Exception as ex:
            raise OllamaDown(str(ex))

    def _call(self, prompt, schema):
        """One call. If Ollama is unreachable, wait and retry for a while instead of
        burning through the run with fallback answers; give up with OllamaDown."""
        waited = 0
        while True:
            try:
                return self._call_once(prompt, schema)
            except Exception as ex:
                if not is_connection_error(ex):
                    raise
                if waited >= self.down_wait * 60:
                    raise OllamaDown(str(ex))
                print(f"  ! Cannot reach Ollama ({type(ex).__name__}). Retrying in 30 s "
                      f"(waited {waited // 60} of {self.down_wait} min)...", flush=True)
                time.sleep(30)
                waited += 30

    def _call_once(self, prompt, schema):
        r = self.client.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            format=schema,
            think=self.think,
            options=self.options,
        )
        return r.message.content

    def ask(self, prompt, schema, validate=None):
        """Return (result_dict or None, list_of_error_messages)."""
        errors = []
        feedback = ""
        self.last = None   # last parsed (but possibly invalid) answer, for salvaging
        for _ in range(self.max_retries):
            try:
                raw = self._call(prompt + feedback, schema)
            except OllamaDown:
                raise
            except Exception as ex:  # timeout or Ollama error: count it and try again
                errors.append(f"Call failed: {type(ex).__name__}: {str(ex)[:120]}")
                feedback = "\n\nKeep your answer short."
                continue
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                err = f"Output was not valid JSON: {raw[:200]}"
                errors.append(err)
                feedback = f"\n\nYour previous answer was invalid or too long. Answer again with short, valid JSON."
                continue
            self.last = data
            err = validate(data) if validate else None
            if err is None:
                return data, errors
            errors.append(err)
            feedback = f"\n\nYour previous answer was not allowed: {err} Choose again."
        return None, errors


class MockLLM:
    """Random answers that follow the schema (but may break game rules)."""

    def __init__(self, cfg, seed=0):
        self.rng = random.Random(seed)
        self.max_retries = cfg["llm"]["max_retries"]

    def _fake(self, schema):
        t = schema.get("type")
        if "enum" in schema:
            return self.rng.choice(schema["enum"])
        if t == "object":
            return {k: self._fake(v) for k, v in schema["properties"].items()}
        if t == "array":
            n = self.rng.randint(0, schema.get("maxItems", 2))
            return [self._fake(schema["items"]) for _ in range(n)]
        if t == "boolean":
            return self.rng.random() < 0.5
        if t == "number":
            return self.rng.choice([1, 2, 3])
        if t == "integer":
            return self.rng.randint(schema.get("minimum", 1), schema.get("maximum", 5))
        return "(mock text)"

    def ask(self, prompt, schema, validate=None):
        errors = []
        self.last = None
        for _ in range(self.max_retries):
            data = self._fake(schema)
            self.last = data
            err = validate(data) if validate else None
            if err is None:
                return data, errors
            errors.append(err)
        return None, errors
