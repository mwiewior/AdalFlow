from typing import Dict, Any, List, Optional, Union
import os
import logging


from dataclasses import dataclass, field
from datetime import datetime
import json

from core.generator import Generator
from core.data_classes import BaseDataClass
from utils import serialize


log = logging.getLogger(__name__)


@dataclass
class GeneratorStatesRecord(BaseDataClass):
    prompt_states: Dict[str, Any] = field(default_factory=dict)
    time_stamp: str = field(default_factory=str)

    def __eq__(self, other: Any):
        if not isinstance(other, GeneratorStatesRecord):
            return NotImplemented
        return serialize(self.prompt_states) == serialize(other.prompt_states)


class GeneratorStatesLogger:
    __doc__ = r"""Log the generator states especially the prompt states update history to a file.

    Each generator should has its unique and identifiable name to be logged.
    One file can log multiple generators' states.

    We use _trace_map to store the states and track any changes and updates and save it to a file.

    Args:
        filename(str, optional): The file path to save the trace. Default is "./traces/generator_state_trace.json"
    """
    _generator_names: set = set()

    def __init__(
        self,
        filename: Optional[str] = None,
    ):
        self.filename = filename or "./traces/generator_state_trace.json"

        # self.generator_state = generator  # TODO: make this a generator state
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)
        self._trace_map: Dict[str, List[GeneratorStatesRecord]] = (
            {}  # generator_name: [prompt_states]
        )
        if os.path.exists(self.filename):
            self.load()

    @property
    def log_location(self):
        return self.filename

    @property
    def list_all_geneartors(self):
        return self._generator_names

    def log_prompt(self, generator: Generator, name: str):
        r"""Log the prompt states of the generator with the given name."""
        self._generator_names.add(name)

        prompt_states: Dict = (
            generator.system_prompt.to_dict()
        )  # TODO: log all states of the generator instead of just the prompt

        try:

            if name not in self._trace_map:
                self._trace_map[name] = [
                    GeneratorStatesRecord(
                        prompt_states=prompt_states,
                        time_stamp=datetime.now().isoformat(),
                    )
                ]
                self.save()
            else:
                # compare the last record with the new record
                last_record = self._trace_map[name][-1]
                new_prompt_record = GeneratorStatesRecord(
                    prompt_states=prompt_states, time_stamp=datetime.now().isoformat()
                )

                if last_record != new_prompt_record:
                    self._trace_map[name].append(new_prompt_record)
                    self.save()
        except Exception as e:
            raise Exception(f"Error logging prompt states for {name}") from e

    def save(self):
        with open(self.filename, "w") as f:
            serialized_obj = serialize(self._trace_map)
            f.write(serialized_obj)

    def load(self):

        if os.stat(self.filename).st_size == 0:
            logging.info(f"File {self.filename} is empty.")
            return
        with open(self.filename, "r") as f:
            content = f.read().strip()
            if not content:
                logging.info(f"File {self.filename} is empty after stripping.")
                return
            self._trace_map = json.loads(content)
            # convert each dict record to PromptRecord
            for name, records in self._trace_map.items():
                self._trace_map[name] = [
                    GeneratorStatesRecord.load_from_dict(record) for record in records
                ]