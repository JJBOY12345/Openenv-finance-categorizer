# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Finance Env environment client."""

from typing import Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult

from .models import FinanceAction, FinanceObservation, FinanceState


class FinanceEnv(
    EnvClient[FinanceAction, FinanceObservation, FinanceState]
):
    """Client for the finance categorization environment."""

    def _step_payload(self, action: FinanceAction) -> Dict:
        """Convert ``FinanceAction`` into a JSON payload."""
        return action.model_dump(mode="json", exclude_none=True)

    def _parse_result(self, payload: Dict) -> StepResult[FinanceObservation]:
        """Parse a step or reset response from the server."""
        observation = FinanceObservation.model_validate(payload.get("observation", {}))

        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> FinanceState:
        """Parse server state responses into ``FinanceState``."""
        return FinanceState.model_validate(payload)
