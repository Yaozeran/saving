"""Runtime configuration; never stores a signing key."""

from dataclasses import dataclass
import os
from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    db_path: str = "./data/saving.sqlite"
    rpc_url: str = ""
    contract_address: str = ""
    admin_code: str = ""
    auditor_code: str = ""
    public_origin: str = ""
    production: bool = False
    auth_limit: int = 15

    @classmethod
    def from_env(cls):
        load_dotenv()
        return cls(
            db_path=os.getenv("DB_PATH", cls.db_path),
            rpc_url=os.getenv("SEPOLIA_RPC_URL", ""),
            contract_address=os.getenv("CONTRACT_ADDRESS", ""),
            admin_code=os.getenv("ADMIN_REGISTRATION_CODE", ""),
            auditor_code=os.getenv("AUDITOR_REGISTRATION_CODE", ""),
            public_origin=(
                os.getenv("PUBLIC_ORIGIN") or os.getenv("RENDER_EXTERNAL_URL", "")
            ).rstrip("/"),
            production=os.getenv("APP_ENV", os.getenv("NODE_ENV")) == "production",
        )
