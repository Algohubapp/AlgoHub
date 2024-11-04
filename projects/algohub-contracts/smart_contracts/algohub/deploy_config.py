import logging

import algokit_utils
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient
from algokit_utils.beta.algorand_client import AlgorandClient

from smart_contracts.artifacts.algohub.algohub_client import CreateAppArgs, DeployCreate

logger = logging.getLogger(__name__)


# define deployment behaviour based on supplied app spec
def deploy(
    algod_client: AlgodClient,
    indexer_client: IndexerClient,
    app_spec: algokit_utils.ApplicationSpecification,
    deployer: algokit_utils.Account,
) -> None:
    from smart_contracts.artifacts.algohub.algohub_client import (
        AlgohubClient,
    )

    app_client = AlgohubClient(
        algod_client,
        creator=deployer,
        indexer_client=indexer_client,
    )

    app_client.deploy(
        on_schema_break=algokit_utils.OnSchemaBreak.AppendApp,
        on_update=algokit_utils.OnUpdate.AppendApp,
        create_args=DeployCreate(args=CreateAppArgs(address=AlgorandClient.default_local_net().account.random().address))
    )

    name = "world"
    response = app_client.hello(name=name)
    logger.info(
        f"Called hello on {app_spec.contract.name} ({app_client.app_id})"
        f"with name={name}, received: {response.return_value}"
    )
