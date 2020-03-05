from squad_client.core.api import SquadApi
from squad_client.core.models import Squad


SquadApi.configure(url='http://localhost:8000/')
groups = Squad().groups()
for _id in groups:
    print(groups[_id].slug)
