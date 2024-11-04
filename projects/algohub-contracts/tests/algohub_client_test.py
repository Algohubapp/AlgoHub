from typing import Any, Dict

import pytest
from algokit_utils import TransactionParameters, get_localnet_default_account
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import (
    AlgorandClient,
    AssetCreateParams,
    AssetTransferParams,
    PayParams,
)
from algokit_utils.config import config
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

from smart_contracts.artifacts.algohub.algohub_client import (
    AlgohubClient,
    TransactionWithSigner,
)


@pytest.fixture(scope="session")
def algorand_client() -> AlgorandClient:
    return AlgorandClient.default_local_net()


@pytest.fixture(scope="session")
def dispenser(algorand_client: AlgorandClient) -> AddressAndSigner:
    return algorand_client.account.dispenser()


@pytest.fixture(scope="session")
def creator_account(algorand_client: AlgorandClient, dispenser: AddressAndSigner) -> AddressAndSigner:
    new_acct = algorand_client.account.random()
    algorand_client.send.payment(PayParams(sender=dispenser.address, receiver=new_acct.address, amount=20_000_000))
    return new_acct


@pytest.fixture(scope="session")
def test_asset_id(creator_account: AddressAndSigner, algorand_client: AlgorandClient) -> int:
    create_txn: Dict[str, Any] = algorand_client.send.asset_create(
        AssetCreateParams(sender=creator_account.address, total=20, clawback=creator_account.address)
    )

    return create_txn["confirmation"]["asset-index"]


@pytest.fixture(scope="session")
def algohub_client(
    algod_client: AlgodClient,
    indexer_client: IndexerClient,
    creator_account: AddressAndSigner,
    # algorand_client: AlgorandClient,
) -> AlgohubClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )

    client = AlgohubClient(
        algod_client,
        creator=get_localnet_default_account(algod_client),
        indexer_client=indexer_client,
    )

    client.create_create_app(address=creator_account.address)

    return client


def test_says_hello(algohub_client: AlgohubClient) -> None:
    result = algohub_client.hello(name="World")

    assert result.return_value == "Hello, World"


def test_simulate_says_hello_with_correct_budget_consumed(algohub_client: AlgohubClient) -> None:
    result = algohub_client.compose().hello(name="World").hello(name="Jane").simulate()

    assert result.abi_results[0].return_value == "Hello, World"
    assert result.abi_results[1].return_value == "Hello, Jane"
    assert result.simulate_response["txn-groups"][0]["app-budget-consumed"] < 100


def test_opt_in_to(
    test_asset_id: int,
    algorand_client: AlgorandClient,
    creator_account: AddressAndSigner,
    algohub_client: AlgohubClient,
) -> None:
    test_mbr_txn = algorand_client.transactions.payment(
        PayParams(sender=creator_account.address, receiver=algohub_client.app_address, amount=200_000, extra_fee=1_000)
    )
    assert (
        algorand_client.account.get_asset_information(creator_account.address, test_asset_id)["asset-holding"]["amount"]
        == 20
    )

    test_opt_in = algohub_client.opt_in_to(
        asset_id=test_asset_id,
        mbr_txn=TransactionWithSigner(txn=test_mbr_txn, signer=creator_account.signer),
        transaction_parameters=TransactionParameters(foreign_assets=[test_asset_id]),
    )

    assert test_opt_in.confirmed_round


def test_pay(
    algorand_client: AlgorandClient,
    dispenser: AddressAndSigner,
    algohub_client: AlgohubClient,
    creator_account: AddressAndSigner,
) -> None:
    payee = algorand_client.account.random()
    algorand_client.send.payment(
        PayParams(sender=dispenser.address, amount=2_000_000, receiver=creator_account.address)
    )
    algorand_client.send.payment(
        PayParams(sender=dispenser.address, amount=2_000_000, receiver=payee.address)
    )
    algorand_client.send.payment(
        PayParams(sender=dispenser.address, amount=2_000_000, receiver=algohub_client.app_address)
    )
    payment = algorand_client.transactions.payment(
        PayParams(sender=creator_account.address, receiver=algohub_client.app_address, amount=1_000, extra_fee=1_000)
    )
    tested_pay = algohub_client.pay(
        payment_txn=TransactionWithSigner(txn=payment, signer=creator_account.signer),
        receiver=payee.address,
        transaction_parameters=TransactionParameters(accounts=[payee.address]),
    )

    assert tested_pay.confirmed_round


def test_supply_asset(
    test_asset_id: int,
    algohub_client: AlgohubClient,
    algorand_client: AlgorandClient,
    creator_account: AddressAndSigner,
    amount: int = 1,
) -> None:
    asset_transfer_txn = algorand_client.transactions.asset_transfer(
        AssetTransferParams(
            sender=creator_account.address, receiver=algohub_client.app_address, amount=amount, asset_id=test_asset_id
        )
    )
    algohub_client.supply_asset(
        asset_transfer=TransactionWithSigner(txn=asset_transfer_txn, signer=creator_account.signer),
        transaction_parameters=TransactionParameters(foreign_assets=[test_asset_id]),
        price=100_000,
    )
