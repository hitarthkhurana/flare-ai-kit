"""Kinetic lending protocol connector for Flare Network."""

from typing import TYPE_CHECKING, Final

from eth_typing import ChecksumAddress
from structlog import get_logger

from flare_ai_kit.common import KineticError, load_abi
from flare_ai_kit.ecosystem.flare import Flare
from flare_ai_kit.ecosystem.settings import EcosystemSettings

if TYPE_CHECKING:
    from typing import Self

    from web3.contract.contract import Contract

logger = get_logger(__name__)


class Kinetic(Flare):
    """Kinetic lending protocol connector (ksFLR market)."""

    KSFLR_MARKET: Final[str] = "0x291487beC339c2fE5D83DD45F0a15EFC9Ac45656"

    def __init__(self, settings: EcosystemSettings) -> None:
        super().__init__(settings)
        self.ksflr_contract: Contract | None = None

    @classmethod
    async def create(cls, settings: EcosystemSettings) -> "Self":
        """
        Create and initialize a Kinetic connector instance.

        Args:
            settings: Ecosystem settings

        Returns:
            Initialized Kinetic connector

        Raises:
            KineticError: If initialization fails

        """
        instance = cls(settings)
        logger.info("Initializing Kinetic ksFLR market...")
        try:
            instance.ksflr_contract = instance.w3.eth.contract(
                address=instance.w3.to_checksum_address(cls.KSFLR_MARKET),
                abi=load_abi("KineticKToken"),
            )
            logger.debug(
                "Kinetic ksFLR market initialized", contract_address=cls.KSFLR_MARKET
            )
            return instance  # noqa: TRY300
        except Exception as e:
            msg = f"Failed to initialize Kinetic connector: {e}"
            logger.exception(msg)
            raise KineticError(msg) from e

    async def supply(self, amount: int) -> str:
        """
        Supply sFLR to Kinetic to earn interest.

        Args:
            amount: Amount of sFLR to supply (in wei, 18 decimals)

        Returns:
            Transaction hash as hex string

        Raises:
            KineticError: If supply fails

        Example:
            >>> tx_hash = await kinetic.supply(10 * 10**18)  # Supply 10 sFLR

        """
        if not self.ksflr_contract:
            msg = "Kinetic contract not initialized"
            raise KineticError(msg)

        logger.info("Supplying sFLR to Kinetic", amount_wei=amount)

        # Build transaction for mint() function
        tx = self.ksflr_contract.functions.mint(amount).build_transaction(
            {
                "from": self.account_address,
                "nonce": self.w3.eth.get_transaction_count(self.account_address),
            }
        )

        # Sign and send transaction
        tx_hash = await self._build_sign_send_tx(tx)  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportUnknownVariableType]
        logger.info("sFLR supplied successfully", tx_hash=tx_hash.hex())
        return tx_hash.hex()  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]

    async def redeem(self, amount: int) -> str:
        """
        Redeem ksFLR tokens to withdraw supplied sFLR.

        Args:
            amount: Amount of ksFLR to redeem (in wei, 18 decimals)

        Returns:
            Transaction hash as hex string

        Raises:
            KineticError: If redeem fails

        Example:
            >>> tx_hash = await kinetic.redeem(5 * 10**18)  # Redeem 5 ksFLR

        """
        if not self.ksflr_contract:
            msg = "Kinetic contract not initialized"
            raise KineticError(msg)

        logger.info("Redeeming ksFLR from Kinetic", amount_wei=amount)

        # Build transaction for redeem() function
        tx = self.ksflr_contract.functions.redeem(amount).build_transaction(
            {
                "from": self.account_address,
                "nonce": self.w3.eth.get_transaction_count(self.account_address),
            }
        )

        # Sign and send transaction
        tx_hash = await self._build_sign_send_tx(tx)  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportUnknownVariableType]
        logger.info("ksFLR redeemed successfully", tx_hash=tx_hash.hex())
        return tx_hash.hex()  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]

    async def get_balance(self, address: ChecksumAddress) -> int:
        """
        Get ksFLR balance for an address.

        Args:
            address: Address to check balance for

        Returns:
            ksFLR balance in wei (18 decimals)

        Raises:
            KineticError: If balance query fails

        Example:
            >>> balance = await kinetic.get_balance("0x...")
            >>> print(f"Balance: {balance / 10**18} ksFLR")

        """
        if not self.ksflr_contract:
            msg = "Kinetic contract not initialized"
            raise KineticError(msg)

        balance = self.ksflr_contract.functions.balanceOf(address).call()  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
        logger.debug("ksFLR balance retrieved", address=address, balance=balance)
        return int(balance)  # pyright: ignore[reportUnknownArgumentType]

    async def get_underlying_balance(self, address: ChecksumAddress) -> int:
        """
        Get underlying sFLR balance for an address (what you can withdraw).

        Args:
            address: Address to check balance for

        Returns:
            Underlying sFLR balance in wei (18 decimals)

        Raises:
            KineticError: If balance query fails

        Example:
            >>> balance = await kinetic.get_underlying_balance("0x...")
            >>> print(f"Can withdraw: {balance / 10**18} sFLR")

        """
        if not self.ksflr_contract:
            msg = "Kinetic contract not initialized"
            raise KineticError(msg)

        # Note: balanceOfUnderlying is not a pure view function in Compound
        balance = self.ksflr_contract.functions.balanceOfUnderlying(address).call()  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
        logger.debug(
            "Underlying sFLR balance retrieved", address=address, balance=balance
        )
        return int(balance)  # pyright: ignore[reportUnknownArgumentType]

    async def get_exchange_rate(self) -> int:
        """
        Get current exchange rate between ksFLR and sFLR.

        Returns:
            Exchange rate (scaled by 1e18)

        Raises:
            KineticError: If query fails

        Example:
            >>> rate = await kinetic.get_exchange_rate()
            >>> print(f"1 ksFLR = {rate / 10**18} sFLR")

        """
        if not self.ksflr_contract:
            msg = "Kinetic contract not initialized"
            raise KineticError(msg)

        rate = self.ksflr_contract.functions.exchangeRateCurrent().call()  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
        logger.debug("Exchange rate retrieved", rate=rate)
        return int(rate)  # pyright: ignore[reportUnknownArgumentType]

    async def get_supply_rate(self) -> int:
        """
        Get current supply APY (interest rate for lenders).

        Returns:
            Supply rate per block

        Raises:
            KineticError: If query fails

        Example:
            >>> rate = await kinetic.get_supply_rate()
            >>> # Convert to APY: rate * blocks_per_year / 1e18

        """
        if not self.ksflr_contract:
            msg = "Kinetic contract not initialized"
            raise KineticError(msg)

        rate = self.ksflr_contract.functions.supplyRatePerTimestamp().call()  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
        logger.debug("Supply rate retrieved", rate=rate)
        return int(rate)  # pyright: ignore[reportUnknownArgumentType]
