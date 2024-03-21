__all__ = (
    'get_provider',
)
import dataclasses

from ..models import Providers, ServiceProvider
from .dummy import DummyProvider
from .justanotherpanel import JustAnotherPanelProvider
from .prosmmstore import ProSMMStoreProvider
from .fxsmmsocpanel import FxSMMSocProvider
from .services import JUSTANOTHERPANEL, PROSMMSTORE, SOCPROOF, FXSMMSOC
from .socproof import SocProofProvider

PROVIDERS = {
    JUSTANOTHERPANEL: JustAnotherPanelProvider,
    SOCPROOF: SocProofProvider,
    PROSMMSTORE: ProSMMStoreProvider,
    FXSMMSOC: FxSMMSocProvider,
    'dummy': DummyProvider,
}


def get_provider(_id: Providers):
    provider = PROVIDERS.get(_id.name)
    if provider is None:
        raise Exception(f'Unknown provider: {_id}')

    return provider


def resolve_provider(service_name: str, index=None):
    return (index or {}).get(service_name, ServiceProvider(service_name, None, Providers['dummy']))


SERVICES = (
    SOCPROOF,
    JUSTANOTHERPANEL,
    PROSMMSTORE,
    FXSMMSOC
)


def is_valid_row(row) -> bool:
    is_valid = True
    is_valid &= len(row) == 3
    is_valid &= row[2] in PROVIDERS
    return is_valid
