import json
import logging
import os
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class Tfstate:
    def __init__(self, data: Optional[Dict[str, str]] = None):
        self.tfstate_file: Optional[str] = None
        self.native_data = data
        if data:
            self.__dict__ = data

    @staticmethod
    def load_file(file_path: str) -> "Tfstate":
        """Read the tfstate file and load its contents.

        Parses then as JSON and put the result into the object.
        """
        logger.debug("read data from %s", file_path)
        if os.path.exists(file_path):
            with open(file_path) as f:
                json_data = json.load(f)

            tf_state = Tfstate(json_data)
            tf_state.tfstate_file = file_path
            return tf_state

        logger.debug("%s does not exist", file_path)

        return Tfstate()
