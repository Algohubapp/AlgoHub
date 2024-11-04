from algopy import Account, ARC4Contract, Asset, Global, String, gtxn, itxn
from algopy.arc4 import Address, DynamicArray, UInt64, abimethod

from .nft import NFTAsset


class Algohub(ARC4Contract):
    def __init__(self) -> None:
        self.address: Account = Account()
        self.assets: DynamicArray[NFTAsset] = DynamicArray[NFTAsset]()

    @abimethod(create="require")
    def create_app(self, address: Account) -> None:
        self.address = Account(address.bytes)

    @abimethod
    def pay(self, payment_txn: gtxn.PaymentTransaction, receiver: Account) -> None:
        assert payment_txn.receiver == Global.current_application_address
        itxn.Payment(receiver=receiver, amount=payment_txn.amount, fee=1_000).submit()

    @abimethod
    def hello(self, name: String) -> String:
        return "Hello, " + name

    @abimethod
    def opt_in_to(self, mbr_txn: gtxn.PaymentTransaction, asset_id: UInt64) -> None:
        assert not Global.current_application_address.is_opted_in(Asset(asset_id.native))
        assert mbr_txn.receiver == Global.current_application_address
        assert mbr_txn.amount == Global.asset_opt_in_min_balance + Global.min_balance
        itxn.AssetTransfer(
            xfer_asset=asset_id.native,
            asset_receiver=Global.current_application_address,
            asset_amount=0,
        ).submit()

    @abimethod
    def supply_asset(self, asset_transfer: gtxn.AssetTransferTransaction, price: UInt64) -> None:
        assert asset_transfer.asset_receiver == Global.current_application_address, "Receiver must be current app"
        self.assets.append(
            NFTAsset(
                asset_id=UInt64(asset_transfer.xfer_asset.id),
                owner=Address(asset_transfer.sender),
                unitary_price=price,
            )
        )

    # @abimethod
    # def buy_asset(self, amount: UInt64, payment_txn: gtxn.PaymentTransaction, asset_id: UInt64) -> None:
    #     assert payment_txn.receiver == Global.current_application_address
    #     assert Global.current_application_address.total_assets >= amount.native
    #     purchased_nft: NFTAsset = NFTAsset(owner=Address(self.address), asset_id=UInt64(1), unitary_price=UInt64(1))
    #     for index in urange(self.assets.length):
    #         if self.assets[index].asset_id == asset_id:
    #             assert payment_txn.amount == self.assets[index].unitary_price.native * amount.native
    #             purchased_nft = self.assets[index].copy()
    #             assert purchased_nft.owner.native == self.assets[index].owner.native
    #             tmp = self.assets[self.assets.length - UInt64(1).native].copy()
    #             self.assets[self.assets.length - UInt64(1).native] = self.assets[index].copy()
    #             self.assets[index] = tmp.copy()

    #     itxn.AssetTransfer(
    #         xfer_asset=asset_id.native,
    #         asset_amount=amount.native,
    #         asset_receiver=payment_txn.sender,
    #     ).submit()

    #     itxn.Payment(receiver=purchased_nft.owner.native, amount=payment_txn.amount).submit()
    #     self.assets.pop()
