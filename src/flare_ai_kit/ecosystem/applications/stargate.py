"""Stargate cross-chain bridge connector for Flare Network."""

from typing import TYPE_CHECKING, Final

from structlog import get_logger

from flare_ai_kit.common import StargateError
from flare_ai_kit.ecosystem.flare import Flare
from flare_ai_kit.ecosystem.settings import EcosystemSettings

if TYPE_CHECKING:
    from typing import Self

logger = get_logger(__name__)


class Stargate(Flare):
    """Stargate cross-chain bridging connector for Flare."""

    # Flare Network (endpointID: 30295)
    FLARE_ENDPOINT_ID: Final[int] = 30295

    # Stargate OFT Token Addresses on Flare
    STARGATE_ETH: Final[str] = "0x8e8539e4CcD69123c623a106773F2b0cbbc58746"
    STARGATE_USDC: Final[str] = "0x77C71633C34C3784ede189d74223122422492a0f"
    STARGATE_USDT: Final[str] = "0x1C10CC06DC6D35970d1D53B2A23c76ef370d4135"

    TOKEN_MESSAGING: Final[str] = "0x45d417612e177672958dC0537C45a8f8d754Ac2E"
    TREASURER: Final[str] = "0x090194F1EEDc134A680e3b488aBB2D212dba8c01"

    # Common Destination Chains
    CHAINS: Final[dict[str, int]] = {
        "ethereum": 30101,
        "bnb_chain": 30102,
        "avalanche": 30106,
        "polygon": 30109,
        "arbitrum": 30110,
        "optimism": 30111,
        "base": 30184,
        "linea": 30183,
        "scroll": 30214,
        "mantle": 30181,
    }

    def __init__(self, settings: EcosystemSettings) -> None:
        super().__init__(settings)

    @classmethod
    async def create(cls, settings: EcosystemSettings) -> "Self":
        """
        Create and initialize a Stargate connector instance.

        Args:
            settings: Ecosystem settings

        Returns:
            Initialized Stargate connector

        Raises:
            StargateError: If initialization fails

        """
        instance = cls(settings)
        logger.info("Initializing Stargate bridge connector...")
        try:
            logger.debug(
                "Stargate connector initialized",
                endpoint_id=cls.FLARE_ENDPOINT_ID,
                eth_oft=cls.STARGATE_ETH,
                usdc_oft=cls.STARGATE_USDC,
                usdt_oft=cls.STARGATE_USDT,
            )
            return instance  # noqa: TRY300
        except Exception as e:
            msg = f"Failed to initialize Stargate connector: {e}"
            logger.exception(msg)
            raise StargateError(msg) from e

    def get_oft_address(self, token: str) -> str:
        """
        Get Stargate OFT token address on Flare.

        Args:
            token: Token symbol ("ETH", "USDC", or "USDT")

        Returns:
            OFT contract address

        Raises:
            StargateError: If token not supported

        Example:
            >>> oft_addr = stargate.get_oft_address("USDC")
            >>> print(f"USDC OFT: {oft_addr}")

        """
        token_upper = token.upper()
        if token_upper == "ETH":
            return self.STARGATE_ETH
        if token_upper == "USDC":
            return self.STARGATE_USDC
        if token_upper == "USDT":
            return self.STARGATE_USDT
        msg = f"Unsupported token: {token}. Supported: ETH, USDC, USDT"
        raise StargateError(msg)

    def get_chain_endpoint(self, chain: str) -> int:
        """
        Get LayerZero endpoint ID for a destination chain.

        Args:
            chain: Chain name (e.g., "ethereum", "arbitrum")

        Returns:
            Endpoint ID

        Raises:
            StargateError: If chain not supported

        Example:
            >>> endpoint = stargate.get_chain_endpoint("arbitrum")
            >>> print(f"Arbitrum endpoint: {endpoint}")

        """
        chain_lower = chain.lower()
        if chain_lower in self.CHAINS:
            return self.CHAINS[chain_lower]
        msg = f"Unsupported chain: {chain}. Supported: {', '.join(self.CHAINS.keys())}"
        raise StargateError(msg)

    def get_supported_tokens(self) -> list[str]:
        """
        Get list of supported bridgeable tokens on Flare.

        Returns:
            List of token symbols

        Example:
            >>> tokens = stargate.get_supported_tokens()
            >>> print(f"Bridgeable: {', '.join(tokens)}")

        """
        return ["ETH", "USDC", "USDT"]

    def get_supported_chains(self) -> list[str]:
        """
        Get list of supported destination chains.

        Returns:
            List of chain names

        Example:
            >>> chains = stargate.get_supported_chains()
            >>> print(f"Destinations: {', '.join(chains)}")

        """
        return list(self.CHAINS.keys())

    def get_bridge_info(self) -> dict[str, str | int | list[str]]:
        """
        Get Stargate bridge information for Flare.

        Returns:
            Dictionary with bridge details

        Example:
            >>> info = stargate.get_bridge_info()
            >>> print(f"Flare endpoint: {info['endpoint_id']}")

        """
        return {  # pyright: ignore[reportReturnType]
            "network": "Flare",
            "endpoint_id": self.FLARE_ENDPOINT_ID,
            "token_messaging": self.TOKEN_MESSAGING,
            "treasurer": self.TREASURER,
            "supported_tokens": self.get_supported_tokens(),
            "supported_chains": self.get_supported_chains(),
        }
