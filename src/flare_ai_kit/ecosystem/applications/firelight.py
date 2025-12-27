"""Firelight XRP staking protocol connector for Flare Network."""

from typing import TYPE_CHECKING, Final

from eth_typing import ChecksumAddress
from structlog import get_logger

from flare_ai_kit.common import FirelightError, load_abi
from flare_ai_kit.ecosystem.flare import Flare
from flare_ai_kit.ecosystem.settings import EcosystemSettings

if TYPE_CHECKING:
    from typing import Self

    from web3.contract.contract import Contract

logger = get_logger(__name__)


class Firelight(Flare):
    """Firelight XRP staking protocol connector (stXRP vault)."""

    STXRP_VAULT: Final[str] = "0x4C18Ff3C89632c3Dd62E796c0aFA5c07c4c1B2b3"

    def __init__(self, settings: EcosystemSettings) -> None:
        super().__init__(settings)
        self.vault_contract: Contract | None = None

    @classmethod
    async def create(cls, settings: EcosystemSettings) -> "Self":
        """
        Create and initialize a Firelight connector instance.

        Args:
            settings: Ecosystem settings

        Returns:
            Initialized Firelight connector

        Raises:
            FirelightError: If initialization fails

        """
        instance = cls(settings)
        logger.info("Initializing Firelight stXRP vault...")
        try:
            instance.vault_contract = instance.w3.eth.contract(
                address=instance.w3.to_checksum_address(cls.STXRP_VAULT),
                abi=load_abi("FirelightVault"),
            )
            logger.debug(
                "Firelight stXRP vault initialized", contract_address=cls.STXRP_VAULT
            )
            return instance  # noqa: TRY300
        except Exception as e:
            msg = f"Failed to initialize Firelight connector: {e}"
            logger.exception(msg)
            raise FirelightError(msg) from e

    async def stake_xrp(self, amount: int) -> str:
        """
        Stake FXRP to receive stXRP.

        Args:
            amount: Amount of FXRP to stake (in wei, 18 decimals)

        Returns:
            Transaction hash as hex string

        Raises:
            FirelightError: If staking fails

        Example:
            >>> tx_hash = await firelight.stake_xrp(10 * 10**18)  # Stake 10 FXRP

        """
        if not self.vault_contract:
            msg = "Firelight vault contract not initialized"
            raise FirelightError(msg)

        logger.info("Staking FXRP to Firelight", amount_wei=amount)

        # Build transaction for deposit() function
        tx = self.vault_contract.functions.deposit(
            amount, self.account_address
        ).build_transaction(
            {
                "from": self.account_address,
                "nonce": self.w3.eth.get_transaction_count(self.account_address),
            }
        )

        # Sign and send transaction
        tx_hash = await self._build_sign_send_tx(tx)  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportUnknownVariableType]
        logger.info("FXRP staked successfully", tx_hash=tx_hash.hex())
        return tx_hash.hex()  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]

    async def request_withdrawal(self, amount: int) -> str:
        """
        Request withdrawal of FXRP (initiates cooldown period).

        Args:
            amount: Amount of FXRP to withdraw (in wei, 18 decimals)

        Returns:
            Transaction hash as hex string

        Raises:
            FirelightError: If withdrawal request fails

        Example:
            >>> tx = await firelight.request_withdrawal(5 * 10**18)  # Request 5 FXRP

        """
        if not self.vault_contract:
            msg = "Firelight vault contract not initialized"
            raise FirelightError(msg)

        logger.info("Requesting FXRP withdrawal", amount_wei=amount)

        # Build transaction for withdraw() function
        tx = self.vault_contract.functions.withdraw(
            amount, self.account_address, self.account_address
        ).build_transaction(
            {
                "from": self.account_address,
                "nonce": self.w3.eth.get_transaction_count(self.account_address),
            }
        )

        # Sign and send transaction
        tx_hash = await self._build_sign_send_tx(tx)  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportUnknownVariableType]
        logger.info("Withdrawal requested successfully", tx_hash=tx_hash.hex())
        return tx_hash.hex()  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]

    async def claim_withdrawal(self, period: int) -> str:
        """
        Claim a pending withdrawal after the cooldown period.

        Args:
            period: Period number to claim from

        Returns:
            Transaction hash as hex string

        Raises:
            FirelightError: If claim fails

        Example:
            >>> period = await firelight.get_current_period()
            >>> tx = await firelight.claim_withdrawal(period - 1)

        """
        if not self.vault_contract:
            msg = "Firelight vault contract not initialized"
            raise FirelightError(msg)

        logger.info("Claiming withdrawal", period=period)

        # Build transaction for claimWithdraw() function
        tx = self.vault_contract.functions.claimWithdraw(period).build_transaction(
            {
                "from": self.account_address,
                "nonce": self.w3.eth.get_transaction_count(self.account_address),
            }
        )

        # Sign and send transaction
        tx_hash = await self._build_sign_send_tx(tx)  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportUnknownVariableType]
        logger.info("Withdrawal claimed successfully", tx_hash=tx_hash.hex())
        return tx_hash.hex()  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]

    async def get_stxrp_balance(self, address: ChecksumAddress) -> int:
        """
        Get stXRP balance for an address.

        Args:
            address: Address to check balance for

        Returns:
            stXRP balance in wei (18 decimals)

        Raises:
            FirelightError: If balance query fails

        Example:
            >>> balance = await firelight.get_stxrp_balance("0x...")
            >>> print(f"Balance: {balance / 10**18} stXRP")

        """
        if not self.vault_contract:
            msg = "Firelight vault contract not initialized"
            raise FirelightError(msg)

        balance = self.vault_contract.functions.balanceOf(address).call()  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
        logger.debug("stXRP balance retrieved", address=address, balance=balance)
        return int(balance)  # pyright: ignore[reportUnknownArgumentType]

    async def get_total_assets(self) -> int:
        """
        Get total FXRP staked in the vault.

        Returns:
            Total assets in wei (18 decimals)

        Raises:
            FirelightError: If query fails

        Example:
            >>> total = await firelight.get_total_assets()
            >>> print(f"Total staked: {total / 10**18} FXRP")

        """
        if not self.vault_contract:
            msg = "Firelight vault contract not initialized"
            raise FirelightError(msg)

        total = self.vault_contract.functions.totalAssets().call()  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
        logger.debug("Total assets retrieved", total=total)
        return int(total)  # pyright: ignore[reportUnknownArgumentType]

    async def get_current_period(self) -> int:
        """
        Get the current withdrawal period number.

        Returns:
            Current period number

        Raises:
            FirelightError: If query fails

        Example:
            >>> period = await firelight.get_current_period()
            >>> print(f"Current period: {period}")

        """
        if not self.vault_contract:
            msg = "Firelight vault contract not initialized"
            raise FirelightError(msg)

        period = self.vault_contract.functions.currentPeriod().call()  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
        logger.debug("Current period retrieved", period=period)
        return int(period)  # pyright: ignore[reportUnknownArgumentType]

    async def get_pending_withdrawal(
        self, period: int, address: ChecksumAddress
    ) -> int:
        """
        Get pending withdrawal amount for a specific period.

        Args:
            period: Period number to check
            address: Address to check for

        Returns:
            Claimable amount in wei (18 decimals)

        Raises:
            FirelightError: If query fails

        Example:
            >>> period = await firelight.get_current_period()
            >>> pending = await firelight.get_pending_withdrawal(period - 1, "0x...")

        """
        if not self.vault_contract:
            msg = "Firelight vault contract not initialized"
            raise FirelightError(msg)

        amount = self.vault_contract.functions.withdrawalsOf(period, address).call()  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
        logger.debug(
            "Pending withdrawal retrieved",
            period=period,
            address=address,
            amount=amount,
        )
        return int(amount)  # pyright: ignore[reportUnknownArgumentType]
