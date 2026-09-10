from fastapi import APIRouter
from fastapi import Response
from gdformat import requests
from gdformat import responses
from gdformat.enums import Secret

from app.api.gd import response
from app.api.gd.context import RequiresForm
from app.api.gd.context import RequiresSession
from app.api.gd.context import RequiresTransaction
from app.services import scores

router = APIRouter()


async def _level_scores(
    form: RequiresForm, session: RequiresSession, ctx: RequiresTransaction
) -> Response:
    request = response.parse(requests.parse_level_scores(form), secret=Secret.COMMON)
    rows = response.unwrap(await scores.level_scores(ctx, session, request))

    if not rows:
        return response.failure()

    return response.text(responses.serialise_level_scores(rows))


router.add_api_route("/getGJLevelScores211.php", _level_scores, methods=["POST"])
router.add_api_route("/getGJLevelScoresPlat.php", _level_scores, methods=["POST"])
