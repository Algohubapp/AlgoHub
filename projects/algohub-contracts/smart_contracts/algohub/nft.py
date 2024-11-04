from algopy.arc4 import Address, Struct, UInt64


class NFTAsset(Struct, kw_only=True):
    asset_id: UInt64
    owner: Address
    unitary_price: UInt64
