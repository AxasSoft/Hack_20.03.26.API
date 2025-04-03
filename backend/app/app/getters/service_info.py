from app.models import Info
from app.models.service_info import ServiceInfo
from app.schemas import GettingInfo
from app.schemas.service_info import GettingServiceInfo
from app.utils.datetime import from_unix_timestamp, to_unix_timestamp


def get_service_info(info: ServiceInfo) -> GettingServiceInfo:
    return GettingServiceInfo(
        id=info.id,
        created=to_unix_timestamp(info.created),
        updated=to_unix_timestamp(info.updated),
        title=info.title,
        body=info.body,
        image=info.image,
        slug=info.slug,
        link=info.link
    )