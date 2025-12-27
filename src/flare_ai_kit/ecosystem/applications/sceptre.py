"""Sceptre liquid staking connector for Flare Network."""

from typing import TYPE_CHECKING, Final

from eth_typing import ChecksumAddress
from structlog import get_logger

from flare_ai_kit.common import SceptreError, load_abi
from flare_ai_kit.ecosystem.flare import Flare
from flare_ai_kit.ecosystem.settings import EcosystemSettings

if TYPE_CHECKING:
    from typing import Self

    from web3.contract.contract import Contract

logger = get_logger(__name__)


class Sceptre(Flare):
    """Sceptre liquid staking connector (stake FLR → receive sFLR)."""

    SFLR_CONTRACT: Final[str] = "0x12e605bc104e93B45e1aD99F9e555f659051c2BB"

    def __init__(self, settings: EcosystemSettings) -> None:
        super().__init__(settings)
        self.sflr_contract: Contract | None = None

    @classmethod
    async def create(cls, settings: EcosystemSettings) -> "Self":
        """
        Create and initialize a Sceptre connector instance.

        Args:
            settings: Ecosystem settings

        Returns:
            Initialized Sceptre connector

        Raises:
            SceptreError: If initialization fails

        """
        instance = cls(settings)
        logger.info("Initializing Sceptre sFLR connector...")
        try:
            instance.sflr_contract = instance.w3.eth.contract(
                address=instance.w3.to_checksum_address(cls.SFLR_CONTRACT),
                abi=load_abi("SceptreSFLR"),
            )
            logger.debug(
                "Sceptre sFLR connector initialized", contract_address=cls.SFLR_CONTRACT
            )
            return instance  # noqa: TRY300
        except Exception as e:
            msg = f"Failed to initialize Sceptre connector: {e}"
            logger.exception(msg)
            raise SceptreError(msg) from e

    async def stake_flr(self, amount: int) -> str:
        """
        Stake FLR to receive sFLR tokens.

        Args:
            amount: Amount of FLR to stake (in wei, 18 decimals)

        Returns:
            Transaction hash as hex string

        Raises:
            SceptreError: If staking fails

        Example:
            >>> tx_hash = await sceptre.stake_flr(10 * 10**18)  # Stake 10 FLR

        """
        if not self.sflr_contract:
            msg = "Sceptre contract not initialized"
            raise SceptreError(msg)

        logger.info("Staking FLR to receive sFLR", amount_wei=amount)

        # Build transaction for submit() function (payable)
        tx = self.sflr_contract.functions.submit().build_transaction(
            {
                "from": self.account_address,
                "value": amount,  # FLR amount to send
                "nonce": self.w3.eth.get_transaction_count(self.account_address),
            }
        )

        # Sign and send transaction
        tx_hash = await self._build_sign_send_tx(tx)  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportUnknownVariableType]
        logger.info("FLR staked successfully", tx_hash=tx_hash.hex())
        return tx_hash.hex()  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]

    async def get_sflr_balance(self, address: ChecksumAddress) -> int:
        """
        Get sFLR balance for an address.

        Args:
            address: Address to check balance for

        Returns:
            sFLR balance in wei (18 decimals)

        Raises:
            SceptreError: If balance query fails

        Example:
            >>> balance = await sceptre.get_sflr_balance("0x...")
            >>> print(f"Balance: {balance / 10**18} sFLR")

        """
        if not self.sflr_contract:
            msg = "Sceptre contract not initialized"
            raise SceptreError(msg)

        balance = self.sflr_contract.functions.balanceOf(address).call()  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
        logger.debug("sFLR balance retrieved", address=address, balance=balance)
        return int(balance)  # pyright: ignore[reportUnknownArgumentType]

    async def get_total_pooled_flr(self) -> int:
        """
        Get total amount of FLR staked in the Sceptre pool.

        Returns:
            Total FLR in pool (in wei, 18 decimals)

        Raises:
            SceptreError: If query fails

        Example:
            >>> total = await sceptre.get_total_pooled_flr()
            >>> print(f"Total staked: {total / 10**18} FLR")

        """
        if not self.sflr_contract:
            msg = "Sceptre contract not initialized"
            raise SceptreError(msg)

        total = self.sflr_contract.functions.getTotalPooledFlr().call()  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
        logger.debug("Total pooled FLR retrieved", total=total)
        return int(total)  # pyright: ignore[reportUnknownArgumentType]

    async def get_flr_by_shares(self, shares: int) -> int:
        """
        Convert sFLR shares to FLR amount.

        Args:
            shares: Amount of sFLR shares

        Returns:
            Equivalent FLR amount (in wei, 18 decimals)

        Raises:
            SceptreError: If conversion fails

        Example:
            >>> flr = await sceptre.get_flr_by_shares(10 * 10**18)
            >>> print(f"10 sFLR = {flr / 10**18} FLR")

        """
        if not self.sflr_contract:
            msg = "Sceptre contract not initialized"
            raise SceptreError(msg)

        flr_amount = self.sflr_contract.functions.getPooledFlrByShares(shares).call()  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
        logger.debug("Converted shares to FLR", shares=shares, flr_amount=flr_amount)
        return int(flr_amount)  # pyright: ignore[reportUnknownArgumentType]

    async def get_shares_by_flr(self, flr_amount: int) -> int:
        """
        Convert FLR amount to sFLR shares.

        Args:
            flr_amount: Amount of FLR (in wei, 18 decimals)

        Returns:
            Equivalent sFLR shares

        Raises:
            SceptreError: If conversion fails

        Example:
            >>> shares = await sceptre.get_shares_by_flr(10 * 10**18)
            >>> print(f"10 FLR = {shares / 10**18} sFLR")

        """
        if not self.sflr_contract:
            msg = "Sceptre contract not initialized"
            raise SceptreError(msg)

        shares = self.sflr_contract.functions.getSharesByPooledFlr(flr_amount).call()  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
        logger.debug("Converted FLR to shares", flr_amount=flr_amount, shares=shares)
        return int(shares)  # pyright: ignore[reportUnknownArgumentType]

    async def request_withdrawal(self, amount: int) -> str:
        """
        Request withdrawal of sFLR (starts cooldown period ~14.5 days).

        Args:
            amount: Amount of sFLR to withdraw (in wei, 18 decimals)

        Returns:
            Transaction hash as hex string

        Raises:
            SceptreError: If request fails

        Example:
            >>> tx_hash = await sceptre.request_withdrawal(5 * 10**18)

        """
        if not self.sflr_contract:
            msg = "Sceptre contract not initialized"
            raise SceptreError(msg)

        logger.info("Requesting withdrawal", amount_wei=amount)

        tx = self.sflr_contract.functions.requestWithdrawal(amount).build_transaction(
            {
                "from": self.account_address,
                "nonce": self.w3.eth.get_transaction_count(self.account_address),
            }
        )

        tx_hash = await self._build_sign_send_tx(tx)  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportUnknownVariableType]
        logger.info("Withdrawal requested", tx_hash=tx_hash.hex())
        return tx_hash.hex()  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]

    async def claim_withdrawal(self, request_id: int) -> str:
        """
        Claim a withdrawal after cooldown period has elapsed.

        Args:
            request_id: ID of the withdrawal request

        Returns:
            Transaction hash as hex string

        Raises:
            SceptreError: If claim fails

        Example:
            >>> tx_hash = await sceptre.claim_withdrawal(0)

        """
        if not self.sflr_contract:
            msg = "Sceptre contract not initialized"
            raise SceptreError(msg)

        logger.info("Claiming withdrawal", request_id=request_id)

        tx = self.sflr_contract.functions.claimWithdrawal(request_id).build_transaction(
            {
                "from": self.account_address,
                "nonce": self.w3.eth.get_transaction_count(self.account_address),
            }
        )

        tx_hash = await self._build_sign_send_tx(tx)  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportUnknownVariableType]
        logger.info("Withdrawal claimed", tx_hash=tx_hash.hex())
        return tx_hash.hex()  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]

