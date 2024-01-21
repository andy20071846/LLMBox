from logging import getLogger

from ..utils import ModelArguments
from .model import Model

logger = getLogger(__name__)


def load_model(args: ModelArguments) -> Model:
    r"""Load corresponding model class.

    Args:
        args (Namespace): The global configurations.

    Returns:
        Model: Our class for model.
    """
    if args.is_openai_model():
        logger.info(f"Loading OpenAI API model `{args.model_name_or_path.lower()}`.")
        from .openai import Openai

        return Openai(args)
    elif args.is_anthropic_model():
        logger.info(f"Loading Anthropic API model `{args.model_name_or_path.lower()}`.")
        from .anthropic import Anthropic

        return Anthropic(args)
    else:
        if args.vllm:
            try:
                from .vllm_model import vllmModel

                return vllmModel(args)
            except ValueError as e:
                if "are not supported for now" in str(e):
                    args.vllm = False
                    logger.warning(f"vllm has not supported the architecture of {args.model_name_or_path} for now.")
                else:
                    raise e
        from .huggingface_model import HuggingFaceModel

        return HuggingFaceModel(args)
